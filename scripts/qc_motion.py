"""Motion metrics per region on a frames dir (1024x576 plate coords). Usage: qc_motion.py <frames_dir>
Regions (from job source coords, scale 0.5999, offset x-10): snow area, steam box, fire box."""
import sys, glob, cv2, numpy as np
fs = sorted(glob.glob(sys.argv[1] + "/f*.png"))
R = {"snow": (200, 12, 575, 330), "steam": (579, 228, 660, 372), "fire": (657, 177, 711, 243)}
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
