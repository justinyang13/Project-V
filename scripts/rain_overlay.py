"""Seamless procedural rain over a finished loop (the AI clips only animate the regions in job.json; this adds rain to the WHOLE frame). v3.
python ../scripts/rain_overlay.py --job Video-Zen4 --frames work/Video-Zen4/loop_flicker --out work/Video-Zen4/loop_rain [--strength 1.0] [--density 1.0] [--seed 7] [--only 60]
Needs work/<job>/depth.npy (0 = near .. 1 = far; Depth Anything V2 Small on the plate, see the runlog).
Look (Lessons R1-R4):
  * a drop is see-through water that catches the light around it: streaks blend towards a heavily blurred copy of the scene (plus a cool ambient), tapered and soft, with a hint of refraction;
  * straight down (no lean); DEPTH: four layers from medium, soft, fast drops to tiny, sharp, slower far drops (no big near drops); a layer is only drawn where the scene behind it is farther
    (so far rain is hidden behind the table, rails and lanterns, and near rain falls in front of everything), and there are enough near/mid drops that rain is visible in every part of the frame;
  * SPLASHES on every surface that gets hit: regions with role "splash" in job.json have a "kind": ground (ring + jumping droplets), top (counter, stools, awning: smaller rings),
    rail (a small flash and two droplets on a "line" polyline, "width" px), leaf (tiny bright hits and a hop on plants); "n" = events per loop. Sizes grow with nearness.
Loops exactly: each streak falls a whole number of screen heights per period and all splash events are scheduled modulo the period.
Writes f0000.png.. in --out (same names as the input); --only N renders just frame N (for tests)."""
import argparse, glob, json, os
import cv2, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--frames", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--strength", type=float, default=1.0); ap.add_argument("--density", type=float, default=1.0, help="multiplies the number of streaks in every layer")
ap.add_argument("--splash", type=float, default=1.0, help="multiplies the number of splashes"); ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--size", type=float, default=1.0, help="scales drop length, width and blur (0.5 = half size)"); ap.add_argument("--light", type=float, default=0.9, help="how much a drop lightens the scene (lower = more transparent, less white)")
ap.add_argument("--slant", type=float, default=0.0, help="horizontal px per vertical px (0 = straight down)"); ap.add_argument("--depth", default=None)
ap.add_argument("--refract", type=float, default=1.6, help="max refraction shift in px"); ap.add_argument("--only", type=int, default=None)
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); fs = sorted(glob.glob(a.frames + "/f*.png")); P = len(fs)
OW, OH = job["plate"]["output_size"]; cx0, cy0, cx1, cy1 = job["plate"]["crop"]; sc = OW / (cx1 - cx0)
rng = np.random.default_rng(a.seed); os.makedirs(a.out, exist_ok=True)
def tp(p): return [(p[0] - cx0) * sc, (p[1] - cy0) * sc]
def pm(pts):
    m = np.zeros((OH, OW), np.uint8); cv2.fillPoly(m, [np.array([tp(p) for p in pts], np.int32)], 255); return m
def lm(line, w):
    m = np.zeros((OH, OW), np.uint8); cv2.polylines(m, [np.array([tp(p) for p in line], np.int32)], False, 255, int(w * sc)); return m
cupm = np.zeros((OH, OW), np.uint8)
for n, r in job["regions"].items():
    if n.startswith("lock_cup"): cupm = np.maximum(cupm, pm(r["poly"]))
# depth: rank-normalised map (0 = nearest pixel .. 1 = farthest) so every layer has a real share of the picture
D = np.load(a.depth or f"work/{a.job}/depth.npy").astype(np.float32); D = cv2.resize(D, (OW, OH), interpolation=cv2.INTER_LINEAR)
Drank = (np.argsort(np.argsort(D.ravel())).reshape(D.shape) / (D.size - 1)).astype(np.float32); Drank = cv2.GaussianBlur(Drank, (0, 0), 1.5)
def vis(z, soft=0.05): x = np.clip((Drank - (z - soft)) / (2 * soft), 0, 1); return x * x * (3 - 2 * x)     # 1 where the scene is farther than the layer -> the streak is in front of it
# four depth layers, near -> far (the two biggest, out-of-focus near layers were removed after the Video-Zen4 review: too distracting). z = depth of the layer; n = streaks; ms = whole screens fallen per period (nearer = faster); L, w, blur in px (nearer = bigger, more out of focus); al = alpha
LAYERS = [dict(z=0.28, n=150, ms=[11, 12],     L=92,  w=3.8,  blur=2.0, al=0.46),
          dict(z=0.50, n=170, ms=[8, 9],       L=58,  w=2.3,  blur=1.2, al=0.50),
          dict(z=0.74, n=190, ms=[6, 7],       L=36,  w=1.4,  blur=0.7, al=0.50),
          dict(z=0.90, n=220, ms=[4, 5],       L=22,  w=1.0,  blur=0.5, al=0.45)]
for ly in LAYERS:
    ly["L"] *= a.size; ly["w"] *= a.size; ly["blur"] *= a.size; ly["al"] *= min(1.0, ly["w"])            # sub-pixel width: keep the line 1 px but fainter
    ly["n"] = max(int(ly["n"] * a.density), 1)
    ly["x"] = rng.uniform(-250, OW + 250, ly["n"]); ly["y"] = rng.uniform(0, OH + ly["L"] * 1.3, ly["n"])
    ly["m"] = rng.choice(ly["ms"], ly["n"]); ly["k"] = rng.uniform(0.35, 1.0, ly["n"]); ly["Ls"] = ly["L"] * rng.uniform(0.7, 1.3, ly["n"]); ly["V"] = vis(ly["z"])
K = 6; TAPER = np.sin(np.linspace(0.05, 0.95, K) * np.pi) ** 0.8          # brightness along a streak: soft tail, soft head
# splash events: (start frame, x, y, life, amp, kind, vx1, vx2, vy)
EV = []
for name, r in job["regions"].items():
    if r["role"] != "splash": continue
    m = lm(r["line"], r.get("width", 9)) if "line" in r else pm(r["poly"])
    if r.get("kind") in ("ground", "top"): m = cv2.subtract(m, cv2.dilate(cupm, np.ones((5, 5), np.uint8)))
    ys, xs = np.nonzero(m)
    if len(ys) == 0: continue
    for _ in range(int(r.get("n", 40) * a.splash)):
        i = int(rng.integers(0, len(ys))); x, y = int(xs[i]), int(ys[i]); near = 1.5 - 1.0 * float(Drank[y, x])
        EV.append((int(rng.integers(0, P)), x, y, float(rng.uniform(9, 16)), float(rng.uniform(0.55, 1.0)) * near, r.get("kind", "ground"), float(rng.uniform(-1.3, -0.3)), float(rng.uniform(0.3, 1.3)), float(rng.uniform(2.4, 4.2))))
def draw_splashes(spl, t):
    for st, x, y, life, amp, kind, vx1, vx2, vy in EV:
        age = (t - st) % P
        if age >= life: continue
        k = age / life; sz = 0.6 + 0.9 * amp
        if kind in ("ground", "top"):
            r = (2 + 8 * k) * sz * (0.55 if kind == "top" else 1.0)
            cv2.ellipse(spl, (x, y), (max(int(r), 1), max(int(r * 0.32), 1)), 0, 0, 360, float(amp * 0.95 * (1 - k) ** 1.5), 2 if sz > 1.1 else 1, cv2.LINE_AA)
            if age < 9:                                                       # crown droplets: two small parabolas
                for vx in (vx1, vx2):
                    px = x + vx * age * sz; py = y - (vy * age - 0.42 * age * age) * sz
                    cv2.circle(spl, (int(px), int(py)), 2 if sz > 1.1 else 1, float(amp * (1 - age / 9)), -1, cv2.LINE_AA)
        elif kind == "rail":
            if age < 5: cv2.circle(spl, (x, y), 3 if sz > 1.1 else 2, float(amp * (1 - age / 5) * 1.1), -1, cv2.LINE_AA)
            if age < 8:
                for vx in (vx1, vx2): cv2.circle(spl, (int(x + vx * age * 1.4), int(y - (vy * age * 0.7 - 0.3 * age * age))), 1, float(amp * (1 - age / 8)), -1, cv2.LINE_AA)
        else:                                                                 # leaf: a bright hit that hops a little
            if age < 6: cv2.circle(spl, (x, int(y - 2 * np.sin(np.pi * age / 6))), 1, float(amp * (1 - age / 6)), -1, cv2.LINE_AA)
def render(t, img):
    cov = np.zeros((OH, OW), np.float32)
    for ly in LAYERS:
        lay = np.zeros((OH, OW), np.float32); Lmax = ly["L"] * 1.3
        for i in range(ly["n"]):
            v = ly["m"][i] * (OH + Lmax) / P; yy = (ly["y"][i] + v * t) % (OH + Lmax); xx = ly["x"][i] + a.slant * yy
            Ls = ly["Ls"][i]
            for j in range(K):                                              # tapered polyline, tail -> head
                s0, s1 = j / K, (j + 1) / K
                p0 = (int(round(xx - a.slant * Ls * (1 - s0))), int(round(yy - Ls * (1 - s0)))); p1 = (int(round(xx - a.slant * Ls * (1 - s1))), int(round(yy - Ls * (1 - s1))))
                cv2.line(lay, p0, p1, float(ly["k"][i] * TAPER[j]), max(int(round(ly["w"])), 1), cv2.LINE_AA)
        cov += cv2.GaussianBlur(lay, (0, 0), ly["blur"]) * ly["al"] * a.strength * ly["V"]
    spl = np.zeros((OH, OW), np.float32); draw_splashes(spl, t)
    cov += cv2.GaussianBlur(spl, (0, 0), 0.6) * 0.85 * a.strength
    cov = np.clip(cov, 0, 0.8)
    # scene light: heavily blurred frame (computed at 1/8 size) plus a cool ambient, so rain catches the colours around it
    small = cv2.resize(img, (OW // 8, OH // 8), interpolation=cv2.INTER_AREA); ill = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (OW, OH), interpolation=cv2.INTER_LINEAR)
    ill = np.clip(ill * 1.7 + np.array([0.20, 0.16, 0.13], np.float32), 0, 1)          # BGR, cool ambient
    # refraction: push the picture along the gradient of the streaks
    cb = cv2.GaussianBlur(cov, (0, 0), 1.2); gx = cv2.Sobel(cb, cv2.CV_32F, 1, 0, ksize=3) * a.refract * 3; gy = cv2.Sobel(cb, cv2.CV_32F, 0, 1, ksize=3) * a.refract * 3
    mx, my = np.meshgrid(np.arange(OW, dtype=np.float32), np.arange(OH, dtype=np.float32))
    refr = cv2.remap(img, mx + np.clip(gx, -a.refract, a.refract), my + np.clip(gy, -a.refract, a.refract), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    C = cov[..., None]
    return refr + C * np.maximum(ill - refr, 0) * a.light - C * 0.04 * refr, cov     # lighter towards the scene light; a hint of darkening = see-through water
tot = 0.0
for t in ([a.only] if a.only is not None else range(P)):
    img = cv2.imread(fs[t]).astype(np.float32) / 255; out, cov = render(t, img); tot += float(np.abs(out - img).mean())
    cv2.imwrite(f"{a.out}/f{t:04d}.png", np.clip(out * 255 + .5, 0, 255).astype(np.uint8))
print(f"wrote {'frame ' + str(a.only) if a.only is not None else str(P) + ' frames'} to {a.out}; {len(EV)} splash events per loop; mean |change| {tot / (1 if a.only is not None else P) * 255:.2f} / 255")
