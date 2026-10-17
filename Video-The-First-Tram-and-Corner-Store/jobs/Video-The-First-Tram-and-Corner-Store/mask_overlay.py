"""Motion overlay for approval 2 (lamps are ellipses, so mask_preview.py does not fit). Run from the video folder:
../.venv/bin/python jobs/<id>/mask_overlay.py <id>  -> jobs/<id>/mask_overlay_v0.png"""
import sys, cv2, json, numpy as np
ID = sys.argv[1]; job = json.load(open(f"jobs/{ID}/job.json")); cx0, cy0, cx1, cy1 = job["plate"]["crop"]; OW, OH = 1920, 1080; sc = OW / (cx1 - cx0)
im = cv2.resize(cv2.imread(job["source"])[cy0:cy1, cx0:cx1], (OW, OH), interpolation=cv2.INTER_AREA).astype(np.float32)
tp = lambda p: [int((p[0] - cx0) * sc), int((p[1] - cy0) * sc)]
col = {"lamp": (0, 200, 255), "sway": (80, 255, 80), "shimmer": (255, 120, 255), "lock": (60, 60, 255)}
ov = im * 0.85 + np.array([255, 200, 120]) * 0.15; lay = np.zeros_like(ov)
def shape(img, r, c, th):
    if r["role"] == "lamp": cv2.ellipse(img, tuple(tp(r["center"])), (int(r["radius"][0] * sc), int(r["radius"][1] * sc)), 0, 0, 360, c, th)
    elif th < 0: cv2.fillPoly(img, [np.array([tp(p) for p in r["poly"]], np.int32)], c)
    else: cv2.polylines(img, [np.array([tp(p) for p in r["poly"]], np.int32)], True, c, th)
for r in job["regions"].values():
    shape(lay, r, col[r["role"]], -1)
    if r["role"] == "sway": cv2.fillPoly(lay, [np.array([tp(p) for p in r["exclude"]], np.int32)], (0, 0, 0))
ov = np.where(lay.sum(2, keepdims=True) > 0, ov * 0.55 + lay * 0.45, ov)
for r in job["regions"].values(): shape(ov, r, col[r["role"]], 2)
ov = ov.clip(0, 255).astype(np.uint8)
leg = [("SNOW: whole frame, near and far (light blue tint)", (255, 200, 120)), ("LAMP FLICKER: rare tiny dips", (0, 200, 255)),
       ("BRANCH SWAY: gentle, stronger at the tips", (80, 255, 80)), ("WINDOW SHIMMER: +-1.5 % slow", (255, 120, 255)),
       ("FROZEN: tram, traffic lights, postbox (+ everything else)", (60, 60, 255))]
y0 = OH - 20 - len(leg) * 30; cv2.rectangle(ov, (10, y0 - 10), (720, OH - 10), (0, 0, 0), -1)
for i, (t, c) in enumerate(leg): cv2.putText(ov, t, (20, y0 + 18 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, c, 2, cv2.LINE_AA)
cv2.imwrite(f"jobs/{ID}/mask_overlay_v0.png", ov); print("wrote", f"jobs/{ID}/mask_overlay_v0.png")
