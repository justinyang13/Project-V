"""Depth map of the plate for rain_overlay.py (0 = near .. 1 = far). Depth Anything V2 Small, from the SSD.
../tools/moss-env/bin/python ../scripts/depth_map.py --job Video-Zen6     (run from the video folder)
Writes work/<job>/depth.npy (plate size, float32) and work/<job>/depth_vis.png."""
import argparse, json, os
import numpy as np, torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
ap = argparse.ArgumentParser(); ap.add_argument("--job", required=True); a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); x0, y0, x1, y1 = job["plate"]["crop"]
im = Image.open(job["source"]).convert("RGB").crop((x0, y0, x1, y1))
M = "/Volumes/SSD-4T-LR/AI/Models/Depth-Anything-V2-Small"
proc = AutoImageProcessor.from_pretrained(M); model = AutoModelForDepthEstimation.from_pretrained(M).eval()
with torch.no_grad(): out = model(**proc(images=im, return_tensors="pt")).predicted_depth      # larger = nearer
d = torch.nn.functional.interpolate(out[None], size=(im.height, im.width), mode="bicubic", align_corners=False)[0, 0].numpy()
d = 1.0 - (d - d.min()) / (d.max() - d.min())                                                    # 0 = near .. 1 = far
os.makedirs(f"work/{a.job}", exist_ok=True); np.save(f"work/{a.job}/depth.npy", d.astype(np.float32))
Image.fromarray((d * 255).astype(np.uint8)).save(f"work/{a.job}/depth_vis.png"); print("depth", d.shape, d.min(), d.max())
