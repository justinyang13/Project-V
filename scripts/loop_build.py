"""Build the 10 s seamless loop from two AI clips that start from the same still, composite onto the locked plate, encode, QC.

python scripts/loop_build.py --job 001-snow-tea --a work/.../segA/frames --b work/.../segB/frames --out output/001-snow-tea

Timeline (period P=240 @24fps, fade F=24, each clip needs >= P/2+F = 144 frames):
  t in [0,24)    blend(B[120+t] -> A[t])        loop point: B's tail fades into A's head
  t in [24,120)  A[t]
  t in [120,144) blend(A[t] -> B[t-120])
  t in [144,240) B[t-120]
Both clips begin at the identical source frame, so nothing drifts across the join.
"""
import argparse, glob, json, os, subprocess
import cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--P", type=int, default=240); ap.add_argument("--F", type=int, default=24)
ap.add_argument("--fps", type=int, default=24)
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json"))
OW, OH = job["plate"]["output_size"]
cx0, cy0, cx1, cy1 = job["plate"]["crop"]
sc = OW / (cx1 - cx0)
P, F = a.P, a.F; L = P // 2

# plate + masks in output coordinates
from PIL import Image
src = np.array(Image.open(job["source"]).convert("RGB"))[:, :, ::-1].copy()
plate = cv2.resize(src[cy0:cy1, cx0:cx1], (OW, OH), interpolation=cv2.INTER_LANCZOS4)

def poly_mask(pts):
    m = np.zeros((OH, OW), np.uint8)
    cv2.fillPoly(m, [np.array([[(x - cx0) * sc, (y - cy0) * sc] for x, y in pts], np.int32)], 255)
    return m
R = job["regions"]
M = np.zeros((OH, OW), np.uint8)
for r in R.values():
    if r["role"] == "animated": M = np.maximum(M, poly_mask(r["poly"]))
for r in R.values():
    if r["role"] == "lock": M = np.minimum(M, 255 - poly_mask(r["poly"]))
feather = max(R["exterior"].get("feather_px", 4) * sc, 1)
if job["loop"].get("per_region_feather"):   # each animated region blurred with its own feather_px (Video-Zen3+); default = exterior's feather for all (Video-Zen1)
    lockm = np.zeros((OH, OW), np.uint8)
    for r in R.values():
        if r["role"] == "lock": lockm = np.maximum(lockm, poly_mask(r["poly"]))
    Mf = np.zeros((OH, OW), np.float32)
    for r in R.values():
        if r["role"] == "animated":
            m = np.minimum(poly_mask(r["poly"]), 255 - lockm)
            Mf = np.maximum(Mf, cv2.GaussianBlur(m, (0, 0), max(r.get("feather_px", 4) * sc, 1)).astype(np.float32) / 255.0)
    Mf = Mf[..., None]
else:
    Mf = cv2.GaussianBlur(M, (0, 0), feather).astype(np.float32)[..., None] / 255.0
lock_all = np.zeros((OH, OW), np.uint8)
for r in R.values():
    if r["role"] == "lock": lock_all = np.maximum(lock_all, poly_mask(r["poly"]))
Mf = Mf * (1 - (lock_all[..., None] > 0))

def load(d):
    fs = sorted(glob.glob(d + "/f*.png")); assert len(fs) >= L + F, f"{d}: need >= {L+F} frames, got {len(fs)}"
    return fs
A, B = load(a.a), load(a.b)
cache = {}
def fr(files, i):
    k = (files[0], i)
    if k not in cache:
        if len(cache) > 60: cache.pop(next(iter(cache)))
        cache[k] = cv2.imread(files[i]).astype(np.float32)
    return cache[k]
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

# optional (Video-Zen4): per-region colour match so the AI pixels have the plate's brightness and contrast (the model adds haze and brightens a few %),
# gain = std_plate / std_ai (clamped 0.8..1.4), offset so the means agree; and a mild sharpen (AI clips are 1024x576, the plate is 1080p)
G = np.ones((OH, OW, 3), np.float32); O = np.zeros((OH, OW, 3), np.float32); SH = float(job["loop"].get("ai_sharpen", 0))
if job["loop"].get("match_region_gain"):
    ref = np.mean([cv2.resize(fr(A, i), (OW, OH), interpolation=cv2.INTER_AREA) for i in range(24, 120, 12)], 0)
    accg = np.zeros((OH, OW, 3), np.float32); acco = np.zeros((OH, OW, 3), np.float32); num = np.zeros((OH, OW, 1), np.float32)
    for n, r in R.items():
        if r["role"] != "animated": continue
        m = poly_mask(r["poly"]); sel = (m > 0) & (lock_all == 0)
        if sel.sum() < 50: continue
        pl, rf = plate[sel].astype(np.float32), ref[sel]
        gain = np.clip(pl.std(0) / np.maximum(rf.std(0), 1), 0.8, 1.4) if job["loop"].get("match_region_contrast", True) else np.ones(3, np.float32)
        off = pl.mean(0) - gain * rf.mean(0)
        w = cv2.GaussianBlur(m, (0, 0), max(r.get("feather_px", 4) * sc, 1)).astype(np.float32)[..., None] / 255
        accg += w * gain; acco += w * off; num += w; print(f"match {n}: gain {np.round(gain, 3)} offset {np.round(off, 1)}")
    G = np.where(num > 1e-3, accg / np.maximum(num, 1e-3), 1.0).astype(np.float32); O = acco / np.maximum(num, 1e-3)
os.makedirs(a.out, exist_ok=True); fdir = os.path.join(a.out, "loop_frames"); os.makedirs(fdir, exist_ok=True)
for t in range(P):
    if t < F:            f = (1 - (w := smooth((t + .5) / F))) * fr(B, L + t) + w * fr(A, t)
    elif t < L:          f = fr(A, t)
    elif t < L + F:      f = (1 - (w := smooth((t - L + .5) / F))) * fr(A, t) + w * fr(B, t - L)
    else:                f = fr(B, t - L)
    up = cv2.resize(f, (OW, OH), interpolation=cv2.INTER_LANCZOS4)
    if SH: up = cv2.addWeighted(up, 1 + SH, cv2.GaussianBlur(up, (0, 0), 1.6), -SH, 0)
    up = up * G + O
    out = Mf * up + (1 - Mf) * plate
    cv2.imwrite(f"{fdir}/f{t:04d}.png", np.clip(out + .5, 0, 255).astype(np.uint8))
cv2.imwrite(os.path.join(a.out, "plate.png"), plate); cv2.imwrite(os.path.join(a.out, "mask.png"), (Mf[..., 0] * 255).astype(np.uint8))

base = os.path.join(a.out, f"{a.job}_loop10s_1080p{a.fps}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", f"{fdir}/f%04d.png", "-c:v", "libx264", "-crf", "14",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", base + ".mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "5", "-i", base + ".mp4", "-c", "copy", os.path.join(a.out, f"{a.job}_preview60s.mp4")], check=True)

# ---- QC ----
sel = Mf[..., 0] > 0.5
def g(i): return cv2.cvtColor(cv2.imread(f"{fdir}/f{i % P:04d}.png"), cv2.COLOR_BGR2GRAY).astype(np.float32)
prev = g(0); diffs = []; lum = [prev[sel].mean()]
for i in range(1, P):
    cur = g(i); diffs.append(np.abs(cur - prev)[sel].mean()); lum.append(cur[sel].mean()); prev = cur
seam = np.abs(g(0) - g(P - 1))[sel].mean()
med = float(np.median(diffs)); jumps = np.abs(np.diff(lum))
lock_ok = True
for i in (0, 57, 130, 239):
    f = cv2.imread(f"{fdir}/f{i:04d}.png"); lock_ok &= bool((f[Mf[..., 0] == 0] == plate[Mf[..., 0] == 0]).all())
rep = {"frames": P, "seam_diff": round(float(seam), 3), "median_consecutive_diff": round(med, 3), "seam_ratio": round(float(seam) / med, 3),
       "max_frame_diff": round(float(max(diffs)), 3), "luma_std_detrended": round(float(np.std(np.array(lum) - np.convolve(np.tile(lum, 3), np.ones(24) / 24, 'same')[P:2 * P])), 3),
       "luma_max_jump": round(float(jumps.max()), 3), "locked_pixels_identical": lock_ok}
json.dump(rep, open(os.path.join(a.out, "qc_final.json"), "w"), indent=1); print(json.dumps(rep, indent=1))
# seam sheet: frames 232..239 then 0..7
tiles = [cv2.resize(cv2.imread(f"{fdir}/f{i % P:04d}.png"), (480, 270)) for i in list(range(232, 240)) + list(range(0, 8))]
cv2.imwrite(os.path.join(a.out, "sheet_seam.png"), np.vstack([np.hstack(tiles[r * 4:(r + 1) * 4]) for r in range(4)]))
