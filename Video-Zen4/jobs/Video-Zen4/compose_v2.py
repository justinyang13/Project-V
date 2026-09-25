"""Video-Zen4 picture v2 (run from the video folder): 1) remove the foreground table (paving patch), 2) put the coffee cup + a folded newspaper on the main shop's bar,
3) replace the bay window (sea) with the cliff-and-houses backdrop. Base = input/Video-Zen4_sea.png (sign fixes applied). Writes input/Video-Zen4.png.
python jobs/Video-Zen4/compose_v2.py [--floor work/v2/floor_t2i_s4.png] [--cliff work/v2/cliff_t2i_s1.png] [--cliff_crop 190 15 770 335] [--out input/Video-Zen4.png]"""
import argparse, json
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument("--floor", default="work/v2/floor_t2i_s4.png"); ap.add_argument("--cliff", default="work/v2/cliff_t2i_s3.png")
ap.add_argument("--cliff_crop", type=int, nargs=4, default=[570, 100, 1150, 454]); ap.add_argument("--out", default="input/Video-Zen4.png"); ap.add_argument("--cup_scale", type=float, default=0.27)
a = ap.parse_args()
base = cv2.imread("input/Video-Zen4_sea.png").astype(np.float32); H, W = base.shape[:2]; orig = base.copy()
def pmask(poly, feather=0):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array(poly, np.int32)], 255)
    return (cv2.GaussianBlur(m, (0, 0), feather) if feather else m).astype(np.float32)[..., None] / 255
def match(patch, mask_bool, ring_bool, k=0.85):
    out = patch.copy()
    for c in range(3):
        mo, so = base[..., c][ring_bool].mean(), base[..., c][ring_bool].std() + 1e-3; mn, sn = patch[..., c][mask_bool].mean(), patch[..., c][mask_bool].std() + 1e-3
        out[..., c] = np.where(mask_bool, k * ((patch[..., c] - mn) * min(so / sn, 1.3) + mo) + (1 - k) * patch[..., c], patch[..., c])
    return out
# 1) table -> paving
table = [[1188, 912], [1240, 898], [1500, 838], [1700, 808], [1920, 795], [1920, 1088], [1196, 1088]]
box = (1150, 742, 1920, 1088); fl = cv2.resize(cv2.imread(a.floor).astype(np.float32), (box[2] - box[0], box[3] - box[1]), interpolation=cv2.INTER_AREA)
patch = base.copy(); patch[box[1]:box[3], box[0]:box[2]] = fl
m0 = pmask(table)[..., 0] > 0.5; ring = (cv2.dilate(m0.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0) & ~(cv2.dilate(m0.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & (np.arange(H)[:, None] > 850)
patch = match(patch, m0, ring, 0.85); w = pmask(table, 4); base = w * patch + (1 - w) * base
# 1b) remove the old steam wisp painted above the old cup (smoky, low-saturation pixels on the teal wall / door)
hsv = cv2.cvtColor(np.clip(base, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV); bx = np.zeros((H, W), bool); bx[745:860, 1425:1530] = True
smoke = (hsv[..., 1] < 95) & (hsv[..., 2] > 85) & bx; smoke = cv2.dilate(smoke.astype(np.uint8) * 255, np.ones((9, 9), np.uint8))
clean = cv2.inpaint(np.clip(base, 0, 255).astype(np.uint8), smoke, 7, cv2.INPAINT_TELEA).astype(np.float32); wsm = cv2.GaussianBlur(smoke, (0, 0), 2).astype(np.float32)[..., None] / 255; base = wsm * clean + (1 - wsm) * base
# 2) cup on the bar (cutout from the original picture) + shadow + newspaper
cup = cv2.imread("work/v2/cup_rgba.png", cv2.IMREAD_UNCHANGED).astype(np.float32); s = a.cup_scale
cup = cv2.resize(cup, (int(cup.shape[1] * s), int(cup.shape[0] * s)), interpolation=cv2.INTER_AREA); ch, cw = cup.shape[:2]
cx, cy = 1332, 610                                             # saucer centre on the counter top
x0, y0 = int(cx - cw * 0.5), int(cy - ch * 0.72)
sh = np.zeros((H, W), np.float32); cv2.ellipse(sh, (cx + 3, cy + 5), (int(cw * 0.5), int(cw * 0.14)), -8, 0, 360, 1.0, -1, cv2.LINE_AA); sh = cv2.GaussianBlur(sh, (0, 0), 2.5)[..., None]
base = base * (1 - 0.55 * sh)
al = cup[..., 3:4] / 255; rgb = cup[..., :3] * np.array([0.88, 0.93, 1.0], np.float32) * 0.90 + np.array([6, 8, 14], np.float32)   # a touch warmer/darker: the bar is lit by amber lamps
base[y0:y0 + ch, x0:x0 + cw] = al * rgb + (1 - al) * base[y0:y0 + ch, x0:x0 + cw]
# newspaper: folded, lying along the counter, generic masthead (日報 = daily paper) and grey text bars (no readable words)
S = 6; tw_, th_ = 90, 50; im = Image.new("RGB", (tw_ * S, th_ * S), (214, 208, 190)); d = ImageDraw.Draw(im); F = "/System/Library/Fonts/STHeiti Medium.ttc"
d.text((tw_ * S / 2, th_ * S * 0.16), "日報", font=ImageFont.truetype(F, int(th_ * S * 0.24)), fill=(35, 32, 30), anchor="mm"); d.line([(tw_ * S * 0.06, th_ * S * 0.29), (tw_ * S * 0.94, th_ * S * 0.29)], fill=(60, 55, 50), width=S)
for col in range(3):
    x = tw_ * S * (0.07 + 0.31 * col); d.rectangle([x, th_ * S * 0.36, x + tw_ * S * 0.27, th_ * S * 0.55], fill=(150, 145, 135))
    for r in range(6): d.rectangle([x, th_ * S * (0.60 + 0.06 * r), x + tw_ * S * (0.27 - 0.03 * (r % 3)), th_ * S * (0.60 + 0.06 * r + 0.022)], fill=(120, 116, 108))
d.line([(tw_ * S / 2, 0), (tw_ * S / 2, th_ * S)], fill=(170, 165, 150), width=S // 2)                    # centre fold
tex = np.array(im.resize((tw_ * 2, th_ * 2), Image.LANCZOS)).astype(np.float32)[..., ::-1]
q = np.float32([[1226, 586], [1294, 570], [1312, 588], [1242, 606]]); Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [tex.shape[1], 0], [tex.shape[1], tex.shape[0]], [0, tex.shape[0]]]), q)
warped = cv2.warpPerspective(tex, Hm, (W, H), flags=cv2.INTER_CUBIC); qm = pmask(q.tolist(), 0.7)
shq = cv2.GaussianBlur(pmask((q + np.float32([3, 4])).tolist(), 0)[..., 0], (0, 0), 2)[..., None]; base = base * (1 - 0.45 * shq * (1 - qm))
paper = warped * np.array([0.82, 0.90, 1.0], np.float32) * 0.80; base = qm * paper + (1 - qm) * base
cv2.imwrite("work/v2/base_no_bg.png", np.clip(base + .5, 0, 255).astype(np.uint8))
# 3) bay window -> cliff backdrop
sp = json.load(open("jobs/Video-Zen4/bg_window.json")); x0w, y0w, x1w, y1w = sp["window"]
cl = cv2.imread(a.cliff); cx0, cy0, cx1, cy1 = a.cliff_crop; cand = cv2.resize(cl[cy0:cy1, cx0:cx1].astype(np.float32), (x1w - x0w, y1w - y0w), interpolation=cv2.INTER_AREA)
mb = np.zeros((H, W), np.uint8)
for p in sp["polys"]: cv2.fillPoly(mb, [np.array(p, np.int32)], 255)
for p in sp.get('protect', []) and [sp['protect']]: cv2.fillPoly(mb, [np.array(p, np.int32)], 0)
patch = base.copy(); patch[y0w:y1w, x0w:x1w] = cand; inside = mb > 0
ringb = (cv2.dilate(mb, np.ones((49, 49), np.uint8)) > 0) & (cv2.dilate(mb, np.ones((5, 5), np.uint8)) == 0)
patch = match(patch, inside, ringb, 0.55); w = cv2.GaussianBlur(mb, (0, 0), 5).astype(np.float32)[..., None] / 255; base = w * patch + (1 - w) * base
cv2.imwrite(a.out, np.clip(base + .5, 0, 255).astype(np.uint8)); print("wrote", a.out)
