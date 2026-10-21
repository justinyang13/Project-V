#!/usr/bin/env python3
"""LTX-2.3 image-to-video per shot (resumable): keyframe chosen.png -> 1088x448 start frame -> LTX takes (seeds) ->
identity QA on sampled frames (face, hair, suit, body) + motion check -> chosen.mp4 (reversed when the shot says so).
Writes clips/<id>/{start.png, take_s<seed>.mp4, qa.json, chosen.mp4}. Claude reviews contact sheets after.
Usage (family-lora-venv): clips_run.py --film <dir> [--only A03,B02] [--seeds 21 22] [--w 1088 --h 448]"""
import argparse, json, os, shutil, subprocess, sys, glob
import numpy as np, cv2
H = os.path.dirname(os.path.abspath(__file__)); CVENV = "/Users/Maxi/Documents/Default Project/ComfyUI/.venv/bin/python"
CLI = os.path.expanduser("~/.claude/bin/dt-cli-26.0928.0/draw-things-cli")
a = argparse.ArgumentParser(); a.add_argument("--film", required=True); a.add_argument("--only", default="")
a.add_argument("--seeds", nargs="+", type=int, default=[21, 22]); a.add_argument("--w", type=int, default=1088); a.add_argument("--h", type=int, default=448)
o = a.parse_args(); F = os.path.abspath(o.film); only = set(filter(None, o.only.split(",")))
P = json.load(open(f"{F}/clips/prompts.json")); SH = {s["id"]: s for s in json.load(open(f"{F}/story/SHOTLIST.json"))["shots"]}
REF = [f"{F}/bible/refs/face_ref_closeup.png", f"{F}/bible/refs/astra_canon_front.png"]
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Users/Maxi/Code/Models")
def frames(mp4, step=12):
    cap = cv2.VideoCapture(mp4); out = []; i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if i % step == 0: out.append(f)
        i += 1
    return out, i
def motion(mp4):
    cap = cv2.VideoCapture(mp4); prev = None; d = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, (272, 112)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None: d.append(float(np.abs(g - prev).mean()))
        prev = g
    return d
for i, pr in P.items():
    if only and i not in only: continue
    kf = f"{F}/keyframes/{i}/chosen.png"; d = f"{F}/clips/{i}"
    if not os.path.exists(kf): print(i, "no keyframe", flush=True); continue
    os.makedirs(d, exist_ok=True)
    if os.path.exists(f"{d}/chosen.mp4"): continue
    st = f"{d}/start.png"
    if not os.path.exists(st):
        im = cv2.imread(kf); ih, iw = im.shape[:2]; tr = o.w / o.h
        if iw / ih > tr: nw = int(ih * tr); im = im[:, (iw - nw) // 2:(iw - nw) // 2 + nw]
        else: nh = int(iw / tr); im = im[(ih - nh) // 2:(ih - nh) // 2 + nh]
        cv2.imwrite(st, cv2.resize(im, (o.w, o.h), interpolation=cv2.INTER_AREA))
    takes = []
    for s in o.seeds:
        t = f"{d}/take_s{s}.mp4"
        if not os.path.exists(t):
            r = subprocess.run([CLI, "generate", "--model", "ltx_2.3_22b_distilled_1.1_q8p.ckpt", "--no-download-missing", "--image", st,
                                "--prompt", pr["prompt"], "--frames", str(pr["frames"]), "--width", str(o.w), "--height", str(o.h), "--seed", str(s), "--output", t],
                               env=env, capture_output=True, text=True, timeout=1800)
            if not os.path.exists(t): print(i, s, "LTX FAIL", (r.stderr or r.stdout)[-200:], flush=True); continue
        takes.append(t)
    res = {}
    kind = SH[i]["kind"]
    for t in takes:
        fr, n = frames(t); tmp = f"{d}/_f_{os.path.basename(t)[:-4]}"; os.makedirs(tmp, exist_ok=True)
        ps = []
        for k, f in enumerate(fr): p = f"{tmp}/{k:03d}.png"; cv2.imwrite(p, f); ps.append(p)
        j = f"{tmp}/qa.json"
        subprocess.run([CVENV, f"{H}/identity_qa.py", "--ref", *REF, "--img", *ps, "--no_face_ok", "--min_face", "40", "--json", j], capture_output=True)
        rows = json.load(open(j)) if os.path.exists(j) else []
        intruder = kind in ("noface", "detail") and any(r.get("face_px", 0) > 0 for r in rows[1:])  # a person/face appears where the shot has none
        faces = [r["face"] for r in rows if r.get("face") is not None]; tors = [r["torso"] for r in rows if "torso" in r]
        mv = motion(t)
        res[t] = dict(frames=n, face_min=min(faces) if faces else None, face_med=float(np.median(faces)) if faces else None,
                      face_drop=max((faces[k] - faces[k + 1]) for k in range(len(faces) - 1)) if len(faces) > 1 else 0,
                      torso_min=min(tors) if tors else None, motion_mean=float(np.mean(mv)) if mv else 0, motion_max=float(max(mv)) if mv else 0,
                      still_frac=float(np.mean(np.array(mv) < 0.15)) if mv else 1, intruder=bool(intruder))
    def score(t):
        r = res[t]; ok_face = (r["face_min"] is None or r["face_min"] >= 0.45) and not r["intruder"]
        ok_body = r["torso_min"] is None or r["torso_min"] >= 3.3
        return (ok_face and ok_body, (r["face_med"] or 0) + (0.2 if r["still_frac"] < 0.5 else 0))
    if not takes: continue
    best = max(takes, key=score)
    if pr.get("reverse"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", best, "-vf", "reverse", "-an", f"{d}/chosen.mp4"])
    else: shutil.copy(best, f"{d}/chosen.mp4")
    json.dump(dict(takes=res, chosen=best, reversed=bool(pr.get("reverse"))), open(f"{d}/qa.json", "w"), indent=1)
    r = res[best]; print(i, "chosen", os.path.basename(best), {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
