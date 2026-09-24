# Wiki — Still-to-loop playbook

Read this to **validate** what was done and to **repeat** it for a new image.
Design and rationale: `../SPEC.md`. Per-image history: `runs/`.

| Run | Image | Status | Hero model | Final |
|---|---|---|---|---|
| [001-snow-tea](runs/001-snow-tea.md) | snowy zen garden, tea steam, brazier fire | ✅ Done, approved | LTX-2.3 22B distilled | `output/001-snow-tea/` |

---

## The idea in 30 seconds

1. Only the parts that should move come from AI video. Everything else is the original image, locked by a mask.
2. Generate **two clips (about 6 s each) from the same still** with different seeds. Draw Things caps one request at 201 frames, and clips that start from the same image can't drift apart.
3. Make it loop by **chaining A → B → A with 1 s crossfades** (240 frames = 10 s). Never ask the model to loop.
4. Measure the seam, drift, flicker, and motion direction with numbers. Look at frame sheets. Then you watch the 60 s preview.

## Local-first: who does what (details: SPEC §12)

Local models and scripts do the work; Claude only decides.

| Work | Owner |
|---|---|
| Video generation | Draw Things (LTX-2.3; Wan 2.2 I2V if installed) |
| Prep, loop build, encode, numeric QC | Plain Python + ffmpeg (no LLM) |
| Writing scripts | `qwen3-coder:30b` via `opencode run --model ollama/qwen3-coder:30b "<brief>"` |
| Scoring frame sheets, drafting run-log entries | `qwen3.5:35B` / `qwen3.8:27b` (vision) via Ollama |
| Choosing changes between rounds, final seam spot-check, reviewing diffs | Claude |

- Local scores **advise**; the numeric metrics plus your sign-off **gate**.
- Memory is shared (64 GB): never run Ollama vision models and a Draw Things render at once, and never load `gpt-oss:120b`.
- In each run-log step, note which model did it and whether it needed correcting. That builds a record of what local models handle reliably.

## Repeat for a new image: checklist

### A. Look at the image (5 min)
- [ ] List what should move, and **how** (direction, speed, character). Example: "rain falls diagonally left, puddle ripples, candle flickers".
- [ ] List what must stay still, which is usually everything else.
- [ ] Find **natural boundaries** for mask edges: window or door frames, table edges, object silhouettes. Masks that follow real edges make invisible seams.
- [ ] Flag anything that could go wrong, like frozen particles in the still (snow or dust in the room), reflections, or light sources that should flicker.

### B. Create the job folder
- [ ] `input/<NNN>-<name>.<ext>`
- [ ] Copy `jobs/001-snow-tea/job.json` to `jobs/<NNN>-<name>/job.json` and edit:
  - `source`, `source_size`, `plate.crop` (16:9 crop of the source)
  - `regions`: one `animated` polygon per moving area, `lock` polygons for foreground objects that overlap them, and `qc_only` boxes for each effect you want to measure
  - `loop` (keep 10 s / 24 fps / 1 s fade unless there's a reason)
- [ ] Draw the polygons over the image (Pillow, as done for job 001) and **look at the overlay**: animated area tinted, lock/QC boxes outlined. Adjust until the edges sit on real edges, and save it as `jobs/<job>/mask_overlay_v<N>.png`. (`loop_build.py` also writes `mask.png` for the final mask.)

### C. Write prompts (`jobs/<job>/prompts.md`, copy from 001)
- [ ] Describe **motion only**. The image already gives the look.
- [ ] **Do not write "the camera does not move / zoom".** It primes camera motion. Use the P5 cinemagraph wording: a single locked photograph where only the named things move. (The negative prompt is ignored by the distilled LTX model.)
- [ ] Give each moving element a direction and speed.
- [ ] Wan: concrete, under about 120 words. LTX-2: one flowing present-tense paragraph, under about 200 words, starting with the main action.
- [ ] Add effect-specific negatives (e.g., "snow falling upward", "thick smoke").

### D. Generate and choose (Round 1 → 2)
- [ ] R1: 2–3 seeds of LTX-2.3 at 1024×576 × 121 frames. Run `qc_drift.py` and `qc_motion.py`, and look at full/fire/steam sheets. Keep only seeds with drift ≤ 0.7 px.
- [ ] R2: two 145-frame clips (segments A and B) from two passing seeds. (Wan 2.2 I2V wasn't installed; if you add it, 16 fps needs interpolation to 24.)

### E. Build the loop
- [ ] Run `scripts/loop_build.py` (see Recipe). It builds, encodes and runs the final checks.
- [ ] Read `sheet_seam.png`: the seam frames should look like any other consecutive frames.
- [ ] Watch `_preview60s.mp4` (6 loops) full screen, looking at the fire, steam, and door edges.

### F. Iterate (max 4 rounds)
- [ ] Fix only what failed. Use the knob table in `prompts.md` and change ≤ 2 variables per round.
- [ ] Log each round in the run log with what changed, why, metrics, and decision.

## How to validate a run (what you check)

| Check | Where | Looks right when |
|---|---|---|
| Masks follow real edges | `jobs/<job>/mask_overlay_v*.png` | Cyan stops exactly at door frames and objects |
| Seam | `qc_final.json` → `seam_ratio`, `sheet_seam.png` | ≤ 1.3; no jump between frames 239 and 0 |
| No drift | `qc_drift.py` → `worst_drift_px` | ≤ 0.7 px; garden doesn't slide against the frames |
| No flicker | `qc_final.json` → `luma_std_detrended`, `luma_max_jump` | ≤ 1.0 / ≤ 1.5 |
| Motion direction | `qc_motion.py` → `moving_down` (snow), `up` (steam) | ≥ 65 % / ≥ 60 % |
| Your eyes | `preview_60s.mp4` | You can't find the loop point |

**Music and long-form (1 h) video:** see [music.md](music.md).

## Recipe that worked (001-snow-tea), copy this for a new image

Prereqs: Draw Things running with API server on; models in `/Volumes/SSD-4T-LR/AI/Models` (flat folder); `.venv` set up (see Tool reference).

1. `input/<NNN>-<name>.webp`, then `jobs/<NNN>-<name>/job.json` (crop to 16:9, mask polygons, lock polygons) and `prompts.md` (copy P5 style; edit only the moving things).
2. Check camera drift first, with two seeds, before doing anything else:
   ```bash
   .venv/bin/python scripts/dt_generate.py --job <job> --round r01 --tag t_s101 --seed 101 --w 1024 --h 576 --frames 121 --pkey P5
   .venv/bin/python scripts/qc_drift.py work/<job>/r01/t_s101/frames 30     # want worst_drift_px <= 0.7
   .venv/bin/python scripts/qc_motion.py work/<job>/r01/t_s101/frames       # snow down %, steam up %, fire activity
   ```
3. Render the two segments (145 frames each, about 3 min each) with two seeds that passed step 2:
   ```bash
   .venv/bin/python scripts/dt_generate.py --job <job> --round r02 --tag segA_s101 --seed 101 --w 1024 --h 576 --frames 145 --pkey P5
   .venv/bin/python scripts/dt_generate.py --job <job> --round r02 --tag segB_s202 --seed 202 --w 1024 --h 576 --frames 145 --pkey P5
   ```
4. Build, encode and QC (takes about 1 minute):
   ```bash
   .venv/bin/python scripts/loop_build.py --job <job> --a work/<job>/r02/segA_s101/frames --b work/<job>/r02/segB_s202/frames --out output/<job>/r02
   ```
   Read `output/<job>/r02/qc_final.json` and `sheet_seam.png`; watch `_preview60s.mp4`.
5. ProRes master: `ffmpeg -framerate 24 -i output/<job>/r02/loop_frames/f%04d.png -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le out.mov`

Files: `scripts/dt_generate.py` (one clip via API; whitelists the config keys), `scripts/qc_drift.py`, `scripts/qc_motion.py` (regions are hard-coded for job 001; edit `R` at the top for a new image), `scripts/loop_build.py` (reads regions from `job.json`).

## Gotchas learned (append as we learn)

- *Plan stage (still true):* first/last-frame conditioning pins falling particles to the still's frozen positions, so they visibly snap or reverse at the loop point. Crossfade clips into a loop instead (A → B → A).
- *Plan stage:* the source still has frozen "snow" specks on indoor surfaces (blanket, floor). Without the lock mask, models may animate them as indoor snowfall.
- *Plan stage:* model sizes: Wan frames = 4n+1; LTX frames = 8n+1. Draw Things needs width/height in multiples of 64 (1024×576 is exactly 16:9).

## Tool reference

| Tool | Notes |
|---|---|
| Draw Things API | Settings > API Server → HTTP, port 7860. Exact request/response schema: see run 001, stage 0 entry. |
| DT base configs | In the app, set up the model → ⋯ → *Copy Configuration* → paste into `jobs/_dt_base/<model>.json`. The scripts merge job overrides onto this. |
| ffmpeg | Contact sheets: `ffmpeg -i in.mp4 -vf "select='not(mod(n\,20))',scale=480:-1,tile=4x3" -frames:v 1 sheet.png` |
| venv | `python3.14 -m venv .venv && .venv/bin/pip install numpy opencv-python-headless pillow requests` |
- **Camera drift is the main failure of image-to-video.** LTX-2.3 zoomed in 15–25 % with descriptive prompts. Writing "the camera never zooms / pushes in" made it *worse*. What fixed it: describe a *cinemagraph* ("one single locked photograph … framing identical in every frame … pixel-still. The only motion is …"), which gave 0.1 px drift on 2 of 3 seeds. Always measure drift (`qc_drift.py`) on a couple of seeds; it is seed-dependent.
- The distilled LTX model runs at CFG 1, so the **negative prompt and `guidance_scale` overrides do nothing**. Put everything in the positive prompt.
- **Draw Things API:** post only a whitelist of config keys (the full dump from `GET /` gets HTTP 422). Width/height must be multiples of 64 (else silently rounded down and the picture is squashed). **Max 201 frames per request**, frames must be 8n+1. The request's `model` key picks the model, whatever the app has selected. There is no cancel: a probe with a valid frame count starts a real render.
- The 24 fps of LTX matches the target, so no frame interpolation (RIFE) was needed.
- Speed on the M5 Max (64 GB): 145 frames at 1024×576, 8 steps ≈ 3 min. GPU sits at 0 % during model load/decode and at ~100 % while sampling; CPU stays near 0.
- `draw-things-cli` (installed via brew) can generate headless and write ProRes, but loads its own copy of the model (~35 GB), so quit the app first. Not needed so far; try it only if clips longer than 201 frames are required. Use `--no-download-missing` and `DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models`.
- Models live flat in `/Volumes/SSD-4T-LR/AI/Models`; see `wiki/models.md`. The SSD is exFAT (no symlinks).
- Long waits: run renders with `nohup … &` and chain the next step in the same script (`until grep -q DONE log; do sleep 10; done`), so the pipeline never sits idle waiting for a manual restart.
