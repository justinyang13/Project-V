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
| A18 | Video-Zen3: the loop showed the **clouds resetting** twice per loop; the numeric gates all passed | A -> B -> A crossfades a clip's drifted state into the other clip's fresh start. Random textures (rain, snow, steam) hide it; **progressive drift (clouds, mist, smoke) does not** | Don't animate progressive-drift effects with the A/B scheme. Options: keep large shapes from the plate + AI high-frequency detail + a loopable procedural sway; or a scrolling two-layer crossfade. Also check pattern correlation across the seams, not just frame difference |
| A19 | Video-Zen3: two 145-frame clips darkened the whole window ~25 % in the last 40 frames; the 121-frame probes looked fine | Exposure drift appears late in the clip | Probe with the **same frame count as the final clips** (145) and check luma over the whole clip |
| A20 | CLI video verified (Video-Zen3): `draw-things-cli generate --image plate --frames 145 --video-format prores422hq` gives exact frame count and size, ~3.5 min per clip after a ~3.5 min first load | — | `scripts/dt_clip_cli.py` replaces the HTTP API path; the Draw Things app is not needed |

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
| D9 | Video-Zen3 and Video-Zen4: the user rejected every procedural rain ambience ("white noise") | `ambience.py` builds rain from synthetic drop ticks and band-limited noise; it never sounds like water | Generate rain with a text-to-audio model. MOSS-SoundEffect (Apache 2.0, 8B + a 7 GB tokenizer, both free, no account) runs on the M5 Max via MPS in bfloat16: 30 s of audio in about 18 s after a 27 s load. Music §Rain has the recipe. Licence check: MMAudio, AudioLDM2 and Tango are non-commercial (CC BY-NC), so avoid them for a monetized channel |
| D10 | MOSS rain clips vary a lot: of 49 clips only 19 passed my checks (loudness swing, sudden event, whistle, brightness) | The model sometimes adds thunder, drips, wind or a different surface | Generate about 50 clips of 30 s and keep the steady ones. Set the rejection limits **from the clip the user approved** (mine first rejected even that clip: swing 5.7 dB, event +11.7 dB, tone x16). Build the hour from random orders, different left and right (correlation 0.000), with 5 s equal-power crossfades and random start offsets. A single 30 s sample the user approves is only a sample: keep its seed and prompt |
| D11 | The rain-only listening pack was approved, but the finished hour was still not right | Approving rain alone says nothing about rain under the piano | Have the user approve the **mixed** pack (piano + rain) at the real level, and give them both a "clear" (about −30 LUFS) and a "subtle" (−36 LUFS) rain. The user chose subtle |
| D12 | "The music keep going quiet ... every 5 seconds" (the finished hour) | Sparse, slow piano ("lots of silence" in the prompt) decays to near-silence between notes: 17 % of 1-second windows were more than 6 dB below the median, 5th percentile −11.7 dB. `slow_level` works over ~20 s and cannot see this | Measure the 1 s envelope on the finished hour, not only 10 s windows. Options, cheapest first: `scripts/upcomp.py` (fast upward compressor: lifts tails, follows a note down fast and up slowly): on a test excerpt B (max +9 dB, ratio 0.8) gave 5 % / −6.2 dB and C (max +12 dB, ratio 0.95) gave 3 % / −4.6 dB; or change the prompt for a steadier pad and more frequent notes. **[UNVERIFIED by ear: the user had not chosen B or C when the project stopped.]** Do this before the full-hour render and let the user hear it |
| D13 | The whole-hour `audio_qc` said FAIL with 901 harsh events after mixing in rain | The limits (flatness ≥ 0.35 = scratch, HF ratio ≥ 0.10) were calibrated on piano only; steady rain is broadband noise and trips them (the rain bed alone gave 2,904 events); it is also brighter than a quiet piano moment | Check three files: the music alone (finished hour, **no ambience**: 3 tiny events), the rain bed alone, and the mix; judge the mix only on the metrics rain cannot trigger (clicks, clipping, HF bursts, whistles, dropouts: all 0 here). Recalibrate `LIMITS` (or skip flatness/HF-ratio) when the ambience is rain. Send the user a pack made from the **real mix** at the flagged moments plus random spots |
| D14 | `music_build.py --amb_wav` refused a 3690 s rain bed for a 3600 s hour | The check compared the bed with the music length (3700 s, 26 pieces), not with the requested time | Compare with the requested length `--minutes × 60` (fixed). Make the rain bed at least the requested time plus 30 s |

## R. Rain animation (Video-Zen4; user feedback in order)

| # | User feedback | Cause | Rule |
|---|---|---|---|
| R1 | "The rain doesn't look real. It's like white lines ... a bit of transparency. It's not about too strong or faint" | v1 drew 1 px white lines and screen-blended them | See-through streaks that take the local scene light (heavily blurred copy of the frame plus a cool ambient), tapered, soft, with refraction of about 1.6 px. Never white |
| R2 | "The direction of the rain is good [straight down]" but "it's too heavy, let's make it a lot less" | The wind lean of 0.10 and 1,000+ streaks | Straight down (`--slant 0`). Start at `--strength 0.8`, `--density 0.4`, then adjust in small steps |
| R3 | "There is no depth. It doesn't look like raining everywhere. Maybe raindrops need different sizes; add more splashes on the coffee table, the ground, the rail, the plants" | One layer, one size, only in the open | Six depth layers from a depth map (Depth Anything V2 Small, 99 MB, Apache 2.0, no account; rank-normalise the map so every layer covers a real share of the picture). A layer is drawn only where the scene behind is farther. Add splash regions per surface with a kind: ground (ring and two droplets), top (counter, stools, awning), rail (flash and droplets along a line), leaf (small hop) |
| R4 | "Reduce the splashes by 40 % and remove all the big raindrops. It's making too much distraction" | The two nearest layers (10–11 px wide, blurred) and 2,600 splash events | Remove the two nearest layers (they were 210 px / 140 px long), splash x0.96 (1,562 events). Big near drops and many splashes pull the eye away from the scene |
| R5 | "Raindrops are still very big. Reduce by 50 % of the size, less white and more transparent" | The remaining layers were still 92 px long, 3.8 px wide | Add `--size 0.5` (length, width and blur x0.5, alpha x width when under 1 px) and `--light 0.5` (how much a drop lightens the scene; the old 0.9 read as white). **Approved: `--strength 0.9 --splash 0.96 --size 0.5 --light 0.5`** |
| R6 | Not said, found while building: the video model's rain did nothing useful, and its sea and steam barely moved (sea flow 0.25 px per 4 frames, steam 59 % upward) | The model boils textures in place and has no travel | For particles and fine motion use a procedural layer that is seamless by construction (whole screens fallen per loop, splash events scheduled modulo the loop, sway with a whole number of cycles). It is verified by the loop point: 0.57 against 0.59 for a normal frame step |
| R7 | The first review always looked at a still; the problem showed only in motion | Streak length, speed and count cannot be judged in a frame | Every change goes to the user as a 10-second loop mp4 (about 5–12 MB at crf 19), with the change described in one line. Encode with a closed GOP (`-g 240 -keyint_min 240 -sc_threshold 0`) so it stream-copies 360 times. File size: about 4.5–5 MB per 10 s loop with the light rain (about 1.6–1.8 GB for the hour), 23 MB with the heavy first rain |

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
