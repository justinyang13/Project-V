"""Remove the slow zoom/shift the video model adds (Lessons A12/A15), separately for every animated region.
python ../scripts/stabilize.py --job Video-Zen4 --frames work/Video-Zen4/r01/t_s101/frames --out work/Video-Zen4/r01/t_s101/stab
For each animated region R: match ORB features between frame 0 and frame i only in a RING around R (dilated by --ring px, minus everything animated,
so it uses the locked things next to R: rocks, walls, table), fit a similarity transform with RANSAC (1.5 px), and warp frame i back onto frame 0.
The output frame takes each region's pixels from its own warp (region mask dilated by 12 px), the rest from the global warp.
Only animated regions reach the final composite, so replicated borders at the image edge do not matter as long as no region touches the edge.
Fits are noisy per frame (~0.8 px), so every parameter track (scale, rotation, dx, dy) is Gaussian-smoothed over time (--smooth frames) before warping; the drift is slow and smooth, the noise is not.\nFalls back to the global transform when a ring has < --min_inl inliers. Writes stab_report.json."""
import argparse, glob, json, os
import cv2, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--frames", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--ring", type=int, default=150); ap.add_argument("--min_inl", type=int, default=25); ap.add_argument("--feat", type=int, default=6000); ap.add_argument("--smooth", type=float, default=8.0, help="Gaussian sigma in frames for the per-region transform")
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); fs = sorted(glob.glob(a.frames + "/f*.png"))
g0 = cv2.cvtColor(cv2.imread(fs[0]), cv2.COLOR_BGR2GRAY); H, W = g0.shape
x0, y0, x1, y1 = job["plate"]["crop"]; sc = W / (x1 - x0)
def pm(pts):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array([[(x - x0) * sc, (y - y0) * sc] for x, y in pts], np.int32)], 255); return m
R = job["regions"]; anim = {n: pm(r["poly"]) for n, r in R.items() if r["role"] == "animated"}
lock = np.zeros((H, W), np.uint8)
for r in R.values():
    if r["role"] == "lock": lock = np.maximum(lock, pm(r["poly"]))
all_anim = np.zeros((H, W), np.uint8)
for m in anim.values(): all_anim = np.maximum(all_anim, m)
all_anim = cv2.subtract(all_anim, lock); nonanim = cv2.dilate(all_anim, np.ones((17, 17), np.uint8)) == 0
k = int(a.ring * sc) | 1
ring = {n: (cv2.dilate(m, np.ones((k, k), np.uint8)) > 0) & nonanim for n, m in anim.items()}
ring["_global"] = nonanim
orb = cv2.ORB_create(a.feat); k0, d0 = orb.detectAndCompute(g0, None); p0 = np.float32([q.pt for q in k0])
inring = {n: np.array([m[int(min(max(p[1], 0), H - 1)), int(min(max(p[0], 0), W - 1))] for p in p0]) for n, m in ring.items()}
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
os.makedirs(a.out, exist_ok=True)
feath = {n: cv2.GaussianBlur(cv2.dilate(m, np.ones((25, 25), np.uint8)), (0, 0), 5).astype(np.float32)[..., None] / 255 for n, m in anim.items()}
def fit(m, sel):
    ms = [x for x in m if sel[x.queryIdx]]
    if len(ms) < 8: return None, 0, 0.0
    src = np.float32([p0[x.queryIdx] for x in ms]); dst = np.float32([kk[x.trainIdx].pt for x in ms])
    A, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.5)
    if A is None: return None, 0, 0.0
    i = inl.ravel() > 0; res = np.linalg.norm(cv2.transform(src[i][None], A)[0] - dst[i], axis=1)
    return A, int(i.sum()), float(res.mean())
rep = {n: [] for n in anim}; rep["_global"] = []
def par(A): return [float(np.hypot(A[0, 0], A[1, 0])), float(np.arctan2(A[1, 0], A[0, 0])), float(A[0, 2]), float(A[1, 2])]
def mat(v): s, t, tx, ty = v; return np.float32([[s * np.cos(t), -s * np.sin(t), tx], [s * np.sin(t), s * np.cos(t), ty]])
P = {n: [[1.0, 0.0, 0.0, 0.0]] for n in list(anim) + ["_global"]}; NI = {n: [999] for n in P}
for i, f in enumerate(fs):                     # pass 1: fit every frame (frame 0 is the identity)
    if i == 0: continue
    g = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY); kk, dd = orb.detectAndCompute(g, None); m = bf.match(d0, dd)
    Ag, ng, rg = fit(m, inring["_global"]); assert Ag is not None, f"global fit failed at frame {i}"
    P["_global"].append(par(Ag)); NI["_global"].append(ng)
    for n in anim:
        A, ninl, res = fit(m, inring[n])
        if A is None or ninl < a.min_inl: A, ninl = Ag, -max(ninl, 1)
        P[n].append(par(A)); NI[n].append(ninl)
def smooth(v, sig):                            # Gaussian smoothing over time, edge values repeated; frame 0 stays the identity
    v = np.array(v); r = int(3 * sig); w = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); w /= w.sum()
    out = np.stack([np.convolve(np.pad(v[:, c], r, mode="edge"), w, "valid") for c in range(4)], 1); out[0] = v[0]; return out
S = {n: smooth(P[n], a.smooth) for n in P}
for i, f in enumerate(fs):                     # pass 2: warp with the smoothed transforms
    img = cv2.imread(f)
    if i == 0: cv2.imwrite(f"{a.out}/f{i:04d}.png", img); continue
    def warp(A): return cv2.warpAffine(img, A, (W, H), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    out = warp(mat(S["_global"][i])).astype(np.float32)
    for n in anim:
        w = feath[n]; out = w * warp(mat(S[n][i])).astype(np.float32) + (1 - w) * out
    cv2.imwrite(f"{a.out}/f{i:04d}.png", np.clip(out + .5, 0, 255).astype(np.uint8))
json.dump({n: {"raw": P[n], "smooth": S[n].tolist(), "inliers": NI[n]} for n in P}, open(os.path.join(a.out, "stab_report.json"), "w"))
print("region            inliers(last)  scale   dx     dy   raw-vs-smooth rms of dx,dy (px)   (inliers<0 = fell back to global)")
for n in P:
    r = np.array(P[n])[:, 2:]; sm = S[n][:, 2:]
    print(f"{n:18s} {NI[n][-1]:6d} {S[n][-1][0]:9.4f} {S[n][-1][2]:6.1f} {S[n][-1][3]:6.1f}   {np.sqrt(((r-sm)**2).mean()):5.2f}")
