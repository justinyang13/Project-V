#!/bin/bash
# Stage 1: generate N candidate images for a job with draw-things-cli (headless; the Draw Things app can be closed),
# then a numbered 2x2 contact sheet for the user to pick from.
# Usage: scripts/image_candidates.sh <job> [n=4] [first_seed=11]
# Needs: jobs/<job>/image_prompt.txt and jobs/<job>/image_negative.txt
# Output: work/<job>/candidates/cand<k>_s<seed>.png (1920x1088) + work/<job>/candidates/sheet.png
set -euo pipefail
JOB=$1; N=${2:-4}; SEED0=${3:-11}
OUT=work/$JOB/candidates; mkdir -p "$OUT"
export DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models
for k in $(seq 1 "$N"); do
  S=$((SEED0 + (k - 1) * 11))
  F="$OUT/cand${k}_s${S}.png"
  [ -f "$F" ] && { echo "exists $F"; continue; }
  draw-things-cli generate --model z_image_turbo_1.0_q8p.ckpt --no-download-missing --disable-preview \
    --prompt-file "jobs/$JOB/image_prompt.txt" --negative-prompt-file "jobs/$JOB/image_negative.txt" \
    --width 1920 --height 1088 --seed "$S" -o "$F" 2>&1 | grep -E "Wrote|Total generation time|rror" || true
done
# numbered contact sheet (Pillow; this ffmpeg build has no drawtext)
.venv/bin/python - "$OUT" <<'PY'
import sys, glob, re
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; fs = sorted(glob.glob(f"{out}/cand*_s*.png"), key=lambda f: int(re.search(r"cand(\d+)_", f).group(1)))
tw, th = 960, 544; cols = 2; rows = (len(fs) + 1) // 2
sheet = Image.new("RGB", (tw * cols, th * rows), "black")
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 56)
except Exception: font = ImageFont.load_default()
for k, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((tw, th)); d = ImageDraw.Draw(im)
    n = re.search(r"cand(\d+)_", f).group(1); d.rectangle([0, 0, 90, 76], fill=(0, 0, 0)); d.text((26, 8), n, fill="white", font=font)
    sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
sheet.save(f"{out}/sheet.png"); print("sheet:", f"{out}/sheet.png", len(fs), "images")
PY
