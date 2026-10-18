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
import argparse, json, os, subprocess
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
if FL.get("mode") not in ("bad_bulb", "relight_all", "off"): print("flickers (s: lamp):", ", ".join(f"{ts % (P / FPS):.1f}: {n}{' +pool' if l else ''}" for ts, n, l in sorted(EVENTS, key=lambda e: e[0] % (P / FPS))))

if FL.get("mode") in ("bad_bulb", "relight_all", "off"): LAMP = []                  # the v6 overlay dips are off ("off" = no lamp flicker at all)

# ---- v10: every lamp relit in place (user on v9 at the final review: "the overlay is not exact to the lamp so the no-light effect looks like a
# square box around the lamp... also the ground area lit by the lamp... create the no-lamp effect for each lamp; only one lamp flickers, that was wrong").
# v9 pasted an AI "lamp off" picture inside an ellipse; the AI had redrawn the lantern bigger and repainted the bushes, so a whole patch changed.
# Now nothing is pasted. Per lamp (region role "lamp"):
#   glass  = the lamp's own bright warm pixels inside its ellipse (exact shape, from the original); off = the same pixels at 3 % light plus a cool ambient;
#   glow   = its share of nearby light, 1/(1+(d/r0)^2)^1.2 x warm tint (the approved v9 falloff), removed in linear light;
#   ground = optional "pool" {poly, share}: the warm light it throws on the ground, = warm-light map x a heavily feathered polygon, removed in linear light.
# Timing: one global timeline of failing-bulb events (twitches, stutter bursts, near-blackouts with a warm-up, brown-outs), an event every 2.2-4.6 s,
# each given to a lamp by weight (never the same lamp twice in a row, never two at once). Filament inertia as v9.
RELIGHT = []; yy_, xx_ = np.mgrid[0:OH, 0:OW].astype(np.float32)
def ell(c, r):
    m = np.zeros((OH, OW), np.float32); cv2.ellipse(m, tuple(int(v) for v in tp(c)), (int(r[0] * sc), int(r[1] * sc)), 0, 0, 360, 1.0, -1); return m
def bulb_events(rb, names, wts):
    Psec = P / FPS; t = rb.uniform(0.5, 3.0); evs = []; last = None; had_burst = set()
    while True:
        cand = [i for i in range(len(names)) if names[i] != last]; w = np.array([wts[i] for i in cand]); i = cand[rb.choice(len(cand), p=w / w.sum())]
        need = [j for j in cand if names[j] not in had_burst]                                # v12: every lamp must go properly dark at least once per loop
        if need and rb.random() < 0.55: i = need[int(rb.integers(len(need)))]
        kind = rb.choice(["twitch", "burst_black", "burst_brown"], p=[0.62, 0.2, 0.18])
        if names[i] not in had_burst and (kind == "twitch" and rb.random() < 0.7): kind = rb.choice(["burst_black", "burst_brown"])
        if kind != "twitch": had_burst.add(names[i])
        f = sec(t); k = {}
        if kind == "twitch":
            v = rb.uniform(0.25, 0.6); k[f] = v
            if rb.random() < 0.4: k[f + 1] = v * 0.5
            if rb.random() < 0.3: k[f + 3] = v * 0.8
        else:
            for _ in range(int(rb.integers(4, 10))):
                hi = rb.uniform(0.35, 0.9); n1 = int(rb.integers(1, 5)); lo = rb.uniform(0.05, 0.35); n2 = int(rb.integers(1, 5))
                for j in range(n1): k[f + j] = hi
                f += n1
                for j in range(n2): k[f + j] = lo
                f += n2
            if kind == "burst_black":
                n = int(rb.integers(6, 15))
                for j in range(n): k[f + j] = rb.uniform(0.85, 1.0)
                f += n
                for v in (0.8, 0.6, 0.45, 0.3, 0.18, 0.08, -0.04, -0.03, -0.01): k[f] = v; f += 1
            else:
                n = int(rb.integers(14, 30)); w0 = rb.uniform(0.25, 0.5); ph = rb.uniform(0.6, 1.2)
                for j in range(n): k[f + j] = w0 * (0.8 + 0.2 * np.sin(j * ph)) * np.sin((0.15 + 0.85 * j / max(n - 1, 1)) * np.pi / 2) ** 0.5
                f += n
        end_s = (max(k) + 1) / FPS
        if evs and evs[0][0] + Psec - end_s < 1.5: break                                 # would run into the first event after the wrap
        evs.append((t, names[i], kind, k)); last = names[i]
        t = end_s + rb.uniform(1.2, 2.6)
        if t > Psec - 0.5: break
    wrap = evs[0][0] + Psec - (max(evs[-1][3]) + 1) / FPS
    if wrap > 4.6:                                                                      # keep "something at least every ~5 s" across the loop point
        tm = (max(evs[-1][3]) + 1) / FPS + wrap / 2; cand = [n for n in names if n not in (evs[-1][1], evs[0][1])] or names
        evs.append((tm, cand[0], "twitch", {sec(tm): rb.uniform(0.3, 0.55)}))
    return evs
if FL.get("mode") == "relight_all":
    LIN = np.power(BASE, 2.2); Bs = cv2.GaussianBlur(BASE, (0, 0), 2 * sc)
    wt = np.clip((Bs[..., 2] - Bs[..., 0]) / np.maximum(Bs.sum(2), 1e-3) * 4, 0, 1) ** 0.6       # warm tint (glow share)
    Bg = cv2.GaussianBlur(BASE, (0, 0), 4 * sc); Lg = Bg.mean(2)
    WARM = np.clip((Bg[..., 2] - Bg[..., 0]) / np.maximum(Bg.sum(2), 1e-3) * 4, 0, 1) * np.clip((Lg - 0.12) / 0.4, 0, 1)   # warm-lit ground
    EXCL = np.ones((OH, OW), np.float32)
    for e in FL.get("exclude", []): EXCL *= 1 - cv2.GaussianBlur(ell(e["center"], e["radius"]) if "center" in e else pm(e["poly"]), (0, 0), 8 * sc)
    names = [n for n, _ in lamps]; wts = [r.get("weight", 1.0) for _, r in lamps]
    EVS = bulb_events(np.random.default_rng(FL.get("seed", 31)), names, wts)
    raw = {n: np.zeros(P, np.float32) for n in names}
    for t0, n, kind, k in EVS:
        for f, v in k.items(): raw[n][f % P] = v if abs(v) > abs(raw[n][f % P]) else raw[n][f % P]
    LUMB = cv2.cvtColor(BASE, cv2.COLOR_BGR2GRAY)
    LDIR = f"jobs/{a.job}/lampoff"; LOFF = json.load(open(f"{LDIR}/lampoff.json")) if os.path.exists(f"{LDIR}/lampoff.json") else {}
    SRC0 = cv2.imread(job["source"])
    for n, r in lamps:
        c = raw[n].copy()
        for _ in range(2):
            for i in range(P): prev = c[i - 1]; c[i] = prev + (raw[n][i] - prev) * (0.7 if raw[n][i] > prev else 0.4)
        c[np.abs(c) < 0.004] = 0                                                         # settled = exactly the original picture
        cx, cy = tp(r["center"]); dist = np.hypot(xx_ - cx, yy_ - cy); reg = ell(r["center"], r["radius"])
        lmax = np.percentile(LUMB[reg > 0], 99.5)
        glass = ((LUMB > r.get("glass_thr", 0.55) * lmax) & (reg > 0) & (wt > 0.15)).astype(np.uint8)
        glass = cv2.morphologyEx(glass, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(int(5 * sc), 3),) * 2))
        glass = cv2.GaussianBlur(glass.astype(np.float32), (0, 0), max(1.0 * sc, 0.6))
        r0 = r.get("glow_r0", r["radius"][0] * 1.2) * sc
        share = r.get("glow_share", 0.8) / (1 + (dist / r0) ** 2) ** 1.2 * (0.05 + 0.95 * wt)   # v11: the sky around a lamp is hardly lit by it
        if "pool" in r: share = share + r["pool"].get("share", 0.6) * cv2.GaussianBlur(pm(r["pool"]["poly"]), (0, 0), r["pool"].get("feather_px", 80) * sc) * WARM
        others = sum(ell(r2["center"], [v * 1.3 for v in r2["radius"]]) for n2, r2 in lamps if n2 != n)
        share = share * (1 - cv2.GaussianBlur(np.clip(others, 0, 1), (0, 0), 6 * sc))           # a lamp never dims another lamp
        share = np.clip(share * EXCL, 0, 0.95); share[glass > 0.5] = np.maximum(share[glass > 0.5], 0.6)
        m = (share > 2e-3) | (glass > 1e-3); ys_, xs_ = np.nonzero(m); bb = (ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1)
        sl = (slice(bb[0], bb[1]), slice(bb[2], bb[3]))
        # v12 (user on v11: "big: the overlay is not matching the lamp, the left side has extras; middle: the overlay extends to the right of the lamp; 3 and 4
        # don't look like a lamp"): no AI pixels at all. The unlit lantern is built from the lamp's OWN pixels: panes (bright warm, inside the traced outline
        # "body_poly" if given, else the lamp ellipse) become dark cool glass with a faint unlit bulb; the frame, bars, snow and cap stay the original's pixels
        # (dimmed where the lamp lit them). The outline can therefore never be off: it is the original's own luminance edge.
        PM = cv2.GaussianBlur(pm(r["body_poly"]), (0, 0), 0.8 * sc) if "body_poly" in r else cv2.GaussianBlur(ell(r["center"], [v * 1.15 for v in r["radius"]]), (0, 0), 1.0 * sc)
        t_ = LUMB / max(lmax, 1e-3); thr = r.get("glass_thr", 0.55)
        pane = np.clip((t_ - thr) / 0.25, 0, 1) ** 1.0 * np.clip((wt - 0.1) / 0.2, 0, 1) * PM
        pane = cv2.GaussianBlur(pane, (0, 0), max(0.6 * sc, 0.5)); pane = np.clip(pane * 1.15, 0, 1)
        kk, lab_, st_, cen_ = cv2.connectedComponentsWithStats((pane > 0.3).astype(np.uint8))   # only the lamp's own pane cluster, never a neighbouring light
        if kk > 1:
            lcx, lcy = tp(r["center"]); main_ = 1 + int(np.argmin([np.hypot(*(cen_[i] - (lcx, lcy))) - 0.02 * st_[i, 4] for i in range(1, kk)]))
            own = cv2.dilate((lab_ == main_).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * max(int(round(3 * sc)), 2) + 1,) * 2)).astype(np.float32)
            pane = pane * own
        py_, px_ = np.nonzero(pane > 0.5)
        if len(py_) < 4: py_, px_ = np.nonzero(reg > 0.5)
        gx0, gx1, gy0, gy1 = px_.min(), px_.max(), py_.min(), py_.max(); gw, gh = max(gx1 - gx0, 2), max(gy1 - gy0, 2)
        yv = np.clip((yy_ - gy0) / gh, 0, 1)[..., None]
        top = np.array(r.get("glass_top", [0.024, 0.017, 0.010]), np.float32); bot = np.array(r.get("glass_bot", [0.006, 0.0045, 0.003]), np.float32)
        glass_col = top * (1 - yv) + bot * yv                                              # BGR linear: the sky reflected in the upper glass, darker below
        bx_, by_ = (gx0 + gx1) / 2, gy0 + 0.42 * gh; rr = np.hypot((xx_ - bx_) / (0.26 * gw), (yy_ - by_) / (0.32 * gh))
        glass_col = glass_col + np.exp(-rr ** 2 * 1.6)[..., None] * np.array(r.get("bulb_lin", [0.032, 0.026, 0.016]), np.float32)   # the unlit bulb, faint
        tint = np.array([1.0, 0.86, 0.62], np.float32)                                      # unlit frame / trim: lamp light gone, cooler
        band = cv2.dilate((pane > 0.3).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * max(int(round(r.get("frame_px", 5) * sc)), 2) + 1,) * 2)).astype(np.float32)
        band = cv2.GaussianBlur(band, (0, 0), max(0.7 * sc, 0.5)) * PM                      # panes + a thin band of lit frame/trim around them, nothing else
        lit = np.clip((wt[..., None] - 0.1) / 0.25, 0, 1)
        frame = LIN * (1 - lit) + LIN * (0.10 * tint) * lit                                # lit frame/trim -> unlit (10 %), cooler
        offfull = pane[..., None] * glass_col + (1 - pane[..., None]) * frame
        glass = np.clip(np.maximum(pane * 3, band), 0, 1)                                   # blend weight = the lantern body, not a halo or neighbours
        share = np.clip(share, 0, 0.95)
        m = (share > 2e-3) | (glass > 1e-3); ys_, xs_ = np.nonzero(m); bb = (ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1)
        sl = (slice(bb[0], bb[1]), slice(bb[2], bb[3])); off = offfull[sl]
        RELIGHT.append((n, bb, (LIN[sl] * share[sl][..., None]).astype(np.float32), glass[sl][..., None], off.astype(np.float32), c))
    st = sorted(e[0] for e in EVS); gaps = np.diff(st + [st[0] + P / FPS])
    print(f"relight_all: {len(EVS)} events, max gap {gaps.max():.1f} s; per lamp:", {n: sum(1 for e in EVS if e[1] == n) for n in names})
    print("events (s lamp kind):", ", ".join(f"{e[0]:.1f} {e[1].replace('lamp_', '')} {e[2]}" for e in EVS))

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
    for n, (y0, y1, x0, x1), loss, gl, off, c in RELIGHT:
        k = float(c[t])
        if k != 0:
            lin = np.power(np.clip(img[y0:y1, x0:x1], 0, 1), 2.2) - k * loss                 # remove (k < 0: add) the lamp's light in linear space
            if k > 0: lin = lin + k * gl * (off - lin)                                       # its own glass goes dark, exact to the panes
            img[y0:y1, x0:x1] = np.power(np.clip(lin, 0, 1), 1 / 2.2)
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
