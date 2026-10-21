#!/usr/bin/env python3
"""Automatic identity QA for the main character (every step: dataset, LoRA tests, keyframes, video frames, 4K).
Measures per image:
  face   ArcFace cosine vs reference set (only if face >= --min_face px)          gate: >= --face_min
  body   person height / face-box height (RMBG mask), only when --fullbody          gate: >= --ratio_min (sheet 8.9-10.4)
  suit   share of near-white plates, dark underlayer, cyan-blue glow inside the person mask below the face
         gate: white+dark >= 0.45 of suit pixels (lighting-tolerant), glow present unless --leds_off
  hair   mean value/saturation of mask pixels above the face box: silver = bright, low saturation
         gate: V >= 0.45 and S <= 0.35 (warm-lit shots can fail S: then rely on the visual check)
Writes JSON; the visual checklist (CHECKLIST.md) is filled by Claude for every image as well.
Run with the ComfyUI venv: identity_qa.py --ref r.png ... --img a.png ... [--fullbody] [--json out.json]"""
import argparse, json, os, sys, numpy as np, cv2, torch
from PIL import Image
os.environ.setdefault("HF_HOME", "/Users/Maxi/Code/Models/hf-cache")
sys.path.insert(0, "/Users/Maxi/Code/Tools/family-lora-venv/lib/python3.14/site-packages")
from insightface.app import FaceAnalysis
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
from rtmlib import Wholebody
DW = "/Users/Maxi/Code/Models/dwpose"
wb = Wholebody(det=f"{DW}/yolox_l.onnx", det_input_size=(640, 640), pose=f"{DW}/dw-ll_ucoco_384.onnx", pose_input_size=(288, 384), backend="onnxruntime", device="cpu")
a = argparse.ArgumentParser()
a.add_argument("--ref", nargs="+", required=True); a.add_argument("--img", nargs="+", required=True)
a.add_argument("--fullbody", action="store_true"); a.add_argument("--leds_off", action="store_true")
a.add_argument("--face_min", type=float, default=0.55); a.add_argument("--min_face", type=int, default=80)
a.add_argument("--no_face_ok", action="store_true"); a.add_argument("--ratio_min", type=float, default=9.0); a.add_argument("--torso_min", type=float, default=3.6); a.add_argument("--leg_min", type=float, default=6.9); a.add_argument("--json"); o = a.parse_args()
fa = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"]); fa.prepare(ctx_id=-1, det_size=(1024, 1024))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
seg = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-2.0", trust_remote_code=True).to(dev).eval()
tf = transforms.Compose([transforms.Resize((1024, 1024)), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
def face(bgr):
    h, w = bgr.shape[:2]; pad = int(0.25 * max(h, w))
    big = cv2.copyMakeBorder(bgr, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(128, 128, 128))
    s = 1600 / max(big.shape[:2]) if max(big.shape[:2]) < 1600 else 2600 / max(big.shape[:2]) if max(big.shape[:2]) > 2600 else 1.0
    if s != 1.0: big = cv2.resize(big, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
    fs = [f for f in fa.get(big) if f.det_score > 0.5]
    if not fs: return None
    # several faces (statues, crowds): take the one most like the reference, not the largest
    f = max(fs, key=lambda f: float(f.normed_embedding @ CREF)) if CREF is not None else max(fs, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return f.normed_embedding, f.bbox / s - pad
CREF = None
R = [face(cv2.imread(p)) for p in o.ref]; E = np.array([r[0] for r in R if r]); c = E.mean(0); c /= np.linalg.norm(c); CREF = c
rows = []
for p in o.img:
    bgr = cv2.imread(p); H, W = bgr.shape[:2]; im = Image.open(p).convert("RGB")
    with torch.no_grad(): m = seg(tf(im).unsqueeze(0).to(dev))[-1].sigmoid().cpu()[0, 0].numpy()
    m = cv2.resize(m, (W, H)) > 0.5
    r = dict(file=os.path.basename(p)); fails = []
    f = face(bgr)
    if f is not None:
        e, bb = f; fw = int(bb[2] - bb[0]); r["face_px"] = fw
        if fw >= o.min_face:
            r["face"] = round(float(e @ c), 3)
            if r["face"] < o.face_min: fails.append("face")
        x0, y0, x1, y1 = [int(v) for v in bb]; fh = y1 - y0
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32) / [180, 255, 255]
        hair = m.copy(); hair[max(0, y0 + fh // 4):, :] = False                     # mask above the brows
        hair[:, :max(0, x0 - fw)] = False; hair[:, min(W, x1 + fw):] = False
        if hair.sum() > 200:
            r["hair_V"] = round(float(hsv[..., 2][hair].mean()), 2); r["hair_S"] = round(float(hsv[..., 1][hair].mean()), 2)
            if r["hair_V"] < 0.45 or r["hair_S"] > 0.35: fails.append("hair")
        suit = m.copy(); suit[:min(H, y1 + fh // 3), :] = False
        if suit.sum() > 500:
            V, S, Hh = hsv[..., 2][suit], hsv[..., 1][suit], hsv[..., 0][suit] * 360
            white = ((V > 0.70) & (S < 0.25)).mean(); dark = (V < 0.30).mean()
            glow = ((Hh > 175) & (Hh < 225) & (S > 0.35) & (V > 0.55)).mean()
            r.update(suit_white=round(float(white), 3), suit_dark=round(float(dark), 3), suit_glow=round(float(glow), 4))
            if white + dark < 0.45: fails.append("suit_colours")
            if not o.leds_off and glow < 0.001: fails.append("suit_leds")
        if o.fullbody:
            band = m[:, max(0, x0):min(W, x1)]; ys = np.where(m.any(1))[0]
            top = np.where(band.any(1))[0][0]; bot = ys[-1]
            r["body_ratio"] = round(float((bot - top) / fh), 2); r["feet_cut"] = bool(bot >= H - 2)
            if r["body_ratio"] < o.ratio_min: fails.append("body_proportions")
    else:
        r["face_px"] = 0
        if not o.no_face_ok: fails.append("no_face")
    # pose-based proportions (any pose): DWPose, units = face length eyes->chin; sheet torso 4.0-4.3, legs 7.9
    kp, sc = wb(bgr)
    if len(kp):
        j = int(np.argmax([np.ptp(k[:, 1]) for k in kp])); k, q = kp[j], sc[j]; ok = lambda i: q[i] > 0.5
        if ok(1) and ok(2) and q[31] > 0.4:
            E = float(np.linalg.norm((k[1] + k[2]) / 2 - k[31]))
            if all(ok(i) for i in (5, 6, 11, 12)):
                r["torso"] = round(float(np.linalg.norm((k[5] + k[6]) / 2 - (k[11] + k[12]) / 2)) / E, 2)
                if r["torso"] < o.torso_min: fails.append("body_torso")
            legs = [float(np.linalg.norm(k[h] - k[n]) + np.linalg.norm(k[n] - k[f])) for h, n, f in ((11, 13, 15), (12, 14, 16)) if ok(h) and ok(n) and ok(f)]
            if legs:
                r["leg"] = round(max(legs) / E, 2)
                if r["leg"] < o.leg_min: fails.append("body_legs (check foreshortening)")
    # face-free fallback (back views, tiny faces): body keypoints + mask top; sheet legs/torso 1.96-2.13, good 1.87-2.13, big-head 1.62-1.79
    if "torso" not in r and len(kp):
        j = int(np.argmax([np.ptp(k[:, 1]) for k in kp])); k, q = kp[j], sc[j]; okb = lambda i: q[i] > 0.4
        if all(okb(i) for i in (5, 6, 11, 12)):
            sm = (k[5] + k[6]) / 2; T = float(np.linalg.norm(sm - (k[11] + k[12]) / 2)); sw = abs(k[5][0] - k[6][0]); cx = int(sm[0])
            band = m[:, max(0, cx - int(sw) // 4):min(W, cx + int(sw) // 4)]; ys = np.where(band.any(1))[0]
            if len(ys) and sm[1] > ys[0]: r["torso_headneck"] = round(T / float(sm[1] - ys[0]), 2)
            legs = [float(np.linalg.norm(k[h] - k[n]) + np.linalg.norm(k[n] - k[f])) for h, n, f in ((11, 13, 15), (12, 14, 16)) if okb(h) and okb(n) and okb(f)]
            if legs:
                r["leg_torso"] = round(max(legs) / T, 2)
                if r["leg_torso"] < 1.85: fails.append("body_legs_vs_torso (check foreshortening)")
            if r.get("torso_headneck") is not None and r["torso_headneck"] < 1.0: fails.append("body_head_big")
    r["auto_fail"] = fails; r["auto_pass"] = not fails; rows.append(r)
    print(f"{r['file']:28} {'PASS' if not fails else 'FAIL ' + ','.join(fails):28} " + " ".join(f"{k}={v}" for k, v in r.items() if k not in ('file', 'auto_fail', 'auto_pass')))
if o.json: json.dump(rows, open(o.json, "w"), indent=1)
