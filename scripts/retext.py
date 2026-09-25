"""Replace unreadable / unknown text in a generated image with known, generic words (signs, posters) and make the rest illegible.
python ../scripts/retext.py --job Video-Zen4          (reads jobs/<id>/text_fix.json; keeps the untouched picture as input/<id>_original.png, writes input/<id>.png)
Image models invent glyphs that look like Chinese characters but mean nothing (or something unintended). We cannot read them all, so:
  neon   : paint the panel's background over the old glyphs and draw our own text (e.g. 麵 / 咖啡 / 小吃) as neon: bright core + coloured glow. "lines" = rows (horizontal) or one string stacked (vertical).
  carved : (wooden sign) inpaint the dark old glyphs, draw new dark text rotated by "angle" degrees.
  blur   : blur a polygon (menu paper, small notes).
  blur_auto : inside "region" polygons (minus "exclude"), find paper-like pixels (low saturation, not dark wall) and blur them, so posters/stickers keep their colour but nothing can be read.
Coordinates are source pixels of the image."""
import argparse, json, os, shutil
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument("--job", required=True); ap.add_argument("--redo", action="store_true", help="start again from the untouched original")
a = ap.parse_args()
job = json.load(open(f"jobs/{a.job}/job.json")); src = job["source"]; orig = src.replace(".png", "_original.png")
if not os.path.exists(orig): shutil.copy(src, orig)
img = cv2.imread(orig).astype(np.float32); H, W = img.shape[:2]
spec = json.load(open(f"jobs/{a.job}/text_fix.json"))
FONTS = {"heiti": "/System/Library/Fonts/STHeiti Medium.ttc", "songti": "/System/Library/Fonts/Supplemental/Songti.ttc", "latin": "/System/Library/Fonts/Supplemental/Arial Bold.ttf"}
def poly_mask(p, feather=0):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 255)
    return cv2.GaussianBlur(m, (0, 0), feather).astype(np.float32) / 255 if feather else m.astype(np.float32) / 255
def text_mask(w, h, item):
    """render the text of an item into a w x h mask (white on black)"""
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im); path = FONTS[item.get("font", "heiti")]
    lines = item["lines"]; vertical = item.get("vertical", False)
    if vertical:
        chars = list(lines if isinstance(lines, str) else "".join(lines)); cell_h = h / len(chars); size = int(min(w * 0.92, cell_h * 0.86) * item.get("scale", 1.0)); f = ImageFont.truetype(path, size)
        for i, ch in enumerate(chars): d.text((w / 2, (i + 0.5) * cell_h), ch, font=f, fill=255, anchor="mm", stroke_width=item.get("stroke", 0))
    else:
        rows = lines if isinstance(lines, list) else [lines]; cell_h = h / len(rows)
        for i, row in enumerate(rows):
            size = int(min(cell_h * 0.86, w * 0.94 / max(len(row), 1)) * item.get("scale", 1.0)); f = ImageFont.truetype(path, size)
            d.text((w / 2, (i + 0.5) * cell_h), row, font=f, fill=255, anchor="mm", stroke_width=item.get("stroke", 0))
    return np.array(im).astype(np.float32) / 255

def draw_poster(w, h, it):
    """a crisp generic poster (w x h px, BGR float): big word + English word + decoration, or a menu list. styles: bg/fg/accent colours are RGB in the spec"""
    S = 4; W_, H_ = max(w, 48) * S, max(h, 48) * S; bg = tuple(it.get("bg", [235, 225, 200])); fg = tuple(it.get("fg", [30, 25, 20])); ac = tuple(it.get("accent", [190, 40, 40]))
    im = Image.new("RGB", (W_, H_), bg); d = ImageDraw.Draw(im); m = int(min(W_, H_) * 0.06); d.rectangle([m // 2, m // 2, W_ - m // 2, H_ - m // 2], outline=ac, width=max(m // 3, 2))
    cj = FONTS["heiti"]; la = FONTS["latin"]; wide = W_ > H_ * 1.25
    if it.get("style") == "menu":
        f1 = ImageFont.truetype(la, int(H_ * 0.09)); d.text((W_ / 2, H_ * 0.09), it.get("title", "MENU"), font=f1, fill=fg, anchor="mm")
        f2 = ImageFont.truetype(cj, int(H_ * 0.06)); d.text((W_ / 2, H_ * 0.18), it.get("cj", "菜單"), font=f2, fill=ac, anchor="mm")
        rows = it.get("rows", [("NOODLES", "80"), ("TEA", "40"), ("COFFEE", "60"), ("WINE", "120"), ("SNACKS", "50"), ("SOUP", "45")]); f3 = ImageFont.truetype(la, int(H_ * 0.055))
        for i, (a_, b_) in enumerate(rows):
            y = H_ * (0.30 + 0.105 * i); d.text((W_ * 0.14, y), a_, font=f3, fill=fg, anchor="lm"); d.text((W_ * 0.86, y), b_, font=f3, fill=fg, anchor="rm"); d.line([(W_ * 0.14, y + H_ * 0.04), (W_ * 0.86, y + H_ * 0.04)], fill=ac, width=max(S // 2, 1))
    elif wide:
        f1 = ImageFont.truetype(cj, int(H_ * 0.62)); d.text((W_ * 0.27, H_ * 0.5), it.get("cj", "麵"), font=f1, fill=fg, anchor="mm")
        f2 = ImageFont.truetype(la, int(min(H_ * 0.28, W_ * 0.5 / max(len(it.get("en", "NOODLES")), 1) * 1.5))); d.text((W_ * 0.64, H_ * 0.5), it.get("en", "NOODLES"), font=f2, fill=ac, anchor="lm")
    else:
        d.ellipse([W_ * 0.5 - H_ * 0.16, H_ * 0.08, W_ * 0.5 + H_ * 0.16, H_ * 0.08 + H_ * 0.32], fill=ac)
        f1 = ImageFont.truetype(cj, int(min(W_ * 0.62 / max(len(it.get("cj", "麵")), 1), H_ * 0.34))); d.text((W_ / 2, H_ * 0.24), it.get("cj", "麵"), font=f1, fill=fg if it.get("cj_on_circle", False) is False else bg, anchor="mm")
        f2 = ImageFont.truetype(la, int(min(H_ * 0.11, W_ * 0.86 / max(len(it.get("en", "NOODLES")), 1) * 1.6))); d.text((W_ / 2, H_ * 0.62), it.get("en", "NOODLES"), font=f2, fill=fg, anchor="mm")
        for i in range(3): d.rectangle([W_ * 0.2, H_ * (0.74 + 0.07 * i), W_ * (0.8 - 0.12 * (i % 2)), H_ * (0.74 + 0.07 * i + 0.03)], fill=tuple(int(0.55 * c + 0.45 * b) for c, b in zip(fg, bg)))
    arr = np.array(im.resize((max(w, 48), max(h, 48)), Image.LANCZOS)).astype(np.float32)[..., ::-1]         # RGB -> BGR, back to output resolution (antialiased)
    return cv2.GaussianBlur(arr, (0, 0), 0.5)
for it in spec["items"]:
    kind = it["kind"]
    if kind == "neon":
        x0, y0, x1, y1 = it["box"]; w, h = x1 - x0, y1 - y0; roi = img[y0:y1, x0:x1].copy()
        lum = roi.mean(2); dark = roi[lum <= np.percentile(lum, 30)]; bg = np.array(it.get("bg_bgr", np.median(dark, 0)), np.float32)
        yy, xx = np.mgrid[0:h, 0:w]; edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)); wgt = np.clip(edge / 2.5, 0, 1)[..., None]      # inside the frame, soft edge
        new = np.ones_like(roi) * bg
        m = text_mask(w, h, it); col = np.array(it["color_bgr"], np.float32)
        core = cv2.GaussianBlur(m, (0, 0), 0.7); g1 = cv2.GaussianBlur(m, (0, 0), 2.2); g2 = cv2.GaussianBlur(m, (0, 0), 6.5)
        new = new + col * (0.55 * g2 + 0.85 * g1)[..., None] + (col * 0.35 + 255 * 0.65) * core[..., None]
        img[y0:y1, x0:x1] = wgt * np.clip(new, 0, 255) + (1 - wgt) * roi
    elif kind == "carved":
        cx, cy = it["center"]; w, h = it["size"]; ang = it["angle"]
        # inpaint the old dark glyphs inside the board
        bx0, by0, bx1, by1 = it["board_box"]; roi = np.clip(img[by0:by1, bx0:bx1], 0, 255).astype(np.uint8); lum = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        dm = (lum < np.percentile(lum, it.get("dark_pct", 38))).astype(np.uint8) * 255; dm = cv2.dilate(dm, np.ones((5, 5), np.uint8)); pm_ = poly_mask(it["board_poly"], 0)[by0:by1, bx0:bx1]
        dm = (dm * (pm_ > 0.5)).astype(np.uint8); clean = cv2.inpaint(roi, dm, 6, cv2.INPAINT_TELEA); img[by0:by1, bx0:bx1] = np.where(dm[..., None] > 0, clean.astype(np.float32), img[by0:by1, bx0:bx1])
        m = text_mask(w, h, it); M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)                     # angle > 0 = counter-clockwise (rising to the right)
        big = np.zeros((H, W), np.float32); tw = cv2.warpAffine(m, M, (w, h), flags=cv2.INTER_LINEAR)
        x0, y0 = int(cx - w / 2), int(cy - h / 2); big[y0:y0 + h, x0:x0 + w] = tw; big = cv2.GaussianBlur(big, (0, 0), 0.9) * pm_.shape[0] / pm_.shape[0]
        ink = np.array(it.get("ink_bgr", [18, 28, 45]), np.float32); a_ = (big * it.get("alpha", 0.85))[..., None]; img = img * (1 - a_) + ink * a_
    elif kind == "plaque":                                   # wooden sign: flatten the board face (old glyphs -> board colour), draw new dark text
        pm_ = poly_mask(it["poly"], 1.2)[..., None]; inside = poly_mask(it["poly"], 0) > 0.5
        lum = img.mean(2); face = np.median(img[inside & (lum >= np.percentile(lum[inside], 55))], 0)
        flat = img.copy(); flat[inside & (lum < np.percentile(lum[inside], it.get("dark_pct", 60)))] = face
        flat = np.where(inside[..., None], cv2.GaussianBlur(flat, (0, 0), it.get("smooth", 3.0)), flat); img = pm_ * flat + (1 - pm_) * img
        cx, cy = it["center"]; w, h = it["size"]; m = text_mask(w, h, it); M = cv2.getRotationMatrix2D((w / 2, h / 2), it["angle"], 1.0)
        tw = cv2.warpAffine(m, M, (w, h), flags=cv2.INTER_LINEAR); big = np.zeros((H, W), np.float32); x0, y0 = int(cx - w / 2), int(cy - h / 2); big[y0:y0 + h, x0:x0 + w] = tw
        big = cv2.GaussianBlur(big, (0, 0), 0.8); ink = np.array(it.get("ink_bgr", [10, 20, 38]), np.float32); a_ = (big * it.get("alpha", 0.9))[..., None]; img = img * (1 - a_) + ink * a_
    elif kind == "plate":                                    # a new nameplate laid over the old carved text: dark lacquer, thin gold edge, gold text (no guessing at the old board's edges)
        cx, cy = it["center"]; w, h = it["size"]; ang = np.deg2rad(it["angle"]); c, s_ = np.cos(ang), np.sin(ang)
        corners = [(cx + dx * c + dy * s_, cy - dx * s_ + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]   # angle > 0 = rising to the right
        pm_ = poly_mask(corners, 0.8)[..., None]; shadow = cv2.GaussianBlur(poly_mask([(x + 3, y + 4) for x, y in corners], 0), (0, 0), 3)[..., None]
        img = img * (1 - 0.55 * shadow * (1 - pm_))
        edge = pm_ - poly_mask([((x - cx) * 0.94 + cx, (y - cy) * 0.88 + cy) for x, y in corners], 0.8)[..., None]
        img = img * (1 - pm_) + np.array(it.get("fill_bgr", [22, 38, 60]), np.float32) * pm_ ; img = img * (1 - np.clip(edge, 0, 1)) + np.array(it.get("edge_bgr", [70, 150, 205]), np.float32) * np.clip(edge, 0, 1)
        tw_, th_ = int(w * 0.86), int(h * 0.7); m = text_mask(tw_, th_, it); M = cv2.getRotationMatrix2D((tw_ / 2, th_ / 2), it["angle"], 1.0)
        bw, bh = int(tw_ * 1.5), int(th_ * 1.8); mm = np.zeros((bh, bw), np.float32); mm[(bh - th_) // 2:(bh - th_) // 2 + th_, (bw - tw_) // 2:(bw - tw_) // 2 + tw_] = m
        M = cv2.getRotationMatrix2D((bw / 2, bh / 2), it["angle"], 1.0); rot = cv2.warpAffine(mm, M, (bw, bh), flags=cv2.INTER_LINEAR)
        big = np.zeros((H, W), np.float32); x0, y0 = int(cx - bw / 2), int(cy - bh / 2); big[y0:y0 + bh, x0:x0 + bw] = rot; big = cv2.GaussianBlur(big, (0, 0), 0.6)[..., None]
        img = img * (1 - big) + np.array(it.get("text_bgr", [130, 205, 245]), np.float32) * big
    elif kind == "poster":                                   # replace a poster/menu with a crisp generic one, warped into the quad and lit like the wall around it
        q = np.array(it["quad"], np.float32); w_ = int(max(np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[2] - q[3]))); h_ = int(max(np.linalg.norm(q[3] - q[0]), np.linalg.norm(q[2] - q[1])))
        tex = draw_poster(w_, h_, it); Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [tex.shape[1], 0], [tex.shape[1], tex.shape[0]], [0, tex.shape[0]]]), q)
        warped = cv2.warpPerspective(tex, Hm, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        qm = poly_mask([tuple(p) for p in q], 0.8)[..., None]; gray = cv2.GaussianBlur(img.mean(2), (0, 0), it.get("light_sigma", 5)); inside = poly_mask([tuple(p) for p in q], 0) > 0.5
        ref = np.percentile(gray[inside], 65); ratio = np.clip(gray / max(ref, 1), 0.45, 1.35)[..., None] ** it.get("light_gamma", 0.9)
        new = warped * ratio; img = qm * (0.9 * new + 0.1 * img) + (1 - qm) * img
    elif kind == "fill":                                     # flat paper/board colour with the wall's own lighting (covers old text under a new poster)
        pmk = poly_mask(it["poly"], 0.8)[..., None]; gray = cv2.GaussianBlur(img.mean(2), (0, 0), it.get("light_sigma", 5)); inside = poly_mask(it["poly"], 0) > 0.5
        ratio = np.clip(gray / max(np.percentile(gray[inside], 65), 1), 0.45, 1.35)[..., None] ** it.get("light_gamma", 0.9); col = np.array(it["rgb"][::-1], np.float32)
        img = pmk * (0.92 * col * ratio + 0.08 * img) + (1 - pmk) * img
    elif kind == "blur":
        m = poly_mask(it["poly"], 1.5)[..., None]; img = m * cv2.GaussianBlur(img, (0, 0), it.get("sigma", 2.4)) + (1 - m) * img
    elif kind == "blur_auto":
        reg = poly_mask(it["region"], 0);
        for ex in it.get("exclude", []): reg = reg * (1 - poly_mask(ex, 0))
        hsv = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV); s, v = hsv[..., 1], hsv[..., 2]
        paper = ((s < it.get("sat_max", 80)) & (v > it.get("val_min", 45))).astype(np.uint8) * 255
        paper = cv2.morphologyEx(paper, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)); paper = cv2.dilate(paper, np.ones((7, 7), np.uint8)); paper = (paper.astype(np.float32) / 255) * reg
        paper = cv2.GaussianBlur(paper, (0, 0), 1.5)[..., None]; img = paper * cv2.GaussianBlur(img, (0, 0), it.get("sigma", 2.6)) + (1 - paper) * img
        print("blur_auto: blurred", int((paper > 0.5).sum()), "px in", len(it.get("region", [])), "point region")
cv2.imwrite(src, np.clip(img + .5, 0, 255).astype(np.uint8)); print("wrote", src, "(original kept as", orig + ")")
