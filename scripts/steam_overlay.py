"""Procedural steam that rises from a cup, seamless over the loop (adds to the AI's faint steam so the vapour clearly moves).
python ../scripts/steam_overlay.py --job Video-Zen4 --frames work/Video-Zen4/loop_flicker --out work/Video-Zen4/loop_steam [--strength 1.0]
job.json: a region {"role": "steam_src", "origin": [x, y] (rim centre, source px), "height": px, "width": px, "lean": px (drift to the side at the top)}.
Method: a tileable noise texture that scrolls upward by a whole number of tile heights per loop (so frame 0 follows frame 239 exactly), multiplied by a column envelope that is narrow
at the rim, widens with height, sways sideways with a sine that has a whole number of cycles per loop, and fades to nothing at the top. Colour: warm off-white (it catches the lamp light).
Only pixels inside the envelope change; everything else is copied."""
import argparse, glob, json, os
import cv2, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--frames", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--strength", type=float, default=1.0); ap.add_argument("--seed", type=int, default=4)
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); fs = sorted(glob.glob(a.frames + "/f*.png")); P = len(fs)
OW, OH = job["plate"]["output_size"]; cx0, cy0, cx1, cy1 = job["plate"]["crop"]; sc = OW / (cx1 - cx0)
os.makedirs(a.out, exist_ok=True); rng = np.random.default_rng(a.seed)
r = next(v for v in job["regions"].values() if v["role"] == "steam_src")
ox, oy = (r["origin"][0] - cx0) * sc, (r["origin"][1] - cy0) * sc; Ht = r["height"] * sc; Wd = r["width"] * sc; lean = r.get("lean", 0) * sc
# tileable noise (torus): sum of blurred random fields at 3 scales, elongated vertically (wisps)
TH, TW = 512, 256
def field(sig_y, sig_x, amp):
    f = rng.standard_normal((TH, TW)).astype(np.float32); f3 = np.tile(f, (3, 3)); f3 = cv2.GaussianBlur(f3, (0, 0), sigmaX=sig_x, sigmaY=sig_y); f = f3[TH:2 * TH, TW:2 * TW]; return amp * f / f.std()   # blur on a 3x3 tiling = wrap-around
N = field(40, 12, 1.0) + field(18, 6, 0.6) + field(8, 3, 0.35); N = (N - N.min()) / (N.max() - N.min()); N = np.clip((N - 0.30) * 2.2, 0, 1) ** 1.1       # sparse, curly veils
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32); h = (oy - yy) / Ht                                # 0 at the rim, 1 at the top
inside = (h > -0.02) & (h < 1.0)
col = np.array([232, 238, 244], np.float32) * 0.94                                                     # BGR, warm off-white
for t in range(P):
    ph = t / P; sway = np.sin(2 * np.pi * (2 * ph) + h * 4.2) * (0.10 + 0.55 * np.clip(h, 0, 1)) * Wd * 0.5 + lean * np.clip(h, 0, 1) ** 1.6      # 2 sway cycles per loop
    cxh = ox + sway; wh = Wd * (0.22 + 0.9 * np.clip(h, 0, 1))                                          # column widens with height
    env = np.exp(-((xx - cxh) / wh) ** 2 * 1.6) * np.clip(np.sin(np.pi * np.clip(h, 0, 1) ** 0.75), 0, 1) * inside
    u = (xx - cxh) / wh * 0.5 * TW * 0.5 + TW / 2; v = (yy / OH) * 0 + (-h * TH * 0.9) + ph * TH * 2                        # scroll = 2 tile heights per loop (whole number -> seamless)
    tex = cv2.remap(N, np.mod(u, TW).astype(np.float32), np.mod(v, TH).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    al = np.clip(env * tex * 1.15 * a.strength, 0, 0.75)[..., None]
    img = cv2.imread(fs[t]).astype(np.float32); out = img * (1 - al) + col * al
    cv2.imwrite(f"{a.out}/f{t:04d}.png", np.clip(out + .5, 0, 255).astype(np.uint8))
print("wrote", P, "frames to", a.out)
