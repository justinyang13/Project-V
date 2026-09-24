# Runbook — exact commands, stage by stage

Follow [SPEC.md](SPEC.md) for what and why; this page is how.

**Conventions.** `<id>` = the video folder name, e.g. `Video-Zen3`. **Run everything from inside the video folder** (`cd /Users/justin/Code/Project-V/<id>`): shared scripts are `../scripts/…`, Python is `../.venv/bin/python`. Small variables: `PY=../.venv/bin/python`, `SC=../scripts`.
Legend: **[verified]** ran on the first video · **[UNVERIFIED]** not run yet.

## 0. Preflight and new video folder
```bash
ls /Volumes/SSD-4T-LR/AI/Models | head; df -h . | tail -1          # SSD mounted, disk free
ollama ps; pgrep -fl "DrawThings|acestep|dt_generate"                # nothing heavy running
cd /Users/justin/Code/Project-V && mkdir -p <id>/{input,jobs/<id>,output,work} && cd <id>
```
Folder naming: `Video-<Shortname><n>` (SPEC §3). To use the CLI ask the user to quit the Draw Things app.

## 1. Scene idea → image [verified] → Approval 1
```bash
# write jobs/<id>/image_prompt.txt and image_negative.txt (templates: SPEC §9)
$SC/image_candidates.sh <id>            # 4 candidates, seeds 11/22/33/44, 1920x1088, ~2-3 min
# -> work/<id>/candidates/cand1_s11.png … cand4_s44.png  +  work/<id>/candidates/sheet.png (numbered 2x2)
$SC/image_candidates.sh <id> 4 55       # another round (seeds 55/66/77/88) after prompt changes
```
Screen each candidate (SPEC 1.1), send `sheet.png` (SendUserFile) with one line per image, wait for the pick. Then intake:
```bash
cp work/<id>/candidates/cand<k>_s<seed>.png input/<id>.png
cp ../Video-Zen1/jobs/001-snow-tea/job.json jobs/<id>/job.json && cp ../Video-Zen1/jobs/001-snow-tea/prompts.md jobs/<id>/
# edit job.json: id, source "input/<id>.png", source_size [1920,1088], plate.crop [0,4,1920,1084], regions (stage 2)
```
The script runs `draw-things-cli generate --model z_image_turbo_1.0_q8p.ckpt --no-download-missing --width 1920 --height 1088 --seed S --prompt-file … --negative-prompt-file …` with `DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models`, skips candidates that exist, and draws the sheet with Pillow (this ffmpeg has no `drawtext`).
*Own image instead?* copy it to `input/<id>.<ext>` and set `source`, `source_size` and a 16:9 `plate.crop`.

## 2. What animates → masks [verified] → Approval 2
Edit the polygons in `jobs/<id>/job.json` (source pixels), then look:
```bash
$PY $SC/mask_preview.py --job <id> --zoom x0 y0 x1 y1        # jobs/<id>/mask_overlay_preview.png (+ _zoom.png)
```
Open the PNGs; repeat until edges sit on real edges; save the final one as `jobs/<id>/mask_overlay_v0.png`. Send it to the user with the plain-words list *"Moves: … Frozen: everything else."* and wait for approval.

## 3. Audio sample → Approval 3 [verified] (see also §M)
Start the music server (§M), then three 30 s styles, each checked, softened, levelled:
```bash
for spec in "a_flute:21:<flute+pad prompt>" "b_piano:32:<piano prompt>" "c_koto:33:<koto prompt>"; do
  IFS=: read tag seed prompt <<< "$spec"
  $PY $SC/music_gen.py --tag s_$tag --seed $seed --dur 30 --bpm 46 --key "D minor" --prompt "$prompt"
  ffmpeg -y -i work/music/s_$tag.flac -af "lowpass=f=6500,highshelf=f=3000:g=-3,loudnorm=I=-22:TP=-3:LRA=7,afade=t=in:d=2,afade=t=out:st=28:d=2" -c:a libmp3lame -b:a 192k work/music/s_$tag.mp3
  $PY $SC/audio_qc.py work/music/s_$tag.mp3 --out work/music/qc_$tag | grep -E "harsh_events|pass"     # must be pass: true
done
```
(Prompts: SPEC §9 and [Music](music.md). Regenerate any sample that fails the check.) Send the MP3s to the user; after the pick, the ambience sample:
```bash
$PY $SC/ambience.py --dur 30 --seed 5 --out work/music/amb_30.wav
ffmpeg -y -i work/music/s_<pick>.flac -i work/music/amb_30.wav -filter_complex "[0:a]lowpass=f=6500,highshelf=f=3000:g=-3,loudnorm=I=-22:TP=-3:LRA=7[m];[1:a]loudnorm=I=-36:TP=-9:LRA=7[a];[m][a]amix=inputs=2:normalize=0:duration=first[x];[x]afade=t=in:d=2,afade=t=out:st=28:d=2" -c:a libmp3lame -b:a 192k work/music/mixed_30.mp3
```
(`loudnorm` true-peak must be −9 or higher.) Also send `amb_30.wav` as an MP3 at +14 dB louder so the user can judge the ambience alone. Save the approved prompt/BPM/keys to `jobs/<id>/music.md`.

## 4. Video prompt
Edit `jobs/<id>/prompts.md`. `dt_generate.py` reads the section whose header starts with the key (`--pkey P5` → `## P5 — …`); the **first fenced block is the positive prompt, the second the negative**. Template: SPEC §9.

## 5. Drift probe (3 seeds) [verified with the API]
```bash
for s in 101 202 303; do
  $PY $SC/dt_generate.py --job <id> --round r01 --tag t_s$s --seed $s --w 1024 --h 576 --frames 121 --pkey P5
  $PY $SC/qc_drift.py  work/<id>/r01/t_s$s/frames 30      # want worst_drift_px <= 0.7
  $PY $SC/qc_motion.py work/<id>/r01/t_s$s/frames        # moving_down/up %, activity
done
ffmpeg -framerate 24 -i work/<id>/r01/t_s101/frames/f%04d.png -vf "select='not(mod(n\,10))',scale=512:-1,tile=4x3" -frames:v 1 work/<id>/r01/t_s101/sheet_full.png
```
For crops use `crop=W:H:X:Y` before `scale` (frame coordinates = `(src_x − crop_x0) × 1024/(crop_x1 − crop_x0)`).

### §Q — editing the QC scripts for a new image
`qc_motion.py` has a region table `R = {"snow": (x0,y0,x1,y1), …}` in **1024×576 frame pixels**; convert each `qc_only` polygon's bounding box with the formula above; rename/add entries for the new effects. `qc_drift.py` tracks features in the left 18 % and right 32 % of the frame (the room on the first video); **this is hardcoded and wrong for any other image**: change the two mask lines at the top to the job's *locked*, textured areas (never areas with rain, bamboo, steam or fire; Lessons A14) and cross-check 2–3 separate locked objects, which should agree. If every seed fails by a wide margin, see SPEC §10 (stabilize fallback, Lessons A15).

## 6. Two clips [verified with the API]
```bash
$PY $SC/dt_generate.py --job <id> --round r02 --tag segA_s101 --seed 101 --w 1024 --h 576 --frames 145 --pkey P5
$PY $SC/dt_generate.py --job <id> --round r02 --tag segB_s202 --seed 202 --w 1024 --h 576 --frames 145 --pkey P5
```
Two best seeds from stage 5; ~3 min each; frames in `work/<id>/r02/<tag>/frames/f0000.png …`.

### §G-CLI — the same clip with `draw-things-cli` [UNVERIFIED]
```bash
# plate at generation size (16:9 crop of the source, Lanczos to 1024x576) -> work/<id>/plate_1024.png ; positive prompt -> work/<id>/prompt.txt
DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models draw-things-cli generate \
  --model ltx_2.3_22b_distilled_1.1_q8p.ckpt --no-download-missing \
  --image work/<id>/plate_1024.png --prompt-file work/<id>/prompt.txt \
  --frames 145 --width 1024 --height 576 --seed 101 \
  --output work/<id>/r02/segA_s101.mov --video-format prores422hq
mkdir -p work/<id>/r02/segA_s101/frames && ffmpeg -i work/<id>/r02/segA_s101.mov -start_number 0 work/<id>/r02/segA_s101/frames/f%04d.png
```
The CLI's `--image` does "aspect-preserving scale and center crop", so pass an already cropped 1024×576 image. Check frame count = 145, size, drift ≤ 0.7 px, and compare steps/sampler/shift/CFG with the API path (`--steps 8 --cfg 1`; other keys via `--config-json`). Record differences in [Lessons](lessons.md).

### §G-API — fallback (what the first video used)
`dt_generate.py` posts to `POST http://127.0.0.1:7860/sdapi/v1/img2img` (Draw Things app, Settings → API Server on). Only a whitelist of config keys is sent; width/height multiples of 64; frames 8n+1 and ≤ 201; the request's `model` key picks the model.

## 7. Loop → Review 1 [verified]
```bash
$PY $SC/loop_build.py --job <id> --a work/<id>/r02/segA_s101/frames --b work/<id>/r02/segB_s202/frames --out work/<id>/loop
cat work/<id>/loop/qc_final.json
```
Writes `loop_frames/`, `plate.png`, `mask.png`, `<id>_loop10s_1080p24.mp4`, a 60 s preview, `qc_final.json`, `sheet_seam.png`. Gates: `seam_ratio ≤ 1.3`, `locked_pixels_identical: true`, `luma_std_detrended ≤ 1.0`, `luma_max_jump ≤ 1.5`. Claude reads `sheet_seam.png` and a full frame, then sends the loop (and the 60 s preview) for Review 1.

## 8. Full hour of audio → Review 2  (§M has server start/stop)
```bash
$PY $SC/music_build.py --minutes 60 --out work/<id>/music_60min \
  --prompt "<approved prompt>" --keys "D minor,F major,A minor,C major,G minor" --bpms "44,40,46,42"       # ~20 min; resumable
```
What it does: per piece generate → soften → `audio_qc` → retake (new seed) up to 4×; crossfade; slow leveler; ambience; fades; AAC; **final `audio_qc` of the finished hour** and the listening pack. Watch the log for `harsh events N -> retry` and `WARNING ... least-bad take`. Outputs: `work/<id>/music_60min.{wav,m4a}`, `music_60min_pieces_qc.json`, `music_60min_qc/audio_qc.json`, **`music_60min_qc/listening_pack.mp3`** + `listening_pack.txt`.
```bash
cat work/<id>/music_60min_qc/audio_qc.json | head -30                    # harsh_events must be 0, pass: true
```
Send `listening_pack.mp3` (with the timestamp list) to the user for Review 2. If the user flags pack item *k*, note its timestamp `t`, find the piece (`t ÷ 142 s`), delete that piece's file(s) in `work/music/<work>/`, rerun (resumable), re-check, resend. To tune the check, edit `LIMITS` in `../scripts/audio_qc.py`; single files: `$PY $SC/audio_qc.py <file> --excerpts 6` (clips of the worst moments) or `--pack`.

## 9. Mux, deliver, clean up
```bash
ffmpeg -y -stream_loop 359 -i work/<id>/loop/<id>_loop10s_1080p24.mp4 -i work/<id>/music_60min.m4a \
  -map 0:v -map 1:a -c copy -t 3600 -movflags +faststart output/<id>_1hr_1080p24.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 output/<id>_1hr_1080p24.mp4                       # 3600.000000
ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 output/<id>_1hr_1080p24.mp4   # 86400
cp work/<id>/music_60min.m4a output/<id>_audio_60min.m4a
cp work/<id>/loop/<id>_loop10s_1080p24.mp4 output/<id>_loop10s_1080p24_silent.mp4
rm -rf work                                                              # scratch; the three files in output/ stay
pkill -f start_api_server_macos; pkill -f acestep-api                    # stop the music server
cd .. && .venv/bin/python scripts/build_docs.py                          # rebuild wiki/html
```
Then fill `<id>/RUNLOG.md`, update [Lessons](lessons.md), commit and push (`git add -A && git commit && git push` from `Project-V/`).

## M. Music server
```bash
cd /Users/justin/Code/Project-V/tools/ACE-Step-1.5 && ACESTEP_CHECKPOINTS_DIR=/Volumes/SSD-4T-LR/AI/Models/ACE-Step nohup ./start_api_server_macos.sh > /tmp/acestep_server.log 2>&1 &
# ready when: curl -s http://127.0.0.1:8001/health returns 200  (music_build.py also restarts it by itself if it dies)
```

## Swap. Put different audio on the picture later
```bash
ffmpeg -y -stream_loop 359 -i output/<id>_loop10s_1080p24_silent.mp4 -i <new_audio>.m4a -map 0:v -map 1:a -c copy -t 3600 -movflags +faststart output/<id>_1hr_v2.mp4
```
For another length change `359` (loops − 1) and `-t` (seconds); the audio must be at least that long.
