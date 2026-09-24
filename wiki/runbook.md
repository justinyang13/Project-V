# Runbook — exact commands, stage by stage

Follow [SPEC.md](../SPEC.md) for what and why; this page is how. `<job>` = e.g. `002-forest-cabin`. Run everything from the project root (`/Users/justin/Code/Project-V/Video-Zen1`). Use `.venv/bin/python`.

Legend: **[verified]** = ran in job 001 · **[UNVERIFIED]** = not yet run.

## 0. Preflight
```bash
ls /Volumes/SSD-4T-LR/AI/Models | head          # SSD mounted, models present
df -h . | tail -1                                # free disk
ollama ps; pgrep -fl "DrawThings|acestep|dt_generate"   # nothing heavy running
```
To use the CLI: ask the user to quit the Draw Things app first (CLI loads its own model copy).

## 1. Intake
```bash
cp "<image>" input/<job>.<ext>
mkdir -p jobs/<job> && cp jobs/001-snow-tea/job.json jobs/001-snow-tea/prompts.md jobs/<job>/
```
Then edit `job.json` (id, source, source_size, crop, regions) — see stage 2.

## 2. Masks
Edit polygons in `jobs/<job>/job.json` (source pixels). Then look at the overlay:
```bash
.venv/bin/python scripts/mask_preview.py --job <job> --zoom x0 y0 x1 y1     # writes jobs/<job>/mask_overlay_preview*.png
```
Open the PNG (and the zoom). Repeat until animated-area edges sit on real edges. Save the final overlay as `jobs/<job>/mask_overlay_v0.png`. **[verified — this helper was recreated from the scratch script used in job 001 and tested on 001.]**

## 3. Prompt
Edit `jobs/<job>/prompts.md`. `dt_generate.py` reads the section whose header starts with the key (`--pkey P5` → a line `## P5 — …`); the **first fenced code block is the positive prompt, the second is the negative**. Keep the P5 template from SPEC §8.

## 4. Drift probe (3 seeds) [verified with the API]
```bash
for s in 101 202 303; do
  .venv/bin/python scripts/dt_generate.py --job <job> --round r01 --tag t_s$s --seed $s --w 1024 --h 576 --frames 121 --pkey P5
  .venv/bin/python scripts/qc_drift.py  work/<job>/r01/t_s$s/frames 30      # want worst_drift_px <= 0.7
  .venv/bin/python scripts/qc_motion.py work/<job>/r01/t_s$s/frames        # moving_down/up %, activity
done
```
Contact sheets for Claude to read (frames every 10, plus crops of each effect):
```bash
ffmpeg -framerate 24 -i work/<job>/r01/t_s101/frames/f%04d.png -vf "select='not(mod(n\,10))',scale=512:-1,tile=4x3" -frames:v 1 work/<job>/r01/t_s101/sheet_full.png
```
For crops use `crop=W:H:X:Y` before `scale` (coordinates in the 1024×576 frame = `(src_x - crop_x0) × 1024/(crop_x1 - crop_x0)`).

### §Q — editing `qc_motion.py` for a new image
The script has a region table `R = {"snow": (x0,y0,x1,y1), "steam": …, "fire": …}` in **1024×576 frame pixels**. Convert each `qc_only` polygon's bounding box from source pixels:
`x' = (x − crop_x0) × 1024 / (crop_x1 − crop_x0)`, `y' = (y − crop_y0) × 576 / (crop_y1 − crop_y0)`. Rename or add entries for the new effects. It reports mean frame difference, luma std over time, and % of moving pixels going down/up per region. Likewise `qc_drift.py` tracks features in the **left 18 % and right 32 %** of the frame (the room on job 001); for a new image change the two mask lines at the top to areas that stay still and contain texture.

## 5. Two clips [verified with the API]
```bash
.venv/bin/python scripts/dt_generate.py --job <job> --round r02 --tag segA_s101 --seed 101 --w 1024 --h 576 --frames 145 --pkey P5
.venv/bin/python scripts/dt_generate.py --job <job> --round r02 --tag segB_s202 --seed 202 --w 1024 --h 576 --frames 145 --pkey P5
```
Use the two best seeds from stage 4. About 3 min each. Frames land in `work/<job>/r02/<tag>/frames/f0000.png …`.

### §G-CLI — same clip with `draw-things-cli` **[UNVERIFIED]**
```bash
# 1) plate at generation size (16:9 crop of the source, resized to 1024x576) -> work/<job>/plate_1024.png
# 2) prompt text -> work/<job>/prompt.txt  (positive prompt only)
DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models draw-things-cli generate \
  --model ltx_2.3_22b_distilled_1.1_q8p.ckpt --no-download-missing \
  --image work/<job>/plate_1024.png --prompt-file work/<job>/prompt.txt \
  --frames 145 --width 1024 --height 576 --seed 101 \
  --output work/<job>/r02/segA_s101.mov --video-format prores422hq
mkdir -p work/<job>/r02/segA_s101/frames
ffmpeg -i work/<job>/r02/segA_s101.mov -start_number 0 work/<job>/r02/segA_s101/frames/f%04d.png
```
`dt_generate.py` builds `input.png` by cropping with `plate.crop` and resizing with Lanczos; the CLI's own `--image` handling is "aspect-preserving scale and center crop", so **pass an already cropped 1024×576 image**. Check: frame count = 145, size 1024×576, drift ≤ 0.7 px, and compare steps/sampler/shift/CFG with the API path (`--steps 8 --cfg 1`; other keys via `--config-json`). Record what differs in `wiki/lessons.md`.

### §G-API — fallback (what job 001 used)
`scripts/dt_generate.py` posts to `POST http://127.0.0.1:7860/sdapi/v1/img2img` (Draw Things app, Settings → API Server on). Only a whitelist of config keys is sent (sending the full dump returns HTTP 422). Width/height multiples of 64; frames 8n+1 and ≤ 201. The request's `model` key picks the model.

## 6. Loop
```bash
.venv/bin/python scripts/loop_build.py --job <job> \
  --a work/<job>/r02/segA_s101/frames --b work/<job>/r02/segB_s202/frames --out output/<job>/r02
cat output/<job>/r02/qc_final.json
```
Writes `loop_frames/`, `plate.png`, `mask.png`, `<job>_loop10s_1080p24.mp4`, a 60 s preview, `qc_final.json`, `sheet_seam.png`. Gates: `seam_ratio ≤ 1.3`, `locked_pixels_identical: true`, `luma_std_detrended ≤ 1.0`, `luma_max_jump ≤ 1.5`. Claude reads `sheet_seam.png` and one frame at full size. Then ask the user to watch the loop (Sign-off A).

## M. Music and the full hour
### Start the music server
```bash
cd tools/ACE-Step-1.5 && ACESTEP_CHECKPOINTS_DIR=/Volumes/SSD-4T-LR/AI/Models/ACE-Step nohup ./start_api_server_macos.sh > ../../work/acestep_server.log 2>&1 &
# wait until: curl -s http://127.0.0.1:8001/health   returns 200
```
### 30-second samples (stage 7) [verified]
```bash
.venv/bin/python scripts/music_gen.py --tag v_piano --seed 32 --dur 30 --bpm 44 --key "D minor" --prompt "<music prompt>"   # -> work/music/v_piano.flac
ffmpeg -y -i work/music/v_piano.flac -af "lowpass=f=6500,highshelf=f=3000:g=-3,loudnorm=I=-22:TP=-3:LRA=7,afade=t=in:d=2,afade=t=out:st=28:d=2" -c:a libmp3lame -b:a 192k work/music/v_piano.mp3
```
Make three styles (flute+pad, piano, koto), send to the user with `SendUserFile`. Then the ambience sample:
```bash
.venv/bin/python scripts/ambience.py --dur 30 --seed 5 --out work/music/amb_30.wav
ffmpeg -y -i work/music/v_piano.flac -i work/music/amb_30.wav -filter_complex "[0:a]lowpass=f=6500,highshelf=f=3000:g=-3,loudnorm=I=-22:TP=-3:LRA=7[m];[1:a]loudnorm=I=-36:TP=-9:LRA=7[a];[m][a]amix=inputs=2:normalize=0:duration=first[x];[x]afade=t=in:d=2,afade=t=out:st=28:d=2" -c:a libmp3lame -b:a 192k work/music/mixed_30.mp3
```
(`loudnorm` true-peak must be ≥ −9.) To change the music style for the hour, edit the `PROMPT` constant and the `KEYS`/`BPMS` lists at the top of `scripts/music_build.py`.

### Build the hour [verified]
```bash
.venv/bin/python scripts/music_build.py --minutes 60 --out output/<job>/music_60min      # ~15 min; resumable; restarts the music server if it dies
ffmpeg -y -stream_loop 359 -i output/<job>/r02/<job>_loop10s_1080p24.mp4 -i output/<job>/music_60min.m4a \
  -map 0:v -map 1:a -c copy -t 3600 -movflags +faststart output/<job>/<job>_1hr.mp4
```
Checks:
```bash
ffprobe -v error -show_entries format=duration,size -of default=nw=1 output/<job>/<job>_1hr.mp4                  # 3600.000000
ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 output/<job>/<job>_1hr.mp4   # 86400
```
Then loudness in 10-second windows (see `wiki/music.md`) and two excerpts for the user:
```bash
ffmpeg -y -ss 128 -t 40 -i output/<job>/music_60min.wav -c:a libmp3lame -b:a 192k excerpt_first_join.mp3     # across the first crossfade
ffmpeg -y -ss 1800 -t 40 -i output/<job>/music_60min.wav -c:a libmp3lame -b:a 192k excerpt_midpoint.mp3
```
### Swap the audio later (why the silent loop is kept)
```bash
ffmpeg -y -stream_loop 359 -i <job>_loop10s_1080p24_silent.mp4 -i <new_audio>.m4a -map 0:v -map 1:a -c copy -t 3600 -movflags +faststart <job>_1hr_v2.mp4
```
For another length change `359` (loops − 1) and `-t` (seconds); the audio must be at least that long.

## 9. Deliver and clean up
```bash
mv output/<job>/<job>_1hr.mp4 output/<job>/<job>_1hr_1080p24.mp4
mv output/<job>/music_60min.m4a output/<job>/<job>_audio_60min.m4a
cp output/<job>/r02/<job>_loop10s_1080p24.mp4 output/<job>/<job>_loop10s_1080p24_silent.mp4
rm -rf output/<job>/r02 output/<job>/music_60min.wav output/music work        # scratch; the three final files stay
.venv/bin/python scripts/build_docs.py                                        # regenerate docs/*.html
```
Stop the music server (`pkill -f start_api_server_macos; pkill -f acestep-api`). Then update `wiki/runs/<job>.md` and commit.
