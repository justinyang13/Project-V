"""Shift the store's green/orange stripes away from a real brand look (video copy only; the Project-I original is untouched).
green -> deep teal, orange (sign band only) -> golden amber. Run from the video folder:
../.venv/bin/python jobs/<id>/recolor_stripes.py <original.png> input/<id>.png"""
import sys, cv2, numpy as np
src, dst = sys.argv[1], sys.argv[2]
im = cv2.imread(src); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32); H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
store = np.zeros(im.shape[:2], np.uint8); cv2.rectangle(store, (2050, 100), (3840, 1400), 255, -1)
band = np.zeros(im.shape[:2], np.uint8); cv2.fillPoly(band, [np.array([(2100, 590), (3840, 140), (3840, 460), (2100, 860)], np.int32)], 255)
def soft(x, lo, hi, w): return np.clip((x - lo + w) / w, 0, 1) * np.clip((hi + w - x) / w, 0, 1)
g = soft(H, 42, 92, 6) * np.clip((S - 50) / 40, 0, 1) * (store / 255)          # green stripes and the green line under the windows
o = soft(H, 4, 17, 3) * np.clip((S - 110) / 40, 0, 1) * (band / 255)           # orange stripes, sign band only
g = cv2.GaussianBlur(g, (0, 0), 1.0); o = cv2.GaussianBlur(o, (0, 0), 1.0)
H2 = H + g * (97 - H) * 0.9 + o * (23 - H) * 0.9                              # OpenCV hue 0-180: 97 = teal, 23 = amber
S2 = S * (1 - 0.12 * g); V2 = V * (1 - 0.10 * g)                              # teal a touch softer/darker so it sits in the dusk
out = cv2.cvtColor(np.dstack([H2, S2, V2]).clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
cv2.imwrite(dst, out); print("recolored", int((g > 0.5).sum()), "green px,", int((o > 0.5).sum()), "orange px ->", dst)
