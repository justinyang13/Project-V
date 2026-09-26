#!/bin/bash
# usage: run.sh FRAMES WIDTH HEIGHT SEED  -> work/runs/<f>f_<w>x<h>_s<seed>/
cd "$(dirname "$0")"; F=$1; W=$2; H=$3; S=$4; D=work/runs/${F}f_${W}x${H}_s$S; mkdir -p $D
[ -f work/plate/plate_${W}x${H}.png ] || ffmpeg -v error -y -i input/explorer_robot.png -vf "scale=-2:$H:flags=lanczos,crop=$W:$H" work/plate/plate_${W}x${H}.png
start=$(date +%s)
DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models draw-things-cli generate --model ltx_2.3_22b_distilled_1.1_q8p.ckpt --no-download-missing --disable-preview \
  --image work/plate/plate_${W}x${H}.png --prompt-file jobs/motion_prompt.txt --frames $F --width $W --height $H --seed $S --steps 8 --cfg 1.0 \
  --output $D/raw.mov --video-format prores422hq > $D/cli.log 2>&1
echo "exit=$? secs=$(( $(date +%s)-start ))" > $D/done.txt
[ -f $D/raw.mov ] && ffmpeg -v error -y -i $D/raw.mov -c:v libx264 -crf 16 -pix_fmt yuv420p $D/clip.mp4
