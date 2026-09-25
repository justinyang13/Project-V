"""Swap a background window (e.g. the sea seen through the alley gap) for a different generated one, without touching the rest of the picture.
python ../scripts/bg_swap.py --job Video-Zen4 --cand work/bg/c1.png --out input/Video-Zen4.png [--base input/Video-Zen4_sea.png] [--preview work/bg/prev1.png]
The candidate is a picture of the WINDOW (jobs/<id>/bg_window.json: "window" = [x0,y0,x1,y1] in source px and "polys" = polygons (source px) that get replaced).
The patch is resized to the window, matched in brightness/colour to the pixels just outside the replaced area (Reinhard mean/std on a 24 px ring), then pasted with a 6 px feather.
Anything drawn in front of the window (wires, bulbs, railings, rocks you keep) must lie outside "polys"."""
import argparse, json
import cv2, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--job", required=True); ap.add_argument("--cand", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--base", default=None); ap.add_argument("--preview", default=None); ap.add_argument("--feather", type=float, default=6); ap.add_argument("--match", type=float, default=0.8)
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); spec = json.load(open(f"jobs/{a.job}/bg_window.json"))
base = cv2.imread(a.base or job["source"]).astype(np.float32); H, W = base.shape[:2]; x0, y0, x1, y1 = spec["window"]
cand = cv2.resize(cv2.imread(a.cand).astype(np.float32), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
m = np.zeros((H, W), np.uint8)
for p in spec["polys"]: cv2.fillPoly(m, [np.array(p, np.int32)], 255)
patch = base.copy(); patch[y0:y1, x0:x1] = cand
ring = (cv2.dilate(m, np.ones((49, 49), np.uint8)) > 0) & (cv2.dilate(m, np.ones((5, 5), np.uint8)) == 0) & (spec.get("ring_ok") is None or True)
inside = m > 0
for c in range(3):                                            # Reinhard: bring the patch's mean/std at the border towards the surroundings (partial, --match)
    mu_o, sd_o = base[..., c][ring].mean(), base[..., c][ring].std() + 1e-3; mu_n, sd_n = patch[..., c][inside].mean(), patch[..., c][inside].std() + 1e-3
    matched = (patch[..., c] - mu_n) * (sd_o / sd_n) * 0.6 + mu_o + (patch[..., c] - mu_n) * 0.4
    patch[..., c] = np.where(inside, a.match * matched + (1 - a.match) * patch[..., c], patch[..., c])
w = cv2.GaussianBlur(m, (0, 0), a.feather).astype(np.float32)[..., None] / 255
out = w * patch + (1 - w) * base; cv2.imwrite(a.out, np.clip(out + .5, 0, 255).astype(np.uint8)); print("wrote", a.out)
if a.preview: cv2.imwrite(a.preview, cv2.resize(np.clip(out, 0, 255).astype(np.uint8), (960, 544), interpolation=cv2.INTER_AREA))
