#!/Users/justin/Code/Project-V/.venv/bin/python
"""Paste the cover Yun (art-only cover crop) into a scene keyframe with a feathered edge, then blend with Z Image Turbo image-to-image.
usage: yun_compose.py <bg.png> <out_prefix> <x> <y> <height_px> [flip 0/1] [strengths comma list] [--prompt-file f]
 x,y = top-left of the pasted head in the 1024x576 frame; height_px = pasted crop height; output: <out_prefix>_paste.png, <out_prefix>_s<strength>.png"""
import json, os, pathlib, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
ROOT = pathlib.Path(__file__).resolve().parent.parent
bg = Image.open(sys.argv[1]).convert("RGB"); prefix = sys.argv[2]
x, y, hpx = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
flip = len(sys.argv) > 6 and sys.argv[6] == "1"
strengths = [float(s) for s in (sys.argv[7] if len(sys.argv) > 7 else "0.45,0.6").split(",")]
prompt = open(sys.argv[9]).read() if len(sys.argv) > 9 and sys.argv[8] == "--prompt-file" else ""
cover = Image.open(ROOT / "input/refs/cover_front_art.png").convert("RGB").crop(tuple(int(v) for v in os.environ.get("YUN_CROP", "230,230,960,810").split(",")))   # Yun head + neck + antlers (override with YUN_CROP=x0,y0,x1,y1)
if flip: cover = cover.transpose(Image.FLIP_LEFT_RIGHT)
w = int(cover.width * hpx / cover.height); cover = cover.resize((w, hpx), Image.LANCZOS)
f = max(8, int(hpx * 0.14))
a = Image.new("L", cover.size, 0); a.paste(255, (f, f, cover.width - f, cover.height - f)); a = a.filter(ImageFilter.GaussianBlur(f * 0.6))
comp = bg.copy(); comp.paste(cover, (x, y), a)
occ = os.environ.get("YUN_OCCLUDE")   # x0,y0,x1,y1: paste this strip of the background back over the head (rock in front of Yun), soft top edge
if occ:
    ox0, oy0, ox1, oy1 = [int(v) for v in occ.split(",")]
    strip = bg.crop((ox0, oy0, ox1, oy1)); m = Image.new("L", strip.size, 255)
    ramp = np.zeros((strip.height, strip.width), np.uint8); n = min(30, strip.height)
    for i in range(strip.height): ramp[i, :] = min(255, int(255 * i / n))
    comp.paste(strip, (ox0, oy0), Image.fromarray(ramp))
comp.save(f"{prefix}_paste.png")
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Volumes/SSD-4T-LR/AI/Models")
for st in strengths:
    o = f"{prefix}_s{int(st*100)}.png"
    subprocess.run(["draw-things-cli", "generate", "--model", "z_image_turbo_1.0_q8p.ckpt", "--no-download-missing", "--disable-preview",
                    "--image", f"{prefix}_paste.png", "--strength", str(st), "--width", "1024", "--height", "576", "--seed", "8801",
                    "--prompt", prompt, "--output", o], env=env, capture_output=True, text=True, timeout=600)
    print("ok" if os.path.exists(o) else "FAIL", o, flush=True)
