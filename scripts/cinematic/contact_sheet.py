#!/usr/bin/env python3
"""Contact sheet of images (or of frames sampled from videos) with labels.
Usage: contact_sheet.py out.jpg img_or_video ... [--cols 6] [--w 320] [--frames 4]"""
import argparse, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont
a = argparse.ArgumentParser(); a.add_argument("out"); a.add_argument("items", nargs="+")
a.add_argument("--cols", type=int, default=6); a.add_argument("--w", type=int, default=320)
a.add_argument("--frames", type=int, default=4); o = a.parse_args()
tiles = []
def label(im, t):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, im.width, 18], fill=(0, 0, 0)); d.text((4, 3), t, fill=(255, 255, 255)); return im
for p in o.items:
    n = os.path.basename(p)
    if p.lower().endswith((".mp4", ".mov")):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 1)
        for k in range(o.frames):
            t = dur * (k + 0.5) / o.frames
            with tempfile.NamedTemporaryFile(suffix=".png") as f:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", f.name])
                im = Image.open(f.name).convert("RGB")
            im.thumbnail((o.w, o.w * 2)); tiles.append(label(im, f"{n} {t:.1f}s"))
    else:
        im = Image.open(p).convert("RGB"); im.thumbnail((o.w, o.w * 2)); tiles.append(label(im, n))
th = max(t.height for t in tiles); rows = (len(tiles) + o.cols - 1) // o.cols
S = Image.new("RGB", (o.cols * o.w, rows * th), (20, 20, 20))
for i, t in enumerate(tiles): S.paste(t, ((i % o.cols) * o.w, (i // o.cols) * th))
S.save(o.out, quality=88); print(o.out, S.size)
