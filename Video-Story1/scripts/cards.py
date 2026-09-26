#!/Users/justin/Code/Project-V/.venv/bin/python
"""Render text cards (book words only). Outputs 1920x1080 RGBA overlays to work/cards/ and the end card as an opaque frame.
Fonts: Georgia Italic for tally/quotes (as the book's tally line), Avenir Next Heavy/Demi for the title lockup (cover font); colours from the book's cover meta (#fff1c9 title, #ffcf6a accent)."""
import pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ROOT = pathlib.Path(__file__).resolve().parent.parent; OUT = ROOT / "work/cards"; OUT.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080
GEO = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"; AV = "/System/Library/Fonts/Avenir Next.ttc"
CREAM, GOLD = (255, 241, 201), (255, 207, 106)
def shadow_text(img, xy, text, font, fill, anchor="la", blur=10, off=(0, 4), spacing=0):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.text((xy[0] + off[0], xy[1] + off[1]), text, font=font, fill=(10, 30, 36, 200), anchor=anchor)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(xy, text, font=font, fill=fill + (255,), anchor=anchor)
def card(name, text, size, y):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); f = ImageFont.truetype(GEO, size)
    # soft dark band behind the text so it reads on any picture
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(band); tw = bd.textlength(text, font=f)
    bd.rounded_rectangle((W / 2 - tw / 2 - 60, y - size * 0.95, W / 2 + tw / 2 + 60, y + size * 0.75), radius=40, fill=(14, 38, 46, 120))
    img.alpha_composite(band.filter(ImageFilter.GaussianBlur(24)))
    shadow_text(img, (W / 2, y), text, f, CREAM, anchor="ma"); img.save(OUT / f"{name}.png")
card("tally114", "Days without rain: 114", 72, 915)
card("q_ill_go", "“I’ll go.”", 92, 860)
card("q_nobody", "“I am very sorry, but nobody is here.”", 62, 900)
card("q_so_am_i", "“Because so am I.”", 92, 860)
card("q_we_are_here", "“We are here.”", 110, 850)
# end card: cover palette background, blurred cover behind, sharp art-only cover on the right, title lockup on the left
cover = Image.open(ROOT / "input/refs/cover_front_art.png").convert("RGB")
bg = cover.resize((W, int(W * cover.height / cover.width))).crop((0, 300, W, 300 + H)).filter(ImageFilter.GaussianBlur(40))
bg = Image.blend(bg, Image.new("RGB", (W, H), (16, 44, 54)), 0.62).convert("RGBA")
art = cover.resize((720, 1080), Image.LANCZOS).convert("RGBA")
m = Image.new("L", art.size, 255); md = ImageDraw.Draw(m); md.rectangle((0, 0, 719, 1079), outline=0, width=1)
m = m.filter(ImageFilter.GaussianBlur(1))
edge = Image.new("L", art.size, 0); ImageDraw.Draw(edge).rectangle((34, 0, 685, 1079), fill=255); art.putalpha(edge.filter(ImageFilter.GaussianBlur(28)))
bg.alpha_composite(art, (1100, 0))
kick = ImageFont.truetype(AV, 34, index=8); title = ImageFont.truetype(AV, 100, index=8); tag = ImageFont.truetype(GEO, 46)
x = 120
shadow_text(bg, (x, 250), "ONE DRY SPRING, ONE SHY DRAGON AND", kick, GOLD, blur=4)
shadow_text(bg, (x, 296), "ONE VERY SMALL VOICE", kick, GOLD, blur=4)
for i, line in enumerate(["MEI AND THE", "DRAGON WHO", "FEARED THUNDER"]):
    shadow_text(bg, (x, 400 + i * 118), line, title, CREAM, blur=12, off=(0, 6))
shadow_text(bg, (x, 830), "Some voices shake. Use them anyway.", tag, CREAM, blur=6)
bg.convert("RGB").save(OUT / "endcard.png")
print(sorted(p.name for p in OUT.iterdir()))
