# SPEC — Scene description → 1-hour ambient loop video (v4, generic)

**Input:** a scene description (Claude asks for it first, §1.1). **Output:** a 1-hour, 1080p (and optionally 4K) 24 fps YouTube-ready video with original soft music and ambience, plus the separate audio track and a silent 10-second loop so the audio can be swapped later.

Status: v4.3 · 2026-09-23 · derived from the reference run (a snowy tea-room video) that produced the proven numbers. v4.1 added the user's **"alive everywhere" rule** (§1.4). v4.2 added an optional **4K master** step (stage 7b). v4.3 makes **asking you for the scene description the first step** (stage 1.0). Items not yet proven are marked **[UNVERIFIED]**.

Where things live: this wiki (`Project-V/wiki/`) holds the repeatable steps and HTML; every video has its own folder `Project-V/Video-<Shortname><n>/`; shared scripts are in `Project-V/scripts/`. See §3.

Companion docs: [Runbook](runbook.md) (exact commands) · [Lessons](lessons.md) (what failed and why) · [Music](music.md) · [Models](models.md) · [Posting plan](posting-plan.md) · HTML versions in `wiki/html/` (open `wiki/html/index.html`).

---

## 1. Contract

### 1.1 What you provide
**A scene description, asked for before anything else (stage 1.0).** Claude starts every job by asking you for it; it does not pick a scene itself. A sentence is enough ("rainy temple at night", "mystical mushroom forest with floating lights"), and more detail is welcome: place and time of day, weather, mood and colours, the main objects, and anything you want to **move, glow or float** (rain, fireflies, waterfall, steam, mist). You can also attach a **reference image** to describe the look you want (Claude describes its mood and layout in its own words and does not copy a signed artwork). Optionally add the music mood and the ambience sound (rain, waterfall, fire…). If you hand over your own finished image, skip the generation steps of stage 1.

### 1.2 What you get (per video folder `Video-<Name>`, id `<id>` = the folder name, e.g. `Video-Zen3`)
Kept in `Video-<Name>/output/`:

| File | What | Notes |
|---|---|---|
| `<id>_1hr_1080p24.mp4` | The final video | 3600.000 s, 1920×1080, 24 fps, H.264 + AAC 256 kbps, about 1.1 GB. Upload this. |
| `<id>_1hr_4k24.mp4` *(optional, stage 7b)* | The 4K version | 3600.000 s, 3840×2160, 24 fps, HEVC or H.264 + the same AAC. Size depends on the encode (several GB, check before uploading). **[UNVERIFIED]** |
| `<id>_loop10s_4k24_silent.mp4` *(optional, stage 7b)* | The 4K seamless loop, no audio | 4K master picture for re-muxing. |
| `<id>_audio_60min.m4a` | The full-length mix (music + ambience) | Kept separately so the audio can be replaced later. About 110 MB. |
| `<id>_loop10s_1080p24_silent.mp4` | The seamless 10-second loop, no audio | The master picture. Re-mux with any audio to make a new long video (Runbook §Swap). |

Everything else (frames, candidates, samples, ProRes, previews, listening packs) is scratch and is deleted at the end (stage 9). The folder keeps only: `input/<id>.png` (the chosen image), `jobs/` (prompts, masks, settings), `README.md`, `RUNLOG.md`, `RUNLOG.html` (its own page, built by `build_docs.py`) and `qc-report.md`.

### 1.3 Human approvals (the only times you're needed)
**Phase 1 — approve before any heavy rendering** (about 15 minutes of your time). Claude does not start video rendering until all three are approved:
1. **Image** (stage 1): pick one of 4 numbered candidates (8 from two compositions if the first round is rejected).
2. **What animates** (stage 2): approve the motion list and the mask overlay picture (which parts move, which stay frozen).
3. **Audio** (stage 3): pick one of three 30-second styles, then approve it again with ambience added.

**Phase 2 — final review** (about 20 minutes):
4. **The loop** (stage 7): watch the 10-second loop repeating; can you see the loop point? Do the effects look right?
5. **The hour of audio** (stage 8): listen to the **listening pack** (about a minute of the riskiest and random moments from all through the hour) and confirm nothing is screechy, scratchy, or unpleasant.
6. Upload to YouTube yourself (§10).

### 1.4 Style rule (from the user, Video-Zen3): the picture must feel alive everywhere
The reference run animated only a small part of the frame (snow in the doorway, a flame, a cup), and the rest looked static. **Do not repeat that.**
- **Broad motion:** the animated area is a large share of the frame, and the moving things are spread across **different areas** (left, right, foreground, background, top, bottom), so no viewer thinks "only one small part is alive". Aim for **5–7 moving elements** in at least 3 separate zones, not 2–3.
- **Looser scenes are allowed:** a rigid frame (window, shoji) is no longer required. Where the scene has no rigid anchor, **assume the stabilizer fallback** (§10, Lessons A15) and plan for it from the start, instead of choosing a scene only to avoid drift.
- **Lock only what must be rigid** (mug, book, lamp base, furniture edges). Everything else that can plausibly move (weather, clouds/mist, distant lights, glass droplets, curtains, flames, glow, foliage) is in the animated regions. Drift is still measured on the `lock` regions (Lessons A14); the stabilizer, not a small mask, is what protects the frame.
- **Cost accepted:** more moving area means more drift and seam risk. Run the 3-seed drift probe (stage 5) as usual, use the stabilizer when needed, and check the seam sheet on every animated boundary.
- **Cityscapes are viewed from high up** (roughly floor 30+ looking out over and down at the skyline), not from street level.

### 1.5 Roles
| Who | Does |
|---|---|
| **Claude** | Plans the scene, writes prompts, draws the masks, runs the stages, reads the QC numbers and contact sheets, decides what to change, writes the log. Cannot hear audio or watch motion, so it measures and asks. |
| **Scripts** (`Project-V/scripts/`) | Rendering, compositing, measuring, encoding, audio checking. Deterministic. |
| **Draw Things via `draw-things-cli`** (never the app, so closing the app can't affect a render) | **Text-to-image** with Z Image Turbo, verified with the CLI. **Image-to-video** with LTX-2.3: the reference run used the app's HTTP API; the CLI video path is **[UNVERIFIED]** and is validated in stage 0. |
| **ACE-Step 1.5** (local, MIT) | Music generation. |
| **You** | The approvals above. |

**Draw Things "projects":** projects (the history/canvas files) exist only inside the Draw Things app; `draw-things-cli` has no project feature, it just writes files. So **the video folder is the project**: it holds every prompt, seed and setting (`jobs/`), the chosen image (`input/`) and the log (`RUNLOG.md`). If you want the images to also appear in the app, create a project named `Video-<Name>` there yourself and import the chosen image; nothing in the pipeline depends on it.

---

## 2. The pipeline at a glance

```
description ─► 1 Image ─► 2 What animates ─► 3 Audio sample ──[ PHASE 1: 3 approvals ]──►
        (4 cands)   (masks, motion)    (3 styles + ambience)

   4 Prompt ─► 5 Drift probe ─► 6 Two clips ─► 7 Loop build ─[ review: loop ]─► (7b 4K master, optional) ─► 8 Full audio ─[ review: listening pack ]─► 9 Mux, deliver, clean up
   (P5)        (3 seeds)        (A and B)      (QC gates)                        (1 h, harshness-checked)
```

Design principles (each paid for by a failure):
1. **Only rigid things are locked; everything that can plausibly move is animated, spread over the whole frame** (§1.4). Locked areas come from the original image, pixel-locked by a mask.
2. **The loop is built, not generated.** Two clips from the same image, chained A → B → A with crossfades.
3. **Measure the camera first.** Image-to-video models drift and zoom; test drift on 3 seeds before final clips.
4. **Describe a photograph, not a scene.** The prompt lists what is frozen and the only things that move. Never write "the camera does not move".
5. **One heavy thing at a time on the 64 GB Mac.**
6. **Every stage has numbers.** A stage is done when its gate passes, not when it looks fine.
7. **Design the image for animation** (stage 1.2).
8. **Approve first, render later.** Image, animation plan and audio style are approved before any long render, so no GPU time is wasted on a direction you'd reject.
9. **Soft to the ear, verified.** Every music piece is checked for screech, harshness, scratch, crackle, clicks, clipping and dropouts; bad pieces are regenerated (stage 8).

---

## 3. Folders and naming

```
Project-V/                         one git repo (private, GitHub justinyang13/Project-V)
  wiki/                            THE repeatable steps: SPEC.md, runbook.md, lessons.md, music.md, models.md, posting-plan.md
    html/                          browsable HTML of the wiki (open wiki/html/index.html); rebuilt by scripts/build_docs.py
    html-src/                      HTML template and style
    archive/                       superseded specs
  scripts/                         shared scripts used by every video (run from the video folder)
  tools/ACE-Step-1.5/              music model code (git-ignored; see Environment)
  .venv/                           shared Python environment (git-ignored)
  Video-<Shortname><n>/            ONE FOLDER PER VIDEO (e.g. Video-Zen3, Video-Autumn1)
    input/<id>.png                 the chosen image
    jobs/<id>/                     job.json (masks), prompts.md, image_prompt.txt, image_negative.txt, mask overlay
    output/                        the three final files (only these stay)
    work/                          scratch (deleted at the end)
    README.md  RUNLOG.md  qc-report.md
```
- **Naming:** `Video-<Shortname><n>` where the shortname is one word for the series/scene (`Zen`, `Autumn`, `Rain`) and `<n>` counts up within it. The video's `<id>` is the folder name (`Video-Zen3`); inside `jobs/` use `jobs/<id>/`.
- **Run everything from the video folder**, calling shared scripts as `../scripts/…` and Python as `../.venv/bin/python` (the Runbook uses these forms).
- **Existing folders:** `Video-Zen2` and `Video-BeachSunset1` predate this layout; they keep their own copies of scripts/docs, are not in git, and are left untouched.

---

## 4. Environment (one-time setup, already done on this machine)

| Item | Where / value |
|---|---|
| Machine | Apple M5 Max, 64 GB unified memory, macOS |
| Project | `/Users/justin/Code/Project-V` (private GitHub repo `justinyang13/Project-V`) |
| Models folder (flat, single) | `/Volumes/SSD-4T-LR/AI/Models` (exFAT SSD). **Never download a model that already exists there.** New downloads go there. |
| Image model | `z_image_turbo_1.0_q8p.ckpt` (Z Image Turbo 1.0) |
| Video model | `ltx_2.3_22b_distilled_1.1_q8p.ckpt` (+ Gemma 3 12B encoder, LTX 2.3 VAE, upscalers) |
| Music model | ACE-Step 1.5 at `tools/ACE-Step-1.5` (git-ignored; `git clone https://github.com/ACE-Step/ACE-Step-1.5.git`, then `uv sync`). Weights on the SSD in `/Volumes/SSD-4T-LR/AI/Models/ACE-Step`; `tools/ACE-Step-1.5/checkpoints` is a **symlink** to that folder. |
| Python | `Project-V/.venv` (Python 3.14; `numpy opencv-python-headless pillow requests markdown pygments`). ACE-Step has its own `.venv` (3.12) via `uv`. |
| Other tools | `ffmpeg`, `uv`, `gh` (logged in as `justinyang13`), `draw-things-cli` (tap `drawthingsai/draw-things`) |
| Access | Claude app has Full Disk Access (needed once to read Draw Things' sandbox) |

---

## 5. Parameters (defaults that worked; change only with a reason)

| Parameter | Value | Why |
|---|---|---|
| Image size | **1920×1088** (multiples of 64), Z Image Turbo, 8 steps; plate crop `[0, 4, 1920, 1084]` = exactly 1920×1080 | Draw Things rounds down to a multiple of 64 |
| Image candidates | 4, seeds 11, 22, 33, 44 (next round 55, 66, 77, 88) | ~30 s each (+ ~50 s model load) |
| Generation size (video) | **1024×576** | Multiple of 64 |
| Clip length | **145 frames** (8n+1) each, two clips | Draw Things caps a request at 201 frames; LTX needs 8n+1 |
| Loop | 240 frames = 10.000 s at 24 fps; crossfade 24 frames (1 s), equal-power | 240 = 2 × 120; exactly 360 loops = 1 hour |
| 4K master (optional) | **3840×2160**, upscale the finished 240-frame loop once, then stream-copy it 360× (the hour is never upscaled) | 4× the pixels of 1080p but only 240 frames to process; see stage 7b **[UNVERIFIED]** |
| Video model settings | 8 steps, sampler TCD Trailing, shift 5, CFG 1 (negative prompt and guidance overrides have no effect) | Recommended preset |
| Seeds (video) | probe 101, 202, 303; clips A and B use two that passed | Drift is seed-dependent |
| Music pieces | 150 s each, 8 s crossfades, ~26 pieces for 1 h, up to 4 takes per piece | 240 s pieces crashed the music server |
| Music style | slow soft piano, 40–46 BPM, keys D minor / F major / A minor / C major / G minor | Chosen by the user; see [Music](music.md) |
| Loudness | music −22 LUFS, ambience −36 LUFS (14 dB under), final peak ≤ 0.89 | Comfortable for hours |
| Audio softening | low-pass 6.5 kHz, high-shelf −3 dB above 3 kHz, slow leveler (−8…+3 dB over ~20 s) | Removes harshness and loudness swings |
| Audio check limits | see `scripts/audio_qc.py` (`LIMITS`): tone ≥ −16 dB, HF ratio ≥ 0.10, HF burst ≥ 40 dB, flatness ≥ 0.35, click ≥ 12, clipping ≥ 0.05 %, dropout ≥ 30 dB | Calibrated on moments the user confirmed unpleasant |
| Final encode | H.264 stream-copied from the loop (no re-encode), AAC 256 kbps, `+faststart` | 1.1 GB per hour |

---

## 6. Stages

Legend: **C** = Claude · **S** = script · **U** = your approval.

### Stage 0 — Preflight (S/C, ~2 min)
- Models present; SSD mounted; disk free ≥ 10 GB; nothing heavy running (`ollama ps`, `pgrep -fl "DrawThings|acestep"`).
- For CLI rendering ask you to quit the Draw Things app (the CLI loads its own ~35 GB copy of the video model).
- **[UNVERIFIED] Validate the CLI for video once,** with a 145-frame clip (Runbook §G-CLI): check frame count and size, drift ≤ 0.7 px, settings equal to the API path (steps 8, TCD Trailing, shift 5, CFG 1), and whether the 201-frame cap applies. Record the result in [Lessons](lessons.md). If it fails, fall back to the HTTP API (Runbook §G-API) and tell you.
- Create the video folder `Video-<Shortname><n>/` with `input/ jobs/<id>/ output/ work/`.

### Stage 1 — Scene description → image (C+S+U, ~10 min) → Approval 1
**1.0 Ask for the scene description (Claude, always the first step of a job).** Ask the user, in one short message, for:
1. **The scene** in their own words (place, time of day, weather, mood, colours, main objects). A reference image is welcome.
2. **What should move, glow or float** (rain, fireflies, waterfall, steam, mist, flames…), and anything that must stay still.
3. **The sound:** music mood and the ambience (rain, water, fire, wind, none).
4. **A short name** for the folder (`Video-<Shortname><n>`), if they have one; otherwise Claude proposes it.
If the reply is only a line, Claude does not stop: it expands the line into a **scene brief** (5–8 lines: setting, light, colours, the moving elements by zone, the sound) and shows it for a quick "yes / change X" before writing prompts. Nothing is generated until the user has given a description; Claude never invents the scene by itself. Keep the user's words: put the description in `jobs/<id>/scene.md` and reuse it in the run log.

**1.1 Plan the scene for animation** (Claude, before writing the prompt):
- **Frame:** a static, eye-level view, usually **from inside looking out** through a large opening (window wall, shoji, veranda). A rigid frame helps but is **not required** (§1.4): a looser scene is fine if you plan the stabilize fallback. A full-frame outdoor scene with no rigid frame drifted 6–17 px per clip on every seed (Lessons A12), so budget for stabilizing it.
- **5–7 moving elements spread over ≥ 3 zones of the frame** (§1.4), from the proven list first (snow, fire/flame, steam; §7), then the unverified ones (rain, mist/clouds, curtains, glass droplets, twinkling lights). Put a moving element in each of the left, right, foreground and background where the scene allows. Prefer **soft backgrounds** behind each one and keep them off foreground objects.
- **Generate candidates from 2 different compositions** when the idea allows (e.g. two viewpoints), so the pick is real.
- **Particles (snow/rain) only outside.** Avoid indoor surfaces that could look like frozen particles (a fluffy blanket near the doorway picked up "snow" specks).
- **No people, animals, text, mirrors/reflections of moving things.** No clutter.
- **Lighting:** warm interior vs cool exterior, dusk/night (the channel's look).

**1.2 Write the image prompt** from the scene description (`jobs/<id>/scene.md`) with template P-IMG (§9) → `jobs/<id>/image_prompt.txt`, and the standard negative → `image_negative.txt`.

**1.3 Generate 4 candidates:** `../scripts/image_candidates.sh <id>` (Z Image Turbo, 1920×1088, ~2–3 min): `work/<id>/candidates/cand1..4_s<seed>.png` and a numbered 2×2 `sheet.png`. Claude screens each (can the moving parts be masked on real edges? anything that would animate wrongly? artifacts like warped shoji grids, extra cups, floating objects, text) and sends the sheet with one line per candidate.

**1.4 Approval 1 (U):** you pick one, or ask for changes → Claude edits the prompt and runs another round with new seeds.

**1.5 Intake:** copy the chosen image to `input/<id>.png`; source size 1920×1088; `plate.crop = [0, 4, 1920, 1084]`; keep `image_prompt.txt`, `image_negative.txt` and the seed.

### Stage 2 — What animates: analysis and masks (C+U, 10–20 min) → Approval 2
1. **Motion inventory.** List every element that could move and how (catalog §7). Anything not listed stays frozen. Write the list in plain words for you: *"Moves: snow falling outside; the fire in the brazier; steam from the cup. Frozen: everything else."*
2. **Regions** (polygons in **source pixels**, in `jobs/<id>/job.json`, schema §8):
   - `animated`: where AI motion is allowed; edges on **real edges** (door/window frames, table edges, silhouettes).
   - `lock`: foreground objects overlapping the animated area that must stay pixel-identical.
   - `qc_only`: small boxes around each effect, for measuring.
3. **Draw the overlay and look at it** (`../scripts/mask_preview.py`; also a 2× zoom of the tricky part). Adjust until edges are right (expect 2–3 adjustments). Save as `jobs/<id>/mask_overlay_v0.png`.
4. **Watch for:** frozen particles in locked areas; steam starting inside a lock region (start the steam box just above the rim); light sources that should flicker.
5. **Approval 2 (U):** Claude sends the overlay picture with the plain-words list. You approve or change it (e.g. "also animate the pond", "don't animate the fire").
- **Gate:** overlay approved; polygons on real edges; every moving thing inside an animated region.

### Stage 3 — Audio sample (S+C+U, ~10 min) → Approval 3
1. Start the ACE-Step server (Runbook §M). Generate **three 30-second samples** in different styles (default trio: low flute + pad, soft piano + faint flute, koto + faint flute), each with an **explicit `--bpm` (~44–48) and `--key`** (the model's own planner ignores "slow"), softened and levelled (Music §Recipe).
2. **Check each sample with `audio_qc.py`** before sending; regenerate any that has harsh events. Send the passing ones to you with a one-line description each.
3. **You** pick one (or say what to change: slower, softer, less reverb, other instrument; a new sample takes ~10 s).
4. Add the ambience 14 dB under the music; send a mixed 30 s plus an ambience-only louder version. **Approval 3 (U):** level and character of the ambience.
- Claude cannot hear: it reports measurements (LUFS, tempo, key, check results) and your verdict decides.
- Record the approved prompt, BPM range and keys in `jobs/<id>/music.md` (used by stage 8).

*Phase 1 is now complete. Nothing after this needs you until the final review.*

### Stage 4 — Video prompt (C, 5 min) → `jobs/<id>/prompts.md`
Use template P5 (§9). Fill `{FROZEN}`, `{MOTION}`, `{MOOD}` from the approved plan. Only name what moves, with direction and speed.

### Stage 5 — Drift probe (S+C, ~10 min)
For seeds 101, 202, 303 render a 121-frame clip at 1024×576 and measure:
- `qc_drift.py` → **worst drift ≤ 0.7 px** (good seeds gave 0.1 px). **Its ROI must be the job's `lock` regions** (things that must not move), never areas with rain, bamboo, steam or fire, or it measures the effect instead of the camera (Lessons A14). Report drift per frame: it usually grows over the clip.
- `qc_motion.py` → the effects really move: snow **moving down ≥ 65 %**, steam **moving up ≥ 60 %**, flicker/fire **activity > 0**. Edit its region table for the new image (Runbook §Q).
- Contact sheets of the full frame and each effect; Claude looks at them.
- **Gate:** ≥ 2 seeds pass. If < 2: change the prompt using §10 (max 4 rounds), rerun. If still failing: §10 "fallback".
- **If all 3 seeds fail by a wide margin (> 5 px) the cause is systematic (the scene primes a camera move; Lessons A12), not seed luck.** Do one prompt round (remove camera words, Lessons A13), build the stabilize fallback in parallel, and only then try more seeds.

### Stage 6 — Two clips (S, ~6 min)
Render clip **A** and clip **B**: 145 frames each, two best seeds, same prompt.

### Stage 7 — Loop build and QC (S+C+U, ~2 min) → Review 1
`loop_build.py` builds the 240-frame loop: `[0,24)` B's tail fades into A's head; `[24,120)` A; `[120,144)` A fades into B; `[144,240)` B. AI pixels only inside the feathered animated mask, over the original plate at 1080p; locked pixels stay identical.
- **Gates:** `seam_ratio ≤ 1.3` · `locked_pixels_identical = true` · `luma_std_detrended ≤ 1.0` · `luma_max_jump ≤ 1.5`.
- Claude looks at the seam sheet (frames 232–239 then 0–7) and one full-size frame.
- **Review 1 (U):** you watch the loop repeating: loop point visible? effects right?

### Stage 7b — 4K master (optional, S+C+U, ~10–15 min) → after Review 1 **[UNVERIFIED]**
**Do the video at 1080p first; make 4K at the end from the approved loop.** Generating the AI clips at 4K is not worth it: LTX would need about 14× the pixels of 1024×576 (memory and time), the 201-frame request cap still applies, and Draw Things sizes must be multiples of 64 (2160 is not; 2176 is). The 4K step is cheap because it works on **one 10-second loop (240 frames)**, and the hour is made by repeating that loop, so the hour is never upscaled.
1. **Start from the approved 1080p loop** (`loop_frames/f0001..f0240.png` from stage 7). Do not rebuild the loop; the seam and the locked pixels were already verified.
2. **Upscale each frame to 3840×2160.** Default: `ffmpeg` Lanczos with a light sharpen (no new tools). Better, if available: an AI upscaler on the frames (LTX spatial upscaler x2 in Draw Things, or another image upscaler; whether `draw-things-cli` can drive it is **[UNVERIFIED]**; any Draw Things route must use 3840×2176 and crop to 2160). Optional quality step: upscale the still plate once (one image) and re-composite the animated layer over it, so the locked areas are truly sharp at 4K; watch the mask edge for a soft seam and raise `feather_px` if you see one.
3. **Encode the 4K loop** with a closed GOP and a keyframe every 240 frames (`-g 240 -keyint_min 240 -sc_threshold 0`), 24 fps, `yuv420p`. It must stream-copy cleanly 360 times like the 1080p loop.
4. **Gates:** exactly 240 frames · 3840×2160 · downscaling the 4K loop back to 1920×1080 matches the approved 1080p loop (mean PSNR ≥ 35 dB, no visible change) · `seam_ratio ≤ 1.3` re-measured on the 4K loop · locked areas unchanged after the round trip · after the mux, video packets **86,400** and duration **3600.000 s**.
5. Claude looks at three full-size 4K **crops** (an animated region, a locked region, a mask edge) and the seam sheet, and reports the file size of the 4K hour before you upload.
6. **Review 1b (U):** watch the 4K loop repeating (same questions as Review 1 plus: any soft halo, ringing, or shimmering at the mask edge?). If it is not better than 1080p, skip 4K and deliver the 1080p file.
Cost: more disk and upload time; YouTube processing takes longer. The 1080p file is always kept.

### Stage 8 — Full hour of audio, checked for softness (S+C+U, ~20 min) → Review 2
`music_build.py --minutes 60` (with the approved prompt/BPMs/keys) does, per piece: generate → soften → **check with `audio_qc.py`** → if any harsh event, regenerate with a new seed (up to 4 takes; the least-bad take is kept with a warning if all fail). Then it crossfades the pieces, applies the slow leveler, mixes the ambience, fades, writes the AAC and **checks the finished hour again**.
- **What "soft" means here (checked, not assumed):** no screech/whistle (sustained high-pitched tone), no harsh brightness, no scratch/static, no crackle/glitch bursts, no clicks/pops, no clipping, no dropouts. Sudden loud notes are reported as warnings.
- **Gates:** `audio_qc` on the final mix: **harsh events = 0**; duration 3600.000 s; ≈ −22.5 LUFS; peak ≤ 0.89; no 3-second near-silent stretch; 10-second loudness std ≤ ~3 dB.
- If the final check still finds events: cut them out by regenerating the affected pieces (`work/.../pieceNN*.flac` → delete, rerun; the build is resumable) and check again.
- **Listening pack (U):** the script writes `<out>_qc/listening_pack.mp3` — 6 riskiest moments (spread through the hour) + 3 random spots, ~72 s — and `listening_pack.txt` with the timestamps. Claude sends it. **Review 2 (U):** you listen and confirm it is pleasant throughout; if any moment bothers you, tell Claude the pack number and the piece is regenerated.

### Stage 9 — Mux, deliver, clean up, document (C, ~10 min)
1. Mux the audio onto 360 loops (stream copy) → `<id>_1hr_1080p24.mp4`; if stage 7b was done, also → `<id>_1hr_4k24.mp4` from the 4K loop. Verify each: 3600.000 s, 86,400 video packets.
2. Rename to the three final names (§1.2); delete everything else under `output/` and all of `work/`.
3. Fill `RUNLOG.md` (what was done, numbers, verdicts, surprises, and the recipe: image prompt + seed, video prompt, seeds, music settings); add anything new to [Lessons](lessons.md).
4. `../.venv/bin/python ../scripts/build_docs.py` (from `Project-V/`) to rebuild `wiki/html/` (master docs) and this video's own page `Video-<Name>/RUNLOG.html` (run log + QC report). **The per-video page stays in its video folder; it is not part of the master site.**
5. Commit and push the repo (small files only; videos are git-ignored).
6. Tell you the file paths and remind you of the YouTube steps (§11).

---

## 7. Motion catalog

Proven so far: snow, fire, steam. Others are expectations only.

| Effect | Prompt phrase (`{MOTION}`) | Direction / speed | Measure | Status |
|---|---|---|---|---|
| Snow | "tiny snowflakes falling gently downward outside" | down, slow | `moving_down ≥ 65 %` | **Proven** (97–98 %) |
| Fire / candle / lantern flame | "the small brazier flame flickering" | in place, irregular | luma std over time > 0 | **Proven** |
| Steam from a cup | "thin steam curling up from the tea cup" | up, thin | `moving_up ≥ 60 %` | **Proven** (92–94 %) |
| Rain | "fine rain falling straight down" | down | as snow | [UNVERIFIED] (also needs rain ambience) |
| Smoke / incense | "a thin thread of smoke rising and curling" | up | as steam | [UNVERIFIED] |
| Fog / mist | "slow drifting mist" | sideways, very slow | flow magnitude | [UNVERIFIED] |
| Falling leaves / petals | "a few leaves drifting slowly down" | down, sparse | as snow | [UNVERIFIED] |
| Water ripples | "gentle ripples on the water" | local | frame diff | [UNVERIFIED] |

Rules: aim for 5–7 moving things in ≥ 3 zones (§1.4), but every one needs a region and a plain-words line in the approved motion list; describe direction and speed; never "wind/gust" unless intended. If the prompt gets long, the 3-seed probe decides how many effects the model can carry; drop the weakest and record it in Lessons.

---

## 8. `job.json` schema
```json
{
  "id": "Video-Zen3",
  "source": "input/Video-Zen3.png",
  "source_size": [1920, 1088],
  "plate": { "crop": [0, 4, 1920, 1084], "output_size": [1920, 1080] },
  "loop":  { "period_s": 10.0, "fps": 24, "crossfade_s": 1.0 },
  "regions": {
    "exterior": { "role": "animated", "poly": [[x,y], ...], "feather_px": 4 },
    "steam":    { "role": "animated", "poly": [[x,y], ...], "feather_px": 8 },
    "lock_table": { "role": "lock", "poly": [[x,y], ...] },
    "fire_qc":  { "role": "qc_only", "poly": [[x,y], ...] }
  }
}
```
Polygons are in **source pixels**. `loop_build.py` requires a region named `exterior` (main animated area). Working example: the `jobs/<id>/job.json` of any earlier video.

---

## 9. Prompt templates

**P-IMG — image (Z Image Turbo; the user's own style, recovered from their Draw Things project):**
```
{SETTING at TIME}, view through {OPENING} onto {EXTERIOR}, {WEATHER outside}, {FOREGROUND anchor: low table / kotatsu / engawa} with {STEAM SOURCE: steaming cup of tea / tetsubin kettle}, {WARM LIGHT: paper lantern / andon / irori hearth glow}, {EXTERIOR DETAILS: stone lantern, pine, moss, pond}, {FIRE if any: small fire in an iron brazier in the background}, contrast between warm interior light and cool {blue/green} exterior, cinematic lighting, shallow depth of field, photorealistic, highly detailed, atmospheric, tranquil, zen aesthetic, 8k, professional photography
```
Example (a snowy tea-room look): *"cozy Japanese tatami room at dusk, view through open shoji screen doors onto a snow-covered zen garden, gentle snowfall outside, warm kotatsu table in foreground with a thick quilted blanket draped over it, steaming cup of hojicha tea resting on the kotatsu, soft irori hearth glow casting warm amber light across the tatami mats, paper lanterns glowing softly, snow-dusted pine tree and stone lantern visible through the doorway, contrast between warm interior firelight and cool blue snowy exterior, intimate and inviting atmosphere, cinematic lighting, shallow depth of field, photorealistic, highly detailed, atmospheric, tranquil, zen aesthetic, 8k, professional photography"*

**Image negative:**
```
people, text, watermark, logo, blurry, low quality, oversaturated, daytime, harsh lighting, cartoon, illustration, deformed, extra objects, cluttered, Chinese architecture, animals, snow indoors, reflections, mirrors
```
(Drop "daytime" for dawn/day scenes.)

**P5 — strict cinemagraph (video, the one that works):**
```
Cinemagraph loop. One single locked photograph on a tripod: the framing is identical in every frame, {FROZEN} stay pixel-still. The only motion in the entire image is {MOTION}. Photorealistic, calm, {MOOD}.
```
First video: `{FROZEN}` = "the doorway, table, cup, blanket, lamp, lanterns and trees"; `{MOTION}` = "tiny snowflakes falling gently downward outside, the small brazier flame flickering in the garden, and thin steam curling up from the tea cup"; `{MOOD}` = "cozy winter night".

**Do not write** "the camera does not move / never zooms" (made drift *worse*: 20–25 % zoom), long descriptive scene text (15 % zoom), or rely on the negative prompt (ignored at CFG 1).

**Music prompt (approved on an earlier run):** *"Very slow, soft, gentle ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, a faint distant low flute and a warm airy pad far in the background. Peaceful, calm, tender, sleepy, {SCENE}. no drums, no percussion, no vocals, no sharp sounds."* with `--bpm 44` and a key.

---

## 10. When something fails (decision table)

| Symptom | Likely cause | Do this |
|---|---|---|
| Camera zooms or shifts (drift > 0.7 px) | Prompt primes camera motion (incl. "tripod", "framing", "locked"); open outdoor scene with mist and no rigid frame; seed | Use P5; remove all camera words; fewer moving things. **If all 3 seeds fail by a wide margin, do not just add seeds** (systematic; Lessons A12). **Fallback [UNVERIFIED]:** stabilize each frame to frame 0 with a similarity transform fitted on **locked-region** features only, replicated border, re-measure (Lessons A15) |
| Drift metric moves with the rain or leaves | ROI contains animated things (hardcoded strips from the first job) | Set the ROI to the `lock` regions; measure 2–3 separate locked objects and check they agree (Lessons A14) |
| Only 1 of 3 seeds passes | Normal | Try seeds 404, 505; use passing seeds for A and B; re-check drift on the built loop |
| Effect too weak/absent | Too many things in the prompt | Put the weak effect first; "clearly visible"; last resort a close-up region clip **[UNVERIFIED]** |
| Snow moves up or sideways | Model artifact | "falling straight down"; other seed |
| Visible seam at mask edge | Polygon not on a real edge | Redraw on the edge; `feather_px` 4 → 8 |
| Seam ratio > 1.3 | Big change between A's tail and B's head | Different seed for B; `crossfade_s` 1.5 |
| Brightness pulsing | Exposure drift | Different seed; check `luma_std_detrended` |
| Draw Things HTTP 422 | Full config dump / size not multiple of 64 / frames > 201 | Whitelisted keys only; check size and frames |
| Music server dies mid-request | 240 s piece crashes VAE decode | 150 s pieces; `music_build.py` restarts and retries |
| Music downloading to the wrong disk | `.env` path ignored | `checkpoints` symlink to the SSD |
| Music "too harsh / too fast" | Planner picked 91–120 BPM; bright top end | `--bpm` and `--key`; low-pass; "warm, low, rounded" |
| `audio_qc` keeps failing a piece | Prompt invites bright sounds | Remove "flute"/"bells"; add "muted, low register, soft"; lower the low-pass to 5.5 kHz (`--filters`) |
| Out of memory / slow | Two heavy models loaded | Quit the Draw Things app before CLI; stop the music server before video; `ollama stop <model>` |

**Stop rule:** after 4 failed prompt rounds in stage 5, stop and report the numbers and contact sheets with a recommendation; don't burn more GPU time unattended.

---

## 11. YouTube notes (from web search, 2026-09-23 — check current policy yourself)
- No YouTube feature loops a short video under a longer audio track: upload the one-hour file. 1.1 GB ≈ 8 min at 20 Mbps upload (30 min at 5 Mbps), plus YouTube's processing.
- In YouTube Studio: **Create → Upload videos**, fill title/description, set **altered or synthetic content = Yes**.
- The "inauthentic content" (repetitive / mass-produced) policy is enforced **per channel** and is reported to hit ambient/lo-fi channels often. Vary scenes and music across videos. See [Posting plan](posting-plan.md).
- The music is generated locally with an MIT-licensed model; no third-party tracks are used.

---

## 12. Budget (reference-run actuals, M5 Max 64 GB)

| Item | Machine time |
|---|---|
| Image: 4 candidates | ~2–3 min |
| Audio samples (3 styles + ambience) | ~2 min |
| Drift probes (3 × 121 frames @ 1024×576) | ~8 min |
| Clips A + B (2 × 145 frames) | ~6 min |
| Loop build + QC | ~1 min |
| Full hour of audio (26 pieces + checks/retakes + ambience + mix + AAC + final check) | ~20 min |
| Mux | seconds |
| **Total (happy path)** | **~40–45 min**, plus your approvals (~15 min) and reviews (~20 min) |

First-run extras (already done): ACE-Step model download 9.6 GB (~12 min).

---

## 13. Known limits and next improvements (not done)
1. **Job-specific bits in scripts:** `qc_motion.py` region table and `qc_drift.py` mask areas are for the reference run; ambience only makes fire/wind/crackle. Best next step: read all of it from `job.json`.
2. **CLI for video** is required by you but **[UNVERIFIED]** (stage 0).
3. **No single orchestrator** (`pipeline.py`); stages are run one by one from the Runbook.
4. **Other ambience types** (rain, waves, forest, insects) need new synthesizers.
5. **Other lengths** (30 min, 3 h, 10 h): change `--minutes` and `-stream_loop`; not run.
6. **Audio check limits** were calibrated on one hour of one video; if it flags too much or misses something you hear, tune `LIMITS` in `scripts/audio_qc.py` using the excerpts and record the change in Lessons.
7. **Wan 2.2 I2V** isn't installed (only T2V); LTX-2.3 was enough.
8. **4K (stage 7b)** is designed, not run: whether the LTX x2 spatial upscaler works through `draw-things-cli`, the best upscale method, the 4K file size and whether it looks better on YouTube than the 1080p file are all open. Record the results in Lessons.
