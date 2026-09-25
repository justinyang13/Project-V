"""Crisp, seamless flicker for lanterns and neon signs (procedural; used instead of the AI clip, which blurs small bright objects).
python ../scripts/flicker.py --job Video-Zen4 --frames work/Video-Zen4/loop/loop_frames --out work/Video-Zen4/loop_flicker [--seed 5]
Every job.json region with role "flicker" ("amp": brightness swing, e.g. 0.10 = +-10 %) gets its own smooth periodic brightness curve: a sum of sine waves with a whole number of cycles
per loop (period = number of input frames), so frame 0 follows the last frame exactly. Lanterns also get a slow warm 'breath' (r/g/b gains differ slightly). Neon adds a rare faint dip.
Pixels outside these regions are copied unchanged."""
import argparse, glob, json, os
import cv2, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--job", required=True); ap.add_argument("--frames", required=True); ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, default=5)
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); fs = sorted(glob.glob(a.frames + "/f*.png")); P = len(fs)
OW, OH = job["plate"]["output_size"]; cx0, cy0, cx1, cy1 = job["plate"]["crop"]; sc = OW / (cx1 - cx0)
rng = np.random.default_rng(a.seed); os.makedirs(a.out, exist_ok=True)
def pm(pts):
    m = np.zeros((OH, OW), np.uint8); cv2.fillPoly(m, [np.array([[(x - cx0) * sc, (y - cy0) * sc] for x, y in pts], np.int32)], 255); return m
regs = []
for n, r in job["regions"].items():
    if r["role"] != "flicker": continue
    m = cv2.GaussianBlur(pm(r["poly"]), (0, 0), max(r.get("feather_px", 3) * sc, 1)).astype(np.float32)[..., None] / 255
    harm = rng.choice([2, 3, 5, 7, 11, 17], size=3, replace=False); ph = rng.uniform(0, 2 * np.pi, 3); wt = rng.uniform(0.5, 1.0, 3); wt /= wt.sum()
    t = np.arange(P) / P; curve = sum(w * np.sin(2 * np.pi * h * t + p) for w, h, p in zip(wt, harm, ph))
    if n.startswith("neon"):                                   # neon: occasional shallow dip (periodic, one per loop at a random place)
        c0 = rng.uniform(0, P); d = np.minimum(np.abs(np.arange(P) - c0), P - np.abs(np.arange(P) - c0)); curve = curve - 1.2 * np.exp(-(d / 2.5) ** 2)
    curve = curve / max(np.abs(curve).max(), 1e-6)
    warm = np.sin(2 * np.pi * 2 * t + rng.uniform(0, 6.28))     # slow warm/cool breath, 2 cycles per loop
    regs.append((n, m, float(r.get("amp", 0.1)), curve, warm, n.startswith("lantern")))
print("flicker regions:", [r[0] for r in regs])
for t in range(P):
    img = cv2.imread(fs[t]).astype(np.float32); out = img.copy()
    for n, m, amp, curve, warm, isl in regs:
        g = 1 + amp * curve[t]
        gain = np.array([g * (1 - 0.25 * amp * warm[t]), g, g * (1 + 0.35 * amp * warm[t])], np.float32) if isl else np.array([g, g, g], np.float32)   # BGR: warm = more red, less blue
        out = out + m * (img * gain - img)
    cv2.imwrite(f"{a.out}/f{t:04d}.png", np.clip(out + .5, 0, 255).astype(np.uint8))
print("wrote", P, "frames to", a.out)
