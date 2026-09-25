"""Motion metrics per region on a frames dir (1024x576 plate coords). Usage: qc_motion.py <frames_dir>
Regions (from job source coords, scale 0.5999, offset x-10): snow area, steam box, fire box."""
import sys, glob, json, cv2, numpy as np
fs = sorted(glob.glob(sys.argv[1] + "/f*.png"))
R = {"snow": (200, 12, 575, 330), "steam": (579, 228, 660, 372), "fire": (657, 177, 711, 243)}      # first video only
CTRL = None
if "--job" in sys.argv:   # regions = the job's qc_only boxes (source px -> frame px); control = the non-animated area, which should stay still
    job = json.load(open(f"jobs/{sys.argv[sys.argv.index('--job') + 1]}/job.json")); x0, y0, x1, y1 = job["plate"]["crop"]
    H0, W0 = cv2.imread(fs[0]).shape[:2]; sc = W0 / (x1 - x0); R = {}
    for n, r in job["regions"].items():
        if r["role"] == "qc_only":
            xs = [p[0] for p in r["poly"]]; ys = [p[1] for p in r["poly"]]
            R[n.replace("_qc", "")] = tuple(int(v) for v in ((min(xs) - x0) * sc, (min(ys) - y0) * sc, (max(xs) - x0) * sc, (max(ys) - y0) * sc))
    an = np.zeros((H0, W0), np.uint8)
    for r in job["regions"].values():
        if r["role"] == "animated": cv2.fillPoly(an, [np.array([[(x - x0) * sc, (y - y0) * sc] for x, y in r["poly"]], np.int32)], 255)
    CTRL = cv2.dilate(an, np.ones((33, 33), np.uint8)) == 0
g = [cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY) for f in fs]
def crop(a, r): x0, y0, x1, y1 = r; return a[y0:y1, x0:x1]
for name, r in R.items():
    lum = [crop(x, r).mean() for x in g]
    diffs = [np.abs(crop(g[i+1], r).astype(float) - crop(g[i], r).astype(float)).mean() for i in range(len(g)-1)]
    ups = downs = 0
    for i in range(0, len(g)-1, 6):
        fl = cv2.calcOpticalFlowFarneback(crop(g[i], r), crop(g[i+1], r), None, .5, 3, 15, 3, 5, 1.2, 0)
        mag = np.hypot(fl[..., 0], fl[..., 1]); mv = mag > 0.3
        ups += int(((fl[..., 1] < 0) & mv).sum()); downs += int(((fl[..., 1] > 0) & mv).sum())
    tot = max(ups + downs, 1)
    print(f"{name:6s} mean_frame_diff={np.mean(diffs):5.2f}  luma_std_over_time={np.std(lum):5.2f}  moving_down={downs/tot:4.0%} up={ups/tot:4.0%}")

if CTRL is not None:   # control: change in the area that must not move (compression/noise floor); effects should be clearly above it
    cd = np.mean([np.abs(g[i + 1].astype(float) - g[i].astype(float))[CTRL].mean() for i in range(len(g) - 1)]); print(f"control (non-animated) mean_frame_diff={cd:5.2f}")
