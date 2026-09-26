#!/Users/justin/Code/Project-V/.venv/bin/python
"""usage: scripts/sheet.py out.jpg cols thumbW file... -> labelled contact sheet"""
import sys
from PIL import Image, ImageDraw
out, cols, W = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
ims = [Image.open(f).convert("RGB") for f in fs]; H = int(W * ims[0].height / ims[0].width)
rows = (len(fs) + cols - 1) // cols; s = Image.new("RGB", (W * cols, H * rows), "white")
for i, (f, im) in enumerate(zip(fs, ims)):
    im = im.resize((W, H)); ImageDraw.Draw(im).text((6, 6), f.split("/")[-1][:-4], fill="red"); s.paste(im, ((i % cols) * W, (i // cols) * H))
s.save(out, quality=85)
