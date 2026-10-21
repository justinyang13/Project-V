#!/usr/bin/env python3
"""Assemble the cut: hard cuts, per-shot trims, 2.39:1 scope letterbox in 16:9, sequence grade, light grain, title card.
Usage (family-lora-venv): edit_cut.py --film <dir> --out edit/cut_v1.mp4 [--w 1920 --h 1080] [--fps 24] [--no-grade]
Per shot: len = min(SHOTLIST dur_s, clip length, trims end_s). Silent video (audio is mixed later)."""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
a = argparse.ArgumentParser(); a.add_argument("--film", required=True); a.add_argument("--out", required=True)
a.add_argument("--w", type=int, default=1920); a.add_argument("--h", type=int, default=1080); a.add_argument("--fps", type=int, default=24)
a.add_argument("--no-grade", action="store_true"); o = a.parse_args(); F = os.path.abspath(o.film)
S = json.load(open(f"{F}/story/SHOTLIST.json"))["shots"]; trims = json.load(open(f"{F}/edit_trims.json")) if os.path.exists(f"{F}/edit_trims.json") else {}
bar = int(round((o.h - o.w / 2.39) / 2 / 2)) * 2; ah = o.h - 2 * bar
GRADE = {"L1": (1.02, 1.05, 0.0), "L2": (1.0, 1.0, 0.0), "L3": (1.03, 1.08, 0.0), "L4": (1.02, 1.06, 0.0)}  # gain, sat, lift
def grade(fr, loc):
    if o.no_grade: return fr
    g, s, l = GRADE.get(loc, (1, 1, 0))
    x = fr.astype(np.float32) / 255.0
    x = x * g + l; x = np.clip(x, 0, 1)
    # filmic-ish toe/shoulder curve (gentle S), then saturation
    x = x * x * (3 - 2 * x) * 0.35 + x * 0.65
    gray = x.mean(axis=2, keepdims=True); x = np.clip(gray + (x - gray) * s, 0, 1)
    return (x * 255).astype(np.uint8)
tmp = tempfile.mkdtemp(prefix="cut_", dir=f"{F}/work"); parts = []
rng = np.random.default_rng(7)
for sh in S:
    i = sh["id"]; out = f"{tmp}/{i}.mp4"
    if i == "T01":
        W, H = o.w, o.h; base = np.zeros((H, W, 3), np.uint8)
        img = Image.fromarray(base); d = ImageDraw.Draw(img)
        font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", int(H * 0.11), index=5) if os.path.exists("/System/Library/Fonts/Avenir Next.ttc") else ImageFont.load_default()
        txt = "A S T R A"; bb = d.textbbox((0, 0), txt, font=font); d.text(((W - (bb[2] - bb[0])) // 2, (H - (bb[3] - bb[1])) // 2 - int(H * 0.02)), txt, fill=(170, 210, 255), font=font)
        card = np.array(img); n = int(sh["dur_s"] * o.fps); vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), o.fps, (W, H))
        for k in range(n):
            t = k / max(1, n - 1); amp = min(1, t / 0.25) * min(1, (1 - t) / 0.3); vw.write(cv2.cvtColor((card * amp).astype(np.uint8), cv2.COLOR_RGB2BGR))
        vw.release(); parts.append(out); continue
    src = f"{F}/clips/{i}/chosen.mp4"
    cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS) or 25; nsrc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    want = sh["dur_s"]; want = min(want, nsrc / fps); 
    if i in trims: want = min(want, trims[i]["end_s"])
    n = int(round(want * o.fps)); vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), o.fps, (o.w, o.h))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    for k in range(n):
        f = frames[min(len(frames) - 1, int(round(k * fps / o.fps)))]
        f = cv2.resize(f, (o.w, ah), interpolation=cv2.INTER_LANCZOS4)
        f = grade(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), sh["location"])
        # fine grain
        gr = rng.normal(0, 3.0, f.shape[:2]).astype(np.float32)[..., None]; f = np.clip(f.astype(np.float32) + gr, 0, 255).astype(np.uint8)
        canvas = np.zeros((o.h, o.w, 3), np.uint8); canvas[bar:bar + ah] = f; vw.write(cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
    vw.release(); parts.append(out); print(i, f"{want:.2f}s", flush=True)
lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", str(o.fps), os.path.abspath(o.out)])
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", o.out], capture_output=True, text=True).stdout)
print("cut", o.out, f"{dur:.1f}s", "bars", bar)
