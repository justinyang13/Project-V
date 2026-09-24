"""Camera-drift metric: track features between frame 0 and frame i inside the static ROOM area (left shoji + right lamp/shoji),
fit a similarity transform, report scale and translation. Usage: qc_drift.py <frames_dir> [step]"""
import sys, glob, cv2, numpy as np
d = sys.argv[1]; step = int(sys.argv[2]) if len(sys.argv) > 2 else 20
fs = sorted(glob.glob(f"{d}/f*.png")); g0 = cv2.cvtColor(cv2.imread(fs[0]), cv2.COLOR_BGR2GRAY)
H, W = g0.shape
mask = np.zeros_like(g0); mask[:, : int(W*.18)] = 255; mask[:, int(W*.68):] = 255   # room only (shoji left / lamp+shoji right)
orb = cv2.ORB_create(1500); k0, d0 = orb.detectAndCompute(g0, mask)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
print("frame  scale   dx_px   dy_px  inliers")
worst = 0
for i in list(range(step, len(fs), step)) + [len(fs) - 1]:
    g = cv2.cvtColor(cv2.imread(fs[i]), cv2.COLOR_BGR2GRAY); k, dd = orb.detectAndCompute(g, mask)
    m = bf.match(d0, dd)
    if len(m) < 8: print(i, "few matches"); continue
    A, inl = cv2.estimateAffinePartial2D(np.float32([k0[x.queryIdx].pt for x in m]), np.float32([k[x.trainIdx].pt for x in m]), method=cv2.RANSAC, ransacReprojThreshold=3)
    s = float(np.hypot(A[0, 0], A[1, 0])); print(f"{i:5d} {s:7.4f} {A[0,2]:7.1f} {A[1,2]:7.1f} {int(inl.sum()):6d}"); worst = max(worst, abs(s - 1) * W / 2, abs(A[0, 2]), abs(A[1, 2]))
print(f"worst_drift_px ~ {worst:.1f} (edge-equivalent, at width {W}); target <= 0.7")
