#!/usr/bin/env python3
"""Body proportion check for standing full-body images.
ratio = person height (RMBG-2.0 mask bbox, top of head to soles) / face box height (insightface det, brows-to-chin approx).
Realistic adult ~7.5-8 heads tall gives a ratio of roughly 9.5-11 (calibrate on the character sheet).
Usage (ComfyUI venv for torch+transformers): body_ratio.py img1.png ... [--json out.json] [--masks dir]
QA only: RMBG-2.0 is CC BY-NC, never used to make film content."""
import argparse, json, os, sys, numpy as np, torch, cv2
from PIL import Image
os.environ.setdefault("HF_HOME", "/Users/Maxi/Code/Models/hf-cache")
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
a = argparse.ArgumentParser(); a.add_argument("imgs", nargs="+"); a.add_argument("--json"); a.add_argument("--masks"); o = a.parse_args()
dev = "mps" if torch.backends.mps.is_available() else "cpu"
seg = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-2.0", trust_remote_code=True).to(dev).eval()
tf = transforms.Compose([transforms.Resize((1024, 1024)), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
sys.path.insert(0, "/Users/Maxi/Code/Tools/family-lora-venv/lib/python3.14/site-packages")
from insightface.app import FaceAnalysis
fa = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"], allowed_modules=["detection"]); fa.prepare(ctx_id=-1, det_size=(1024, 1024))
rows = []
for p in o.imgs:
    im = Image.open(p).convert("RGB"); W, H = im.size
    with torch.no_grad(): m = seg(tf(im).unsqueeze(0).to(dev))[-1].sigmoid().cpu()[0, 0].numpy()
    m = cv2.resize(m, (W, H)) > 0.5
    ys = np.where(m.any(1))[0]
    bgr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR); s = 1.0
    if max(W, H) < 1200: s = 1600 / max(W, H); bgr = cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4)
    fs = fa.get(bgr)
    if not len(ys) or not fs: rows.append(dict(file=p, ratio=None)); print(os.path.basename(p), "no person/face"); continue
    f = max(fs, key=lambda f: f.bbox[3] - f.bbox[1]); fh = (f.bbox[3] - f.bbox[1]) / s
    # person top: highest mask pixel in the column band of the face (ignores a ponytail flying sideways)
    x0, x1 = int(f.bbox[0] / s), int(f.bbox[2] / s); band = m[:, max(0, x0):min(W, x1)]
    top = np.where(band.any(1))[0][0]; bot = ys[-1]
    r = dict(file=p, person_px=int(bot - top), face_px=round(float(fh), 1), ratio=round(float((bot - top) / fh), 2), touches_bottom=bool(bot >= H - 2))
    rows.append(r); print(f"{os.path.basename(p):32} ratio {r['ratio']:5}  person {r['person_px']}px face {r['face_px']}px{'  FEET CUT' if r['touches_bottom'] else ''}")
    if o.masks: os.makedirs(o.masks, exist_ok=True); Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(o.masks, os.path.basename(p)))
if o.json: json.dump(rows, open(o.json, "w"), indent=1)
