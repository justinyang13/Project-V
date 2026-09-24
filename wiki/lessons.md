# Lessons — what went wrong, why, and the rule that came out of it

Read this before starting a new job. Each row is something that actually happened in job 001. Add new rows at the bottom of the right table.

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
| A11 | (untested) Draw Things CLI | — | User rule: use the CLI so closing the app doesn't matter. Validate it in stage 0 (SPEC §5) and record the outcome here |

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
| D6 | The user preferred piano (v3b) over flute and koto | Taste | Offer three styles in stage 7 and let the user pick; piano + faint flute + pad was the winner |

## E. Working style that worked
- Confirm risky/large actions (moving 71 GB of models; deleting) and verify sizes before deleting.
- Answer the user's confusion directly (e.g., the 40-second excerpt vs the 1-hour file are different files).
- Log every step in the run log as it happens; the wiki is the memory.
