#!/usr/bin/env python3
"""Pose-based body proportion check (any pose): DWPose whole-body (yolox_l + dw-ll_ucoco_384, Apache 2.0,
/Users/Maxi/Code/Models/dwpose) via rtmlib. Units = face length E (eye midpoint to chin landmark).
  leg   = mean over visible sides of hip->knee + knee->ankle   (/E)
  torso = shoulder midpoint -> hip midpoint                    (/E)
  shld  = shoulder width                                        (/E)
Segment lengths are 2D, so foreshortened limbs read short: only judge limbs whose keypoint scores are high,
and read the number together with the sheet_compare strip. Run with family-lora-venv.
Usage: pose_body.py img ... [--json out.json] [--draw dir]"""
import argparse, json, os, numpy as np, cv2
from rtmlib import Wholebody, draw_skeleton
D = "/Users/Maxi/Code/Models/dwpose"
a = argparse.ArgumentParser(); a.add_argument("imgs", nargs="+"); a.add_argument("--json"); a.add_argument("--draw"); o = a.parse_args()
wb = Wholebody(det=f"{D}/yolox_l.onnx", det_input_size=(640, 640), pose=f"{D}/dw-ll_ucoco_384.onnx",
               pose_input_size=(288, 384), backend="onnxruntime", device="cpu")
def dist(p, q): return float(np.linalg.norm(p - q))
rows = []
for p in o.imgs:
    im = cv2.imread(p); kp, sc = wb(im); r = dict(file=os.path.basename(p))
    if len(kp) == 0: r["note"] = "no person"; rows.append(r); print(r["file"], "no person"); continue
    i = int(np.argmax([np.ptp(k[:, 1]) for k in kp])); k, s = kp[i], sc[i]; ok = lambda j: s[j] > 0.5
    eyes = (k[1] + k[2]) / 2; chin = k[31]                       # 23+8 = chin in the 68-point face set
    E = dist(eyes, chin) if ok(1) and ok(2) and s[31] > 0.4 else None
    if not E: r["note"] = "face not measurable"; rows.append(r); print(r["file"], r["note"]); continue
    legs = [dist(k[h], k[n]) + dist(k[n], k[f]) for h, n, f in ((11, 13, 15), (12, 14, 16)) if ok(h) and ok(n) and ok(f)]
    if legs: r["leg"] = round(max(legs) / E, 2)
    if all(ok(j) for j in (5, 6, 11, 12)): r["torso"] = round(dist((k[5] + k[6]) / 2, (k[11] + k[12]) / 2) / E, 2)
    if ok(5) and ok(6): r["shld"] = round(dist(k[5], k[6]) / E, 2)
    r["E_px"] = round(E, 1); rows.append(r)
    print(f"{r['file']:28} leg {r.get('leg','-'):>6} torso {r.get('torso','-'):>6} shld {r.get('shld','-'):>6}  E {r['E_px']}px")
    if o.draw:
        os.makedirs(o.draw, exist_ok=True); cv2.imwrite(os.path.join(o.draw, r["file"]), draw_skeleton(im.copy(), kp[i:i+1], sc[i:i+1], kpt_thr=0.5))
if o.json: json.dump(rows, open(o.json, "w"), indent=1)
