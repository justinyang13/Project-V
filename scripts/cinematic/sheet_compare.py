#!/usr/bin/env python3
"""Side-by-side consistency strip: each candidate's figure (RMBG mask bbox) scaled to the SAME HEIGHT as the
reference-sheet panels, with horizontal guide lines every 1/8 of the height (head units), so head size, leg length,
slimness, suit design and hair can be compared directly. Run with the ComfyUI venv.
Usage: sheet_compare.py out.jpg --sheet full_front.png full_34l.png full_side.png --img a.png b.png ... [--h 900]"""
import argparse, os, numpy as np, cv2, torch
from PIL import Image, ImageDraw
os.environ.setdefault("HF_HOME", "/Users/Maxi/Code/Models/hf-cache")
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
a = argparse.ArgumentParser(); a.add_argument("out"); a.add_argument("--sheet", nargs="+", required=True)
a.add_argument("--img", nargs="+", required=True); a.add_argument("--h", type=int, default=900); o = a.parse_args()
seg = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-2.0", trust_remote_code=True).to("mps").eval()
tf = transforms.Compose([transforms.Resize((1024, 1024)), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
def figure(p):
    im = Image.open(p).convert("RGB"); W, H = im.size
    with torch.no_grad(): m = seg(tf(im).unsqueeze(0).to("mps"))[-1].sigmoid().cpu()[0, 0].numpy()
    m = cv2.resize(m, (W, H)) > 0.5; ys, xs = np.where(m)
    if not len(ys): return im
    pad = int(0.02 * H); c = im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(W, xs.max() + pad), min(H, ys.max() + pad)))
    return c
tiles = []
for p in o.sheet + o.img:
    f = figure(p); s = o.h / f.height; f = f.resize((max(1, int(f.width * s)), o.h), Image.LANCZOS)
    t = Image.new("RGB", (f.width + 20, o.h + 24), (30, 30, 30)); t.paste(f, (10, 24)); d = ImageDraw.Draw(t)
    for k in range(1, 8): y = 24 + k * o.h // 8; d.line([(0, y), (t.width, y)], fill=(255, 80, 80), width=1)
    d.text((6, 5), ("SHEET " if p in o.sheet else "") + os.path.basename(p), fill=(255, 255, 255)); tiles.append(t)
S = Image.new("RGB", (sum(t.width for t in tiles), o.h + 24), (30, 30, 30)); x = 0
for t in tiles: S.paste(t, (x, 0)); x += t.width
S.save(o.out, quality=90); print(o.out, S.size)
