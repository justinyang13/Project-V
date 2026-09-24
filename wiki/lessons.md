# Lessons — what went wrong, why, and the rule that came out of it

Read this before starting a new job. Each row is something that actually happened in earlier jobs. Add new rows at the bottom of the right table.

## A. Video generation

| # | What happened | Cause | Rule |
|---|---|---|---|
| A1 | First draft: the camera zoomed in 15 % and shifted 124 px in 5 s | Long descriptive prompt (P2) | Measure drift on every probe (`qc_drift.py`). Never accept a clip without it |
| A2 | Wording "the camera never zooms / pushes in" gave 20–25 % zoom (worse) | Naming a camera move primes it | Never mention the camera. Use the **cinemagraph** prompt (SPEC §8) |
| A3 | Cinemagraph wording (P4) cut drift 10× but 2 of 3 seeds still drifted 65–89 px | Seed dependence | Add "one single locked photograph … pixel-still" (P5): 0.1 px on 2 of 3 seeds. Always test 3 seeds |
| A4 | `guidance_scale=2` gave a byte-identical result; the negative prompt did nothing | The model is distilled and runs at CFG 1 | Put everything in the positive prompt; don't spend time on negatives/CFG |
| A5 | A 265-frame (11 s) request failed with HTTP 422 | Draw Things caps a request at **201 frames** | Build the loop from two 145-frame clips (A → B → A) instead of one long clip |
| A6 | HTTP 422 with the full config dump ("More than one key for Compression Artifacts", `original_width` 0, `tea_cache_end` −1) | The API rejects some fields it returns itself | Send a **whitelist** of keys only (`dt_generate.py`) |
| A7 | 640×352 came back 640×320, squashed | Sizes are rounded down to multiples of **64** | Use multiples of 64 (1024×576 is 16:9) |
| A8 | Probing the frame limit with a *valid* number (201) started a real render that can't be cancelled | The API has no cancel | Probe limits with an *invalid* value, or accept the wait |
| A9 | A render finished but the machine sat idle for a while | A watcher script was waiting on a job that had failed | Chain steps in one background script (`until grep -q DONE log; …`) and check the log for failures; never leave a queued step depending on a step that may have failed |
| A10 | Wan 2.2 in Draw Things looked like a video model but couldn't animate the still | The installed model was the **T2V** (text-to-video) expert | For image-to-video you need an **I2V** model. LTX-2.3 accepts an input image |
| A17 | Draw Things **projects** can't be created with the CLI | Projects are an app feature (history/canvas files); the CLI only writes files | The video folder is the project (prompts, seeds, chosen image, log). Create a project in the app by hand only if you want to browse there |
| A11 | Draw Things CLI for **images** works (Z Image Turbo, 1920×1088, 8 steps, ~30 s/image after an ~50 s first load; the app doesn't need to be open). **Video** via CLI still untested | — | User rule: use the CLI so closing the app doesn't matter. Validate video in stage 0 (SPEC §5) and record the outcome here |
| A12 | Job 002 (zen garden: bamboo, torii, pond, rain): drift **6–17 px, growing steadily over the clip (~0.3 px at frame 20, ~10 px by frame 140), on all 3 seeds** (101/202/303) even though job 001's seeds gave 0.1 px | A full-frame outdoor scene with fog and no rigid frame (no shoji/window) reads to the model as a camera move; it is systematic, not seed luck | If **all 3 seeds** fail by a wide margin, don't keep adding seeds. Change the prompt once (A13) and go to the stabilize fallback (A15). Only try 404/505 after that |
| A13 | The job-002 prompt said "one single locked photograph on a **tripod**: the **framing** is identical" | Tripod / framing / locked are camera words; they prime camera ideas (same effect as A2) | Say what is frozen (objects by name) and list the only things that move. No "tripod", "framing", "locked", "camera", "steady" |
| A14 | `qc_drift.py` still measured the job-001 "room" strips (left 18 %, right 32 %), which on job 002 are bamboo and rain (moving) | Hardcoded ROI. I re-measured on the locked objects (lantern, bridge+table, torii) and got the same or bigger numbers, so the gate result was right, but only by luck | **Always set the ROI to the job's `lock` regions**, never to areas that contain animated things. Best: make `qc_drift.py` read the ROI from `job.json`. Check ROI first: if the metric moves with the effect (rain/bamboo), it is measuring the effect, not the camera |
| A15 | Stabilize fallback (SPEC §10) for slow linear drift | Composite puts AI pixels over the locked plate; drift makes the animated region slide against the plate and shows a seam at the mask edge | `stabilize.py`: per frame, ORB features on the **locked** regions only (not bamboo, rain, steam) → `estimateAffinePartial2D` (RANSAC 1.5 px) → warp frame to frame 0 with replicated border. Re-run `qc_drift.py` on the stabilized frames. **[UNVERIFIED on job 002 — record the outcome here]** |
| A16 | Steam over the tea bowl moved in the job-002 clips though the prompt never asked for it | Model adds plausible motion to steam/smoke already in the image | Make sure the steam is inside a `lock` region (or that it is what you want animated); check the contact sheet for motion you did not list |

## B. Compositing and QC

| # | What happened | Cause | Rule |
|---|---|---|---|
| B1 | Frozen "snow" specks on the blanket in the original image | The still itself contains particles | Lock those areas (they can never animate) |
| B2 | Steam box overlapped the cup rim | Steam starts at the rim | Start the steam box just above the rim; lock the cup |
| B3 | A brightness-steadiness metric reported 10.1 (fail) | My moving average had edge effects | Use a circular average (fixed); the real value was 0.16 |
| B4 | `qc_motion.py` crashed (`calcOpticalFlowFarneback` missing `flags`) | OpenCV 5 needs the extra argument | Pass `flags=0` |
| B5 | I can't see motion or hear audio | Limitation of Claude | Use numbers + contact sheets + the user's sign-offs; never claim "sounds/looks good" without them |

## C. Models, disk and access

| # | What happened | Cause | Rule |
|---|---|---|---|
| C1 | Couldn't read Draw Things' model folder ("Operation not permitted") | macOS sandbox protection | Grant the Claude app **Full Disk Access** (one time); can be revoked afterwards |
| C2 | Same model files in two places (Draw Things container + SSD) | No single source | One **flat** folder `/Volumes/SSD-4T-LR/AI/Models`; Draw Things External Model Folder points at it. SSD is exFAT, so no symlinks between models |
| C3 | Deleting a model file Draw Things had open | — | Quit the app first; verify each file exists on the SSD with an identical byte size before deleting |
| C4 | ACE-Step downloaded its weights into the project folder (Mac disk) although `.env` said SSD | `.env` path wasn't applied by the server launcher | Make `tools/ACE-Step-1.5/checkpoints` a **symlink** to `/Volumes/SSD-4T-LR/AI/Models/ACE-Step` |
| C5 | Memory: Draw Things app held 32 GB; CLI would load another copy | Two copies of a 26 GB model | Quit the Draw Things app before CLI rendering; never run video model, music model and LLMs together |
| C6 | Model download was slow (2.2 MB/s, 12 min) | Network | First-run only; weights are now on the SSD |

## D. Music and audio

| # | What happened | Cause | Rule |
|---|---|---|---|
| D1 | First flute clip: "too harsh and fast" | Model's planner chose 91–120 BPM, ignoring "slow"; bright solo flute at −14.7 LUFS | Set `--bpm` and `--key` explicitly; describe "warm, low, rounded"; low-pass 6.5 kHz + high-shelf −3 dB; −22 LUFS |
| D2 | A 240 s piece crashed the music server (during VAE decode) | Long decode | 150 s pieces; `music_build.py` restarts the server and retries |
| D3 | Loudness swung from −34.5 to −16.2 dBFS over the hour | Sparse piano with long silences + pieces of different dynamics | Slow leveler (−8…+3 dB over ~20 s); ambience fills natural silences |
| D4 | `loudnorm` error "TP out of range" | Valid true-peak range is −9…0 | Use `TP=-9` or higher |
| D5 | Two of the three "free Japanese music" reference sites didn't load | Certificate error / suspended account | Use references only as style hints; generate locally; nothing downloaded |
| D7 | **The full hour had unpleasant moments** the earlier spot-checks missed: screech/whistle, harsh brightness, scratch/crackle (worst around 10:09, 16:59, 24:54, 25:58, 31:09, 46:14, 52:12, 52:41, 53:24, 53:43, 55:26, 59:26). The user confirmed a 4-clip sample of them was unpleasant "in general, not only screeching" | Two excerpts + loudness statistics can't find a 0.5 s screech in 60 minutes | Check **every** piece and the finished hour with `audio_qc.py` (tone, HF ratio, scratch/flatness, HF bursts, clicks, clipping, dropouts, loud notes); regenerate bad pieces; give the user a **listening pack** of the riskiest + random moments (SPEC stage 8) |
| D8 | Naive limits flagged ~2,000 events (every piano note's harmonics) | Limits set without calibration | Calibrate against moments the user confirms; keep `hf_burst_db` ≥ 40 (note onsets are 20–35 dB) and let only sustained tones (≥ 0.5 s) count as screech |
| D6 | The user preferred piano (v3b) over flute and koto | Taste | Offer three styles in stage 7 and let the user pick; piano + faint flute + pad was the winner |

## D2. Images

| # | What happened | Cause | Rule |
|---|---|---|---|
| I1 | The user's original prompts were recoverable from the Draw Things project database (`Peaceful Images.sqlite3`, read-only copy + `strings`) | Draw Things stores prompts in its project files | Reuse the user's style: template P-IMG and their negative (SPEC §8). Don't write to those files |
| I2 | ffmpeg `drawtext` filter missing | This Homebrew ffmpeg build has no freetype | Draw labels with Pillow |
| I3 | Test candidates varied: one had a fire in the background building, one didn't | Seed | Generate 4 and let the user pick; screen for animatability (SPEC 1.2) |

## F. Process

| # | What happened | Rule |
|---|---|---|
| P1 | Rendering started before the user had confirmed the image, what moves, and the music | **Approve first, render later:** image, animation plan (mask overlay + plain-words list) and audio sample are approved before any long render (SPEC §1.3) |
| P2 | Wiki, scripts and HTML lived inside one video's folder | One folder per video (`Video-<Shortname><n>`); wiki, shared scripts and HTML in `Project-V/wiki/` and `Project-V/scripts/`; one git repo for all |
| P3 | Video-Zen3, round 1: I proposed a rainy window nook where only the glass, the steam and one lamp would move. The user rejected it: only a small part of the picture felt "alive". The first round was also a street-level city view | **Alive everywhere (SPEC §1.4):** 5–7 moving elements in ≥ 3 zones, a large animated area, lock only rigid objects, looser scenes allowed with the stabilizer assumed; cityscapes from a high floor (30+). Do not choose a scene just to keep the animated area small |
| P4 | Only 4 candidates gave too little to choose from once the direction was wrong | When the user rejects the direction, generate **8 candidates from two compositions**, not another 4 of the same |

## E. Working style that worked
- Confirm risky/large actions (moving 71 GB of models; deleting) and verify sizes before deleting.
- Answer the user's confusion directly (e.g., the 40-second excerpt vs the 1-hour file are different files).
- Log every step in the run log as it happens; the wiki is the memory.
