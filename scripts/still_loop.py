"""Seamless procedural loop from a still (no AI video, so no camera drift): snow everywhere, rare lamp flickers, branch sway, a faint window shimmer.
python ../scripts/still_loop.py --job <id> --out work/<id>/loop60.mp4 [--size 1920 1080] [--only 300 --png f.png] [--seconds 60]     (run from the video folder)
job.json: plate.crop (source px), loop.period_s/fps, "snow" {seed, density, size, strength, slant}, regions:
  role "lamp"    center [x,y], radius [rx,ry], weight (how often it is picked to fill gaps). Only the bright pixels dim (the light, not the pole). Schedule: "flicker" block (below).
  role "pool"    poly, feather_px: warm light on the ground that dims with the lead lamp (only warm-lit pixels).
  role "sway"    poly, root [x,y], reach (px), amp_px (source px at the tips), exclude (poly kept still, e.g. a pole). Displacement grows with distance from the root.
  role "shimmer" poly, amp (0.015 = +-1.5 % slow warm breath).
Snow: depth-sorted layers (work/<id>/depth.npy, 0 = near .. 1 = far); a layer only shows where the scene is farther than it, so far tiny flakes sit over the far street and sky and
near flakes fall in front of everything. Flakes take the colour of the light around them (warm near lamps and the store, blue-grey in the dark). Each flake falls a whole number of
screen heights per loop and wobbles with a whole number of cycles per loop, so the last frame runs into the first exactly. No big blurry flakes (Lessons R-series, rain)."""
import argparse, json, subprocess
import cv2, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--out"); ap.add_argument("--size", type=int, nargs=2, default=None)
ap.add_argument("--only", type=int, default=None); ap.add_argument("--png", default=None); ap.add_argument("--seconds", type=float, default=None)
ap.add_argument("--crf", type=int, default=17); ap.add_argument("--no-snow", action="store_true")
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); cx0, cy0, cx1, cy1 = job["plate"]["crop"]
OW, OH = a.size or job["plate"]["output_size"]; sc = OW / (cx1 - cx0); k1080 = OH / 1080          # k1080: sizes below are given for 1080p
FPS = job["loop"]["fps"]; P = int(round((a.seconds or job["loop"]["period_s"]) * FPS))
src = cv2.imread(job["source"])[cy0:cy1, cx0:cx1]
BASE = cv2.resize(src, (OW, OH), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LANCZOS4).astype(np.float32) / 255
def tp(p): return [(p[0] - cx0) * sc, (p[1] - cy0) * sc]
def pm(pts, feather=0):
    m = np.zeros((OH, OW), np.float32); cv2.fillPoly(m, [np.array([tp(p) for p in pts], np.int32)], 1.0)
    return cv2.GaussianBlur(m, (0, 0), feather * sc) if feather else m
SN = job.get("snow", {}); rng = np.random.default_rng(SN.get("seed", 11)); TT = np.arange(P) / P
LUM = cv2.cvtColor(BASE, cv2.COLOR_BGR2GRAY)

# ---- lamps (v6, user: "depth 30-40 %, 0.3-0.5 s, one of the lamps flickers every 5 s at minimum, the warm light on the sidewalk faints a little every 15 s") ----
# job.json "flicker": {seed, depth [lo,hi], dur_s [lo,hi], max_gap_s, min_gap_s, pool_every_s, lead}: "lead" lamp flickers every pool_every_s and the "pool" regions
# (warm light on the ground) dim with it; the other lamps fill the gaps so a flicker comes at least every max_gap_s. Never two at once.
lamps = [(n, r) for n, r in job["regions"].items() if r["role"] == "lamp"]
# keep the approved snow v5 identical: replay the random draws the v5 lamp code made from the shared rng before the snow was seeded from it
_slots = [n for n, r in lamps for _ in range(int(r.get("dips", 1)))]; rng.shuffle(_slots)
for n, r in lamps:
    for s_ in _slots:
        if s_ == n: rng.uniform(); rng.uniform(); rng.random()
FL = job.get("flicker", {}); rf = np.random.default_rng(FL.get("seed", 23))
def sec(x): return int(round(x * FPS))
every = FL.get("pool_every_s", 15.0); lead = FL.get("lead", lamps[0][0]); gmin, gmax = FL.get("min_gap_s", 2.5), FL.get("max_gap_s", 5.0)
nlead = max(int(round(P / FPS / every)), 1); t0 = rf.uniform(1.0, 4.0); EVENTS = []
for k in range(nlead):
    ts = t0 + k * P / FPS / nlead; seg = P / FPS / nlead; EVENTS.append((ts, lead, True))
    nfill = int(np.ceil(seg / gmax)) + 1                                            # gaps in this segment, each in [gmin, gmax] (+1 so the max is reachable)
    while True:
        g = rf.uniform(gmin, gmax, nfill); g *= seg / g.sum()
        if g.min() >= gmin and g.max() <= gmax: break
    others = [n for n, _ in lamps if n != lead]; wts = np.array([lamps_r.get("weight", 1.0) for n2, lamps_r in lamps if n2 != lead]); last = None
    for gg in np.cumsum(g)[:-1]:
        cand = [o for o in others if o != last]; w = np.array([wts[others.index(o)] for o in cand]); last = cand[rf.choice(len(cand), p=w / w.sum())]
        EVENTS.append((ts + gg, last, False))
dlo, dhi = FL.get("depth", [0.30, 0.40]); ulo, uhi = FL.get("dur_s", [0.3, 0.5])
def dip_shape(nf, double):
    if double:                                                                       # flick, half back up, flick again, recover
        h = nf // 2; return np.concatenate([[0.6], np.ones(max(h - 2, 1)), [0.45], [0.7], np.ones(max(nf - h - 4, 1)), [0.55, 0.2]])
    return np.concatenate([[0.6], np.ones(max(nf - 4, 1)), [0.7, 0.4, 0.15]])        # 1 frame down, hold, softer recovery
CURVES = {n: np.ones(P, np.float32) for n, _ in lamps}; POOL = np.ones(P, np.float32)
for ts, n, is_lead in EVENTS:
    c = sec(ts) % P; dep = rf.uniform(dlo, dhi); sh = dip_shape(sec(rf.uniform(ulo, uhi)), rf.random() < 0.35)
    for j, v in enumerate(sh):
        CURVES[n][(c + j) % P] = min(CURVES[n][(c + j) % P], 1 - dep * v)
        if is_lead: POOL[(c + j) % P] = min(POOL[(c + j) % P], 1 - FL.get("pool_depth", 0.12) * v)
LAMP = []
for n, r in lamps:
    cx, cy = tp(r["center"]); rx, ry = r["radius"][0] * sc, r["radius"][1] * sc
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32); d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    m = np.clip(1.2 - d, 0, 1) ** 1.5 * np.clip((LUM - 0.25) / 0.45, 0, 1)          # radial, and only where it is bright
    LAMP.append((n, m[..., None], CURVES[n]))
warm = np.clip((BASE[..., 2] - BASE[..., 0] - 0.05) / 0.25, 0, 1) * np.clip((LUM - 0.2) / 0.3, 0, 1)   # warm-lit pixels only
for n, r in job["regions"].items():
    if r["role"] == "pool": LAMP.append((n, (pm(r["poly"], r.get("feather_px", 30)) * warm)[..., None], POOL))
if FL.get("mode") != "bad_bulb": print("flickers (s: lamp):", ", ".join(f"{ts % (P / FPS):.1f}: {n}{' +pool' if l else ''}" for ts, n, l in sorted(EVENTS, key=lambda e: e[0] % (P / FPS))))

if FL.get("mode") == "bad_bulb": LAMP = []                                           # v8: the v6 overlay dips are off; only the relit bad bulb flickers

# ---- bad bulb (v8, user: "the flickers are just an overlayed dim... it doesn't look real"): blend towards a real "lamp off" picture ----
# region role "relight": off_image (an image-editor version of a source crop with that lamp switched off), crop_xy (where the crop sits in the source),
# head {center, radius} (the glass, blended to the off picture), r0_px / fall_pow / share (how far and how strongly its light reaches), exclude [ellipses / polys].
# Light only goes down: per-channel ratio off/on of a blurred copy, clipped to <= 1, so the warm light leaves the sign, pole, cap and bushes while the details stay
# the original's; the glass itself is blended straight to the off picture. Timing: a failing bulb, i.e. irregular fast stutter bursts, some ending in a short
# blackout and a warm-up, plus small twitches so that something happens at least every max_gap_s. Filament inertia: off fast, on a little slower.
RELIGHT = []; yy_, xx_ = np.mgrid[0:OH, 0:OW].astype(np.float32)
def ell(c, r):
    m = np.zeros((OH, OW), np.float32); cv2.ellipse(m, tuple(int(v) for v in tp(c)), (int(r[0] * sc), int(r[1] * sc)), 0, 0, 360, 1.0, -1); return m
def bad_bulb_curve(B, rb):
    k = np.zeros(P, np.float32); events = []
    nb = max(int(round(P / FPS / B.get("burst_every_s", 16))), 1); t = rb.uniform(1, 4)
    starts = np.cumsum(rb.uniform(0.7, 1.3, nb)); starts = t + (starts - starts[0]) * (P / FPS - 6) / max(starts[-1] - starts[0], 1e-6) * (nb - 1) / nb if nb > 1 else np.array([t])
    for st in starts:                                                                # stutter burst
        f = sec(st); events.append(st)
        for _ in range(int(rb.integers(4, 10))):
            hi = rb.uniform(0.35, 0.9); n1 = int(rb.integers(1, 5)); lo = rb.uniform(0.05, 0.35); n2 = int(rb.integers(1, 5))   # v9: in-between levels, not on/off
            k[np.arange(f, f + n1) % P] = hi; f += n1; k[np.arange(f, f + n2) % P] = lo; f += n2
        if rb.random() < 0.5:                                                        # short near-blackout, then a slow warm-up with a tiny overshoot
            n = int(rb.integers(6, 15)); k[np.arange(f, f + n) % P] = rb.uniform(0.85, 1.0); f += n
            for v in (0.8, 0.6, 0.45, 0.3, 0.18, 0.08, -0.04, -0.03, -0.01): k[f % P] = v; f += 1
        else:                                                                        # or a brown-out: the light sags and wavers for ~1 s, then recovers
            n = int(rb.integers(14, 30)); w = rb.uniform(0.25, 0.5)
            k[np.arange(f, f + n) % P] = w * (0.8 + 0.2 * np.sin(np.arange(n) * rb.uniform(0.6, 1.2))) * np.sin(np.linspace(0.15, 1, n) * np.pi / 2) ** 0.5; f += n
    gmin, gmax = B.get("twitch_gap_s", [2.5, 5.0]); allev = sorted(events)
    ext = allev + [allev[0] + P / FPS]
    for a0, a1 in zip(ext[:-1], ext[1:]):                                            # twitches between bursts, every gmin..gmax s
        tcur = a0 + rb.uniform(gmin, gmax)
        while tcur < a1 - gmin * 0.8:
            f = sec(tcur); v = rb.uniform(0.2, 0.55); k[f % P] = max(k[f % P], v)
            if rb.random() < 0.4: k[(f + 1) % P] = max(k[(f + 1) % P], v * 0.5)
            if rb.random() < 0.3: k[(f + 3) % P] = max(k[(f + 3) % P], v * 0.8)
            allev.append(tcur); tcur += rb.uniform(gmin, gmax)
    out = k.copy()                                                                   # filament inertia (periodic, two passes): going on is slower than going off
    for _ in range(2):
        for i in range(P):
            prev = out[i - 1]; out[i] = prev + (k[i] - prev) * (0.7 if k[i] > prev else 0.4)   # v9: both ways eased (dims in ~2 frames, recovers in ~3-4)
    return out, sorted(e % (P / FPS) for e in allev)
for n, r in job["regions"].items():
    if r["role"] != "relight": continue
    full = cv2.imread(job["source"]).copy(); off = cv2.imread(r["off_image"]); ox, oy = r["crop_xy"]
    full[oy:oy + off.shape[0], ox:ox + off.shape[1]] = off
    OFF = cv2.resize(full[cy0:cy1, cx0:cx1], (OW, OH), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LANCZOS4).astype(np.float32) / 255
    # v9 (user on v8: "I can still see the overlay... like someone reduced the exposure"): the off picture only really changes the glass, and a ratio map
    # darkened a whole circle. Now the lamp's light is modelled in LINEAR light: its share of each pixel falls off smoothly with distance (1/(1+(d/r0)^2)^p)
    # and only warm-lit pixels carry it (the blue sky and snow in shadow are not lit by the lamp), so the glow and the light on the sign, cap, pole and
    # bushes fade with the bulb, strongest at the lamp and gone by a few hundred px. Removing light in linear space, not scaling sRGB, avoids the exposure look.
    lcx, lcy = tp(r["head"]["center"]); dist = np.hypot(xx_ - lcx, yy_ - lcy)
    fall = 1 / (1 + (dist / (r.get("r0_px", 140) * sc)) ** 2) ** r.get("fall_pow", 1.2)
    Bs = cv2.GaussianBlur(BASE, (0, 0), 2 * sc); wt = np.clip((Bs[..., 2] - Bs[..., 0]) / np.maximum(Bs.sum(2), 1e-3) * 4, 0, 1) ** 0.6   # warm tint 0..1
    share = np.clip(r.get("share", 0.85) * fall * (0.25 + 0.75 * wt), 0, 0.95)
    for e in r.get("exclude", []):
        ex = ell(e["center"], e["radius"]) if "center" in e else pm(e["poly"])
        share *= 1 - cv2.GaussianBlur(ex, (0, 0), 10 * sc)
    share = cv2.GaussianBlur(share, (0, 0), 3 * sc)
    LOSS = (np.power(BASE, 2.2) * share[..., None]).astype(np.float32)                # the lamp's light, linear
    head = cv2.GaussianBlur(ell(r["head"]["center"], r["head"]["radius"]), (0, 0), 3 * sc)
    curve, evs = bad_bulb_curve(r.get("bulb", {}), np.random.default_rng(r.get("seed", 31)))
    ys_, xs_ = np.nonzero(share > 2e-3); bb = (ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1)
    RELIGHT.append((n, bb, LOSS[bb[0]:bb[1], bb[2]:bb[3]], head[bb[0]:bb[1], bb[2]:bb[3], None], OFF[bb[0]:bb[1], bb[2]:bb[3]], curve))
    gaps = np.diff(evs + [evs[0] + P / FPS]); print(f"bad bulb {n}: {len(evs)} events, max gap {gaps.max():.1f} s, first at", ", ".join(f"{e:.1f}" for e in evs[:8]))

# ---- branch sway ----
SWAY = []
for n, r in job["regions"].items():
    if r["role"] != "sway": continue
    m = pm(r["poly"], 6)
    if "exclude" in r: m *= 1 - pm(r["exclude"], 3)
    rx, ry = tp(r["root"]); yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    w = m * np.clip(np.hypot(xx - rx, yy - ry) / (r.get("reach", 600) * sc), 0, 1) ** 1.3
    ys, xs = np.nonzero(w > 1e-3); bb = (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)
    A = r.get("amp_px", 3) * sc
    h = rng.choice([3, 4, 5, 7], 2, replace=False); ph = rng.uniform(0, 6.28, 3)
    SWAY.append((bb, w[bb[0]:bb[1], bb[2]:bb[3]], xx[bb[0]:bb[1], bb[2]:bb[3]], yy[bb[0]:bb[1], bb[2]:bb[3]], A, h, ph))
def sway(img, t):
    for (y0, y1, x0, x1), w, X, Y, A, h, ph in SWAY:
        tt = TT[t]; wave = 2 * np.pi * (X - X.min()) / 900                           # slow travelling wave so the crown does not move as one block
        dx = A * w * (0.65 * np.sin(2 * np.pi * h[0] * tt + ph[0] + wave) + 0.35 * np.sin(2 * np.pi * h[1] * tt + ph[1] + 1.7 * wave))
        dy = 0.25 * A * w * np.sin(2 * np.pi * h[0] * tt + ph[2] + wave)
        img[y0:y1, x0:x1] = cv2.remap(BASE[y0:y1, x0:x1], (X - x0 - dx).astype(np.float32), (Y - y0 - dy).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return img

# ---- window shimmer ----
SHIM = [((pm(r["poly"], 12) * np.clip((LUM - 0.35) / 0.4, 0, 1))[..., None], float(r.get("amp", 0.015)), rng.uniform(0, 6.28)) for r in job["regions"].values() if r["role"] == "shimmer"]

# ---- snow ----
D = cv2.resize(np.load(f"work/{a.job}/depth.npy").astype(np.float32), (OW, OH))
Dr = (np.argsort(np.argsort(D.ravel())).reshape(D.shape) / (D.size - 1)).astype(np.float32); Dr = cv2.GaussianBlur(Dr, (0, 0), 1.5 * k1080)
def vis(z, s=0.05): x = np.clip((Dr - (z - s)) / (2 * s), 0, 1); return x * x * (3 - 2 * x)
dens, size, strength, slant = SN.get("density", 1.0), SN.get("size", 1.0), SN.get("strength", 1.0), SN.get("slant", 0.12)
# v2 (user: "too consistent, more random, more size variation, slower"; v3: v2 was "a bit too slow", speeds x1.4): every flake has its own speed, size, drift, wobble and twinkle, plus a slow gusty wind
# that sways whole bands of flakes. z = layer depth; n = flakes; v = fall speed range px/s @1080p; r = median radius px @1080p; blur px; al = alpha; wob = wobble px
LAYERS = [dict(z=0.22, n=130, v=(63, 133), r=2.1, blur=1.2, al=0.70, wob=16),
          dict(z=0.42, n=330, v=(45, 98), r=1.5, blur=0.8, al=0.75, wob=11),
          dict(z=0.62, n=420, v=(31, 70), r=1.1, blur=0.6, al=0.75, wob=7),
          dict(z=0.80, n=650, v=(21, 49), r=0.8, blur=0.5, al=0.70, wob=5),
          dict(z=0.93, n=800, v=(14, 35), r=0.6, blur=0.4, al=0.60, wob=3)]
Psec = P / FPS; mins = Psec / 60
def cyc(lo, hi, n): return np.maximum(np.round(rng.uniform(lo, hi, n) * mins), 1)      # whole cycles per loop (lo..hi per minute)
GUST = [(cyc(1, 3, 1)[0], rng.uniform(0, 6.28), rng.uniform(250, 500)), (cyc(3, 6, 1)[0], rng.uniform(0, 6.28), rng.uniform(120, 250))]
for L in LAYERS:
    n = L["n"] = max(int(L["n"] * dens), 1)                                          # same flakes at any output size
    L["R"] = np.clip(L["r"] * rng.lognormal(0, 0.55, n), 0.35 * L["r"], min(2.4 * L["r"], 4.5)) * size * k1080
    M = (L["R"].max() + 2.5 * L["wob"] * k1080) * 3 + 60 * k1080; L["M"] = M; Hmin = OH + 2 * M
    v = rng.uniform(*L["v"], n) * k1080 * rng.choice([1.0, 1.0, 1.0, 0.7, 1.35], n)      # a few clearly slower or faster flakes
    L["m"] = np.maximum(np.floor(v * Psec / Hmin), 1)                                 # whole wraps per loop ...
    L["H"] = np.maximum(v * Psec / L["m"], Hmin * rng.uniform(1.0, 1.4, n))            # ... over a per-flake wrap height, so speeds vary freely and still loop
    L["x"] = rng.uniform(-0.2 * OW, 1.1 * OW, n); L["y"] = rng.uniform(0, L["H"]); L["sl"] = slant * rng.uniform(0.3, 1.7, n)
    L["w1"] = L["wob"] * k1080 * rng.uniform(0.3, 1.6, n); L["c1"] = cyc(4, 14, n); L["p1"] = rng.uniform(0, 6.28, n)
    L["w2"] = L["wob"] * k1080 * rng.uniform(0.0, 0.7, n); L["c2"] = cyc(14, 40, n); L["p2"] = rng.uniform(0, 6.28, n)
    L["a"] = rng.uniform(0.3, 1.0, n); L["wh"] = rng.random(n) < SN.get("white_share", 0.22); L["sh"] = rng.random(n) < SN.get("sharp_share", 0.3); L["tw"] = rng.uniform(0.0, 0.35, n); L["c3"] = cyc(6, 24, n); L["p3"] = rng.uniform(0, 6.28, n)
    L["g"] = 1.0 - L["z"] * 0.7; L["V"] = vis(L["z"])                                   # near flakes feel the gusts more
def snow(img, t):
    cov = np.zeros((OH, OW), np.float32); covw = np.zeros((OH, OW), np.float32); tt = TT[t]
    for L in LAYERS:
        buf = {(w, h): np.zeros((OH, OW), np.float32) for w in (0, 1) for h in (0, 1)}  # (white, sharp)
        y = (L["y"] + L["m"] * L["H"] * tt) % L["H"] - L["M"]
        gust = sum(18 * k1080 * np.sin(2 * np.pi * c * tt + ph + y / (wl * k1080)) for c, ph, wl in GUST) * L["g"]
        x = (L["x"] + L["sl"] * (y + L["M"]) + gust + L["w1"] * np.sin(2 * np.pi * L["c1"] * tt + L["p1"]) + L["w2"] * np.sin(2 * np.pi * L["c2"] * tt + L["p2"]))
        al = L["a"] * (1 - L["tw"] * (0.5 + 0.5 * np.sin(2 * np.pi * L["c3"] * tt + L["p3"])))   # tumbling flakes catch the light now and then
        for xi, yi, ri, ai, wi, hi in zip(x, y, L["R"], al, L["wh"], L["sh"]):
            if -10 < xi < OW + 10 and -10 < yi < OH + 10:
                tgt = buf[(int(wi), int(hi))]                                            # v4: ~22 % bright white flakes; v5 ("make some of the snow sharper"): ~30 % crisp, unblurred
                if ri < 1.0: cv2.circle(tgt, (int(round(xi)), int(round(yi))), 1, float(ai * ri), -1, cv2.LINE_AA)
                else: cv2.circle(tgt, (int(round(xi * 4)), int(round(yi * 4))), int(round(ri * 4)), float(ai), -1, cv2.LINE_AA, 2)
        bl = max(L["blur"] * k1080, 0.3); k = L["al"] * strength * L["V"]
        for (w, h), b in buf.items():
            b = cv2.GaussianBlur(b, (0, 0), 0.35 * k1080 if h else bl) * (k * 1.15 if h else k)
            if w: covw += b * np.minimum(1.3, 0.95 / np.maximum(k, 1e-3))
            else: cov += b
    cov = np.clip(cov, 0, 0.9)[..., None]
    small = cv2.resize(img, (OW // 8, OH // 8), interpolation=cv2.INTER_AREA); ill = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3), (OW, OH))
    flake = np.clip(ill * 1.6 + np.array([0.40, 0.36, 0.33], np.float32), 0, 1)       # BGR: scene light plus a cool snow-white base
    img = img + cov * (flake - img)
    white = np.clip(flake * 0.3 + 0.70, 0, 1); covw = np.clip(covw, 0, 0.95)[..., None]  # near-white, with a hint of the light around it
    return img + covw * (white - img)

def frame(t):
    img = sway(BASE.copy(), t) if SWAY else BASE.copy()
    for m, amp, ph in SHIM:
        g = 1 + amp * np.sin(2 * np.pi * 2 * TT[t] + ph); img = img + m * (img * np.array([g * 0.995, g, g * 1.005], np.float32) - img)
    for n, (y0, y1, x0, x1), loss, hm, off, c in RELIGHT:
        k = float(c[t])
        if k != 0:
            sub = img[y0:y1, x0:x1]
            sub = np.power(np.clip(np.power(np.clip(sub, 0, 1), 2.2) - k * loss, 0, 1), 1 / 2.2)   # remove (k < 0: add) the lamp's light in linear space
            if k > 0: sub = sub + k * hm * (off - sub)                                  # the glass itself goes dark like the off picture
            img[y0:y1, x0:x1] = sub
    for n, m, c in LAMP:
        if c[t] < 1: g = c[t]; img = img + m * (img * np.array([g * 1.03, g, g * 0.97], np.float32) - img)   # BGR: a dimmer lamp is a touch redder
    if not a.no_snow: img = snow(img, t)
    return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)

if a.only is not None:
    cv2.imwrite(a.png or f"work/{a.job}/still_f{a.only:04d}.png", frame(a.only)); print("wrote frame", a.only)
else:
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow", "-pix_fmt", "yuv420p", "-g", str(FPS * 10), "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    for t in range(P):
        ff.stdin.write(frame(t).tobytes())
        if t % 120 == 0: print(f"frame {t}/{P}", flush=True)
    ff.stdin.close(); ff.wait(); print("wrote", P, "frames to", a.out)
