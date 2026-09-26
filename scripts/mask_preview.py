"""Draw the region overlay for a job so masks can be reviewed by eye (stage 2).
python scripts/mask_preview.py --job 001-snow-tea [--zoom x0 y0 x1 y1]   (zoom box in source pixels)
Writes jobs/<job>/mask_overlay_preview.png (+ _zoom.png). Cyan tint = animated, orange outline = lock, yellow/red = qc_only, white = plate crop."""
import argparse, json
from PIL import Image, ImageDraw, ImageFilter, ImageChops
ap = argparse.ArgumentParser(); ap.add_argument("--job", required=True); ap.add_argument("--zoom", type=int, nargs=4)
a = ap.parse_args(); job = json.load(open(f"jobs/{a.job}/job.json"))
src = Image.open(job["source"]).convert("RGB"); W, H = src.size
def poly(p):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon([tuple(q) for q in p], fill=255); return m
anim = Image.new("L", (W, H), 0); R = job["regions"]
for r in R.values():
    if r["role"] == "animated": anim = ImageChops.lighter(anim, poly(r["poly"]))
for r in R.values():
    if r["role"] == "lock": anim = ImageChops.subtract(anim, poly(r["poly"]))
anim = anim.filter(ImageFilter.GaussianBlur(3))
over = Image.composite(Image.blend(src, Image.new("RGB", (W, H), (0, 200, 255)), 0.45), src, anim); d = ImageDraw.Draw(over)
col = {"lock": (255, 128, 0), "qc_only": (255, 255, 0)}
for n, r in R.items():
    if r["role"] in col: d.polygon([tuple(q) for q in r["poly"]], outline=col[r["role"]], width=3)
# procedural-motion jobs (Video-Zen4/6): flicker = magenta outline, steam_src = cyan column, splash = green area / line (ground, top, leaf) or yellow line (rail)
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
for n, r in R.items():
    if r["role"] == "splash":
        if "poly" in r: od.polygon([tuple(q) for q in r["poly"]], fill=(0, 255, 90, 70), outline=(0, 255, 90, 255))
        if "line" in r: od.line([tuple(q) for q in r["line"]], fill=(255, 230, 0, 255), width=max(3, int(r.get("width", 8) / 2)))
    elif r["role"] == "steam_src":
        x, y = r["origin"]; h, w, lean = r["height"], r["width"], r.get("lean", 0)
        od.polygon([(x - w * .2, y), (x + w * .2, y), (x + lean + w * .9, y - h), (x + lean - w * .9, y - h)], fill=(255, 255, 255, 60), outline=(0, 230, 255, 255)); od.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(0, 230, 255, 255))
    elif r["role"] == "flicker": od.polygon([tuple(q) for q in r["poly"]], outline=(255, 0, 220, 255))
over = Image.alpha_composite(over.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(over)
x0, y0, x1, y1 = job["plate"]["crop"]; d.rectangle([x0, y0, x1, y1], outline=(255, 255, 255), width=2)
out = f"jobs/{a.job}/mask_overlay_preview.png"; over.save(out); print("wrote", out)
if a.zoom:
    zx0, zy0, zx1, zy1 = a.zoom; z = over.crop((zx0, zy0, zx1, zy1)); z = z.resize((z.width * 2, z.height * 2)); z.save(out.replace(".png", "_zoom.png")); print("wrote zoom")
