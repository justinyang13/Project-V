# Run log — 001-snow-tea

| | |
|---|---|
| Source | `input/001-snow-tea.webp` (1728×960, WebP) |
| Job | `jobs/001-snow-tea/job.json`, `jobs/001-snow-tea/prompts.md` |
| Target | 10 s, 1920×1080, 24 fps, seamless loop; snow falls, fire flickers, tea steams |
| Status | **DONE (2026-09-23)** — loop approved by you. Files in `output/001-snow-tea/`; report in `output/001-snow-tea/qc_report.md`. |

Legend: ✅ done · ⏳ pending · ❌ failed · ↩ redone

---

## Step 0 — Requirements and decisions ✅ (2026-09-23)

What you asked for: animate snow, the fire (realistic even though it's blurred), and the tea steam. About 10 s, loopable with an invisible seam. Draw Things local models (Wan, LTX). Check quality and iterate.

Decisions from Q&A:
| Question | Answer |
|---|---|
| Scope of this pass | Plan docs + prompts only. You run execution later with the kickoff prompt. |
| Draw Things access | HTTP API server |
| Models available | Wan 2.2 I2V A14B, LTX-2 |
| Output | YouTube ambient loop: 10 s master at 1080p24, later looped to hours; no audio |

Decisions Claude made (see SPEC §3 for why):
- Hybrid pipeline: AI video only inside masks; the room is locked to the source pixels.
- Loop by crossfade (1 s) of a ≥ 11 s continuous clip, not first/last-frame conditioning.
- Round 1 A/B tests Wan 2.2 A14B against LTX-2 before committing.
- Final format 24 fps (LTX native; Wan interpolated with RIFE).

**Validate:** Read SPEC §1–3 and check it matches what you want.

Decision added later (2026-09-23): **local-first execution.** Local LLMs (Ollama/OpenCode) and scripts do as much as possible to save Claude tokens; Claude decides only what's listed in SPEC §12.2. Local models found on the machine: `qwen3-coder:30b` (scripts), `qwen3.5:35B` and `qwen3.8:27b` (vision, for QC scoring), `gpt-oss:120b` (65 GB, excluded because of memory). OpenCode was already configured for Ollama. The Draw Things API server was off when checked.

## Step 1 — Image analysis and masks v0 ✅ (2026-09-23)

What was done:
1. Copied the image to `input/001-snow-tea.webp` and confirmed it's 1728×960.
2. Drew candidate boxes over a 100 px grid to locate the doorway, fire, steam, cup, and lamp.
3. Built polygon masks with Pillow and checked them on a full overlay plus a 2× zoom of the cup, table, and blanket. Adjusted twice:
   - Moved the blanket/table lock up 6 px so the blanket fuzz is locked.
   - Moved the cup lock up to the rim (y = 616) so the rim can't warp. Steam starts just above it.

Result: `jobs/001-snow-tea/mask_overlay_v0.png` (cyan = animated; orange = table/blanket lock; magenta = cup lock; yellow = steam box; red = fire QC box).

| Region | Source px | Note |
|---|---|---|
| exterior (animated) | x 318–1200, y 0–712 | Edges sit exactly on the shoji frames and sill |
| steam (animated) | x 975–1110, y 380–620 | Covers the tallest wisp (~445) with headroom |
| lock_table_blanket | polygon, y ≥ 636–712 | Blanket top ~643, table back edge ~642 |
| lock_cup | x 958–1118, y 616–706 | Cup, handle, saucer |
| fire_qc | x 1105–1195, y 295–405 | Flame at ~(1145, 350) |

Observations:
- The still has frozen "snow" specks on the blanket and the floor to the right. They're locked, so they won't animate.
- The garden is shallow-focus, so 720p AI output upscaled to 1080p will be acceptable there. The room stays at source resolution.

**Validate:** Open `mask_overlay_v0.png`. Does cyan stop exactly at the door frames and the table and blanket edges?

## Step 2 — Prompts v1 ✅ (2026-09-23)

Written in `jobs/001-snow-tea/prompts.md`: P1 (Wan 2.2), P2 (LTX-2), shared negatives, a symptom → knob table, and fallback region-pass prompts for fire and steam.

**Validate:** Read P1/P2. Is the motion described the way you picture it (snow speed, steam thickness)?

---

## Step 3 — Stage 0: environment and DT API probe ✅ (2026-09-23)

Your answers: downloads OK if a model isn't already on disk; 24 fps OK; RIFE OK if needed (not needed: LTX-2.3 only). Models now live flat in `/Volumes/SSD-4T-LR/AI/Models` (see `wiki/models.md`).

What was done and learned:
- `.venv` created (Python 3.14; numpy, opencv-python-headless, pillow, requests).
- **DT API:** `GET http://127.0.0.1:7860/` returns the app's current config. Image-to-video is `POST /sdapi/v1/img2img` with JSON: config keys + `prompt`, `negative_prompt`, `init_images: [base64 PNG]`. Response: `{"images": ["<base64 PNG>", ...]}`, one entry per frame.
- **Gotcha 1:** posting the full config that `GET /` returns fails with HTTP 422 (fields like `original_width: 0`, `tea_cache_end: -1`, and several duplicate-key errors such as "More than one key for Compression Artifacts"). **Send a minimal whitelist instead:** model, steps, guidance_scale, sampler, shift, strength, seed, start_frame_guidance, guidance_embed, resolution_dependent_shift, speed_up_with_guidance_embed, width, height, num_frames, prompt, negative_prompt, init_images (see `scripts/dt_probe.py`). This worked first try.
- **Gotcha 2:** the model is selected by the `model` key in the request, so the app's current selection doesn't matter (the app was on LTX-2 19B; the request asked for LTX-2.3 22B and got it).
- **Gotcha 3:** output size is **rounded down to a multiple of 64**. I asked for 640×352 and got 640×320, which squashed the picture. Use sizes that are multiples of 64: **1024×576** is exactly 16:9.
- **Probe result** (LTX-2.3 22B distilled, 8 steps, 640×320, 25 frames, first call incl. model load): **102 s**, HTTP 200, 25 frames. Contact sheet `work/probe/sheet.png`: image follows the source well; snow and steam visible; brazier glow present. Not yet judged for loop quality (only 1 s long).

Decision: LTX-2.3 only for job 001 (no Wan I2V installed, no RIFE).

## Step 4 — Stage 1: DT base configs ⏳
- LTX 2.3: done (`jobs/_dt_base/ltx2_i2v.json`; only the whitelisted keys are sent, see Step 3).
- Wan: skipped (see Step 3).

## Step 5 — Round 1: drafts, camera-drift fix ↩ (2026-09-23)

Model: **LTX-2.3 22B distilled** only (Wan I2V not installed). Draft = 1024×576, 8 steps, seeds as listed. Render times: 73 frames ≈ 2 min, 121 frames ≈ 2.5–3 min. Metrics from `scripts/qc_drift.py` (camera zoom/shift of the room, features tracked on shoji/lamp areas; limit ≤ 0.7 px) and `scripts/qc_motion.py` (motion in snow/steam/fire regions).

| Clip | Prompt | Frames | Camera drift | Verdict |
|---|---|---|---|---|
| ltx_s101 | P2 (long descriptive) | 121 | zoom +15 %, shift 124 px | ❌ camera pushes in |
| p3_s101 / s202 | P3 ("never zooms, never pushes in") | 73 | zoom +20 % / +25 %, 96–133 px | ❌ worse: naming the camera move primes it |
| p3_cfg2_s101 | P3 + guidance_scale 2 | 73 | identical to p3_s101 | the guidance override had no effect |
| p4_s101 | P4 (cinemagraph) | 73 | +2 %, 11 px | ❌ better, not enough |
| p4_s202 / s303 | P4 | 121 | +11 % / +12 % | ❌ seed-dependent |
| **p5_s101** | **P5 (strict cinemagraph)** | 121 | **0.1 px** | ✅ |
| **p5_s202** | P5 | 121 | **0.1 px** | ✅ |
| p5_s303 | P5 | 121 | ~1.1 px shift, luma std 2.1 | ⚠ borderline |

P5 motion (p5_s101): snow moves down 98 % of moving pixels; steam rises 92 %; fire changes shape frame to frame with a warm glow. Sheets: `work/001-snow-tea/r01/p5_s101/sheet_{full,steam,fire}.png`. Fire has a few faint smoky wisps at the lower left in late frames (to watch).

Lessons:
- **Never write "camera does not zoom/push in" for LTX-2.3.** Describe a still photograph ("cinemagraph … framing identical in every frame … pixel-still") and list only what moves.
- Distilled model at CFG 1 ignores the negative prompt.
- Drift is seed-dependent: always measure it, don't trust one seed.
- **Draw Things caps one request at 201 frames** (8.4 s at 24 fps); asking for 265 gives HTTP 422 "Number of Frames must be between 1 and 201". A ≥ 11 s single clip is impossible, so the loop is built from two clips (Step 6 plan).
- Mistake to avoid: probing the frame limit with a valid number (201) starts a real render that can't be cancelled from the API. Probe with an invalid number, or accept the wait.

Decision: hero prompt = P5, LTX-2.3.

## Step 6 — Round 2: full loop (r02) ✅ APPROVED (2026-09-23)

Method: two clips from the same still, P5 prompt, LTX-2.3, 1024×576, 145 frames each (seeds 101 and 202; 163 s and 189 s to render). `scripts/loop_build.py` builds a 240-frame (10.0 s @ 24 fps) loop: A → 1 s crossfade → B → 1 s crossfade → A. AI pixels are used only inside the animated mask (doorway/garden + steam); the room, table, cup, blanket and lamp are the original image at 1920×1080. Output: `output/001-snow-tea/r02/001-snow-tea_loop10s_1080p24.mp4` (+ `_preview60s.mp4`, `sheet_seam.png`, `qc_final.json`).

| Check | Result | Limit |
|---|---|---|
| Seam ratio (frame 239→0 vs typical frame step) | 0.97 | ≤ 1.3 ✅ |
| Locked pixels identical to source (4 frames checked) | true | ✅ |
| Largest brightness jump | 0.48 | ≤ 1.5 ✅ |
| Camera drift of both clips | 0.1 px | ≤ 0.7 ✅ |
| Snow down / steam up | 97–98 % / 92–94 % | ≥ 65 % / ≥ 60 % ✅ |
| Brightness steadiness (`luma_std_detrended`) | first reported 10.1 = my metric bug (moving average edge effect); fixed to a circular average → **0.16** | ≤ 1.0 ✅ |

Visual check by Claude (frame 60 at full size + seam sheet frames 232→7): room identical to source, no visible mask edges at the shoji frames, snow and steam present, seam frames look continuous. Not yet verified: how the motion looks in playback (Claude can't watch video).

**Your review:** (1) loop point visible? **No.** (2) fire natural? **Yes.** (3) steam thin and attached? **Yes.** (4) snow speed/density right? **Yes.** → approved.

## Step 7 — Iterations ✅
Camera-drift fix took 4 prompt rounds (Step 5). Nothing further needed after r02; no more iterations.

## Step 8 — Delivery and sign-off ✅ (2026-09-23)
- [x] `output/001-snow-tea/001-snow-tea_loop10s_1080p24.mp4` (verified 240 frames, 10.000 s)
- [x] `output/001-snow-tea/001-snow-tea_loop10s_1080p24_prores422hq.mov`
- [x] `output/001-snow-tea/001-snow-tea_preview60s.mp4` — you watched it; loop point not visible
- [x] `output/001-snow-tea/qc_report.md`

Total generation time for the winning recipe: about 6 minutes of GPU (2 × ~3 min). Total including all failed tests: about 50 minutes.

## Step 9 — Music, ambience and the 1-hour video ✅ built (2026-09-23), awaiting your listen
- Style chosen by you after A/B of 3 clips: soft piano (v3b), then ambience approved. Method and lessons: `wiki/music.md`.
- Output: `output/001-snow-tea/001-snow-tea_1hr.mp4` (1.1 GB, 3600.000 s, 1080p24, AAC 256 kbps), plus `music_60min.m4a` / `.wav`.
- Checks: 86,400 video frames = exactly 24×3600; audio ≈ −22.5 LUFS, peak 0.67, no near-silent stretches; slow leveler reduced loudness swings (std 3.8 → 2.7 dB).
- Excerpts to listen to: `output/music/full_excerpt_first_join.mp3` (a crossfade between pieces), `full_excerpt_midpoint.mp3`, `full_excerpt_video_first_join.mp4`.
- Note: the earlier version (before the leveler) is in `work/old_v1/` and can be deleted.

## Step 10 — Clean-up, generic spec, docs, GitHub (2026-09-23)
- Kept only the three final files in `output/001-snow-tea/` (renamed): `001-snow-tea_1hr_1080p24.mp4`, `001-snow-tea_audio_60min.m4a`, `001-snow-tea_loop10s_1080p24_silent.mp4`. Deleted ProRes master, previews, frames, sample audio, and the whole `work/` scratch folder (3.8 GB). File names in earlier steps above refer to the pre-cleanup names.
- Rewrote `SPEC.md` as a generic image-to-1-hour spec (v2); old job-specific spec archived in `wiki/archive/`. New `wiki/runbook.md`, `wiki/lessons.md`; `scripts/mask_preview.py` and `scripts/build_docs.py` added; HTML docs in `docs/` (open `docs/index.html`).
- User decisions: docs only (scripts not generalized, CLI not yet tested); new private GitHub repo.

## Lessons for the playbook
Copied into `wiki/README.md` → Gotchas and Recipe.
