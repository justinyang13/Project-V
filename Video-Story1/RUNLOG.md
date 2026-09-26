# RUNLOG — Video-Story1 ("Mei and the Dragon Who Feared Thunder" trailer)

The rundown of every step, in order, written as the work happens. Spec: [SPEC.md](SPEC.md) · Canon: [CANON.md](CANON.md).

**Entry template** (copy for each step):
```
### <n>. <short title>  ·  <date time>  ·  who: Claude | Qwen | script | user
- Why:
- Command / tool (exact):
- Parameters (model, seed, size, steps):
- Output files:
- Numbers / result:
- Decision / next:
```

## Status board
| Stage | State |
|---|---|
| Study of the book | done (1–2) |
| Plan agreed with user | done (3–4) |
| SPEC v0.1 + CANON + RUNLOG | written (5); user then asked for the video overnight: gates G1–G5 self-approved by Claude |
| Keyframes, animation, audio, assembly | **done**, trailer delivered in `output/` (31) |
| Stage 0 tech tests | done: T0.1 style (Z Image Turbo), T0.2 consistency (cover-head composite for Yun), T0.3 LTX on painting (works, seed choice matters), T0.5 voice (Qwen3-TTS Serena), T0.6 music/sound (ACE-Step, MOSS) |
| G1 canon sheets … G6 final | not started |

---

### 1. Read the whole book  ·  2026-09-25  ·  who: Claude
- Why: the user wants me to know the characters and world inside out; consistency is the key.
- Tool: read `source/bible.md`, `source/outline.md`, all 20 `source/chapters/chNN.json` (100 pages of text + per-page image prompts), viewed cover and all 100 illustrations as contact sheets.
- Output: notes saved to memory (`project-video-story1`, `reference-mei-book-canon`); text + image prompts dumped to `input/refs/book_full_text_and_image_prompts.txt`.
- Result: canon and timeline understood (CANON.md). Found **book problems**: art drift (Yun cover vs interior; Tao's boots brown on p041; Hua's jeans/sneakers not in the bible; Nainai's jacket grey-brown on p080/p095; Yun's size and pose vary); Captain the tadpole dropped after ch7; tea gift is both a "red paper bundle" and a "bamboo tube"; the book's images are 640×640 (too small to reuse). Decisions in CANON §6.

### 2. Checked what tools exist  ·  2026-09-25  ·  who: Claude
- Read Project-V SPEC/models/lessons, `draw-things-cli --help`, `models list`, `train lora --help`, SSD model folder.
- Result: **`draw-things-cli train lora` exists** (local LoRA training, dataset of images + .txt captions) and Qwen-Image-Edit-2511 / FLUX.2 klein are in the CLI's model list: options for character consistency. Installed on the SSD: klein 9B, Z Image Turbo, qwen_3_vl_4b, LTX-2.3 22B distilled + upscalers, Depth-Anything-V2-Small, ACE-Step, MOSS. Video via CLI is verified (Project-V lesson A20).
- Found how the book art was made: `/Users/justin/Code/Maxi/factory/books/mei-and-the-dragon-who-feared-thunder/style.json` (style prefix, per-character "looks" strings, cover prompts with seeds) and `gen_images.py` (Z Image Turbo, 768 px pages, seed_base 21000). Copied `book_style.json`, `cover_front_art.png` (1024×1536 art-only cover), `book_bible.md` into `input/refs/`.

### 3. Plan presented to user  ·  2026-09-25  ·  who: Claude
- Presented the study, the consistency system, stages and questions.

### 4. User decisions  ·  2026-09-25  ·  who: user
- 60–90 s trailer · 16:9 for YouTube · match the book watercolor exactly · Yun = cover version exactly (serpentine) · narrator chosen by Claude · music yes · not for Zen Hour Music, language rule applies, use book titles/words only · free downloads OK · "don't go idle, use local AI".
- Later: "start with spec and rundown file; record the steps as much as possible."

### 5. Wrote SPEC.md v0.1, CANON.md, this RUNLOG  ·  2026-09-25  ·  who: Claude
- Created folder `Project-V/Video-Story1/{input/refs,jobs,output,work,research}`.
- SPEC covers: contract, gates G1–G6, draft 13-shot trailer script (book words only), Stage 0 tests T0.1–T0.6, consistency system (canon sheets, identity strings, continuity ledger, keyframe checklist), image/motion/audio/text specs, roles, never-idle rules, documentation rules, risks, open items.
- Decision: the standing memory says "FLUX.2 klein 9B, not Z Image Turbo" for Project-V pictures, but the book art was made with Z Image Turbo and the user wants an exact match. Not decided by Claude: T0.1 measures both; a one-time exception is asked of the user only if klein cannot match (SPEC §12 item 2).

### 6. Background research by local AI (Qwen)  ·  2026-09-25 23:08  ·  who: Qwen (qwen3.8:27b, direct Ollama API via `~/.claude/bin/qwen_agent.py`, web tools, 1200 s limit each)
- Script: `research/run_research.sh` runs three tasks in sequence, each writing a report: `tts_report.md` (free local narrator voices for Apple Silicon), `consistency_report.md` (character LoRA training with the Draw Things CLI, reference editing, multi-character tips), `ltx_report.md` (keeping painted faces stable in LTX-2.3 image-to-video). Completion flag: `research/research_done.flag`.
- Status: running (TTS report still being written at 23:15).
- Rule: Qwen's facts get spot-checked by Claude before they enter the SPEC/RUNBOOK (registry: it can invent details).

### 7. T0.1 style match, first result (FLUX.2 klein 9B)  ·  2026-09-25 23:12  ·  who: Claude + Draw Things CLI
- Why: "match the book down to exact"; the book's images came from Z Image Turbo, the user's standing choice is klein.
- Command: `DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models draw-things-cli generate --model flux_2_klein_9b_i8x.ckpt --no-download-missing --disable-preview --width 1024 --height 1536 --seed {731,733,735} --prompt-file work/t0_style/prompt_cover.txt --output work/t0_style/klein_<seed>.png` (prompt = the book's `covers.front3.prompt`; script `work/t0_style/run.sh`).
- Result: 43 s per image including model load; 4 sampling steps. Comparison sheet `work/t0_style/compare.jpg` (cover + 3 klein).
- Looks (Claude viewing): klein reproduces the **gouache/coloured-pencil paper-grain family** well, but **not the exact cover**: Mei got a **zip puffer jacket with patches** (cover: padded jacket with cloth **knot buttons**) and a **conical bamboo hat** (cover: wide round straw hat); Yun's head is sharper, more spiky and realistic, greener than the cover's teal, antlers browner and larger, a **silver pearl hangs under the chin** (good: the pearl is canon, the cover doesn't show it), a soft feathery grey mane is missing; background mountains are cleaner/paler than the cover's ink-wash peaks.
- Verdict so far: text prompt alone does not give "exact"; this confirms the need for the reference-based consistency method (T0.2). Z Image Turbo baseline for the same 3 seeds is rendering (`work/t0_style/run_z.sh`, files `z_<seed>.png`) so the two can be compared fairly.

### 8. T0.1 style match, verdict (Z Image Turbo baseline)  ·  2026-09-25 23:19  ·  who: Claude
- Command: same as 7 with `--model z_image_turbo_1.0_q8p.ckpt` (script `work/t0_style/run_z.sh`), seeds 731/733/735, same prompt. Sheet: `work/t0_style/compare_z_vs_klein.jpg` (cover, z731, z733, z735, klein731).
- Result (Claude viewing): **Z Image Turbo with the book's prompt reproduces the cover look almost exactly** (seed 733 gives the same composition, teal serpentine Yun with grey mane, round straw hat, knot-button padded jacket, ink-wash peaks). **FLUX.2 klein 9B does not** (zip puffer jacket, conical hat, spiky realistic dragon, pale cleaner mountains).
- Consequence: "match the book down to exact" and "cover-exact Yun" need Z Image Turbo as the base look. This conflicts with the standing rule "FLUX.2 klein only, never Z Image Turbo" (memory feedback-image-model-flux2-klein). Not overridden by Claude: **user asked** (see 9).
- Possible middle path to test if the user prefers klein: klein with reference images from the cover (method A of T0.2) or a klein LoRA trained on Z-Image-made canon images. Both are extra work and may still not be exact.

### 9. User decision: Z Image Turbo for this project only  ·  2026-09-25 23:22  ·  who: user
- Asked via a question dialog; answer: "Z Image Turbo, this project only". Recorded as SPEC D10; standing klein rule unchanged for other videos. Memory note updated.

### 10. Qwen research failed once, fixed the tool, restarted  ·  2026-09-25 23:24  ·  who: Claude + Qwen
- What happened: all three Qwen reports of run 1 were empty or refused ("No results" for every query). Cause: `web_search` scrapes DuckDuckGo, which now returns a bot-challenge page. Qwen also could not find `draw-things-cli` (it is not on the web index it saw).
- Fix (Claude configured the local agent; user rule "configure Qwen to handle more"): `~/.claude/bin/qwen_agent.py` `web_search` now falls back to the **GitHub repo search API and HuggingFace model search API** (no keys); backup at `qwen_agent.py.bak`. Tested: query "kokoro" returns hexgrad/kokoro (Apache-2.0) and the HF model card.
- Restart: `research/run_research2.sh` (900 s limit per task, grounded prompts, real CLI help saved in `research/draw_things_cli_help.txt`); run-1 outputs moved to `research/failed_run1/`. Reports: `tts_report.md`, `consistency_report.md`, `ltx_report.md`, flag `research_done.flag`.
- Lesson candidate: local research needs a search backend that does not bot-block; check `web_search` before delegating web research.

### 11. T0.2 candidate batch (Z Image Turbo, Mei + Yun)  ·  2026-09-25 23:31  ·  who: Claude + script
- Why: find out how well the CANON identity strings alone hold Mei and Yun across 6 varied scenes × 4 seeds each (the baseline "method A0"), and produce the raw material for a character LoRA (method B) if strings alone drift.
- Command: `scripts/t02_batch.py` (background, log `work/t02_batch.log`); model `z_image_turbo_1.0_q8p.ckpt`, 1024×576, seeds 7101–7104, book style prefix + CANON §2 Mei string / Yun cover-based string (+ pearl phrase in the two pearl scenes). Every prompt and seed is saved in `jobs/t02/prompts.json`.
- Speed: ≈ 25 s per image. 48 images.
- LoRA check: `draw-things-cli train lora --model z_image_turbo_1.0_q8p.ckpt --dataset <dir> --dry-run` accepts Z Image Turbo (default rank 32, resolution 512, name lora_output); a real training run is not done yet **[UNVERIFIED]**.
- Next: contact sheets → Claude scores them with the SPEC §5.4 checklist → decide A0 vs LoRA.

### 12. T0.2 batch verdict (Claude viewing `work/t02/sheet_mei.jpg`, `sheet_yun.jpg`)  ·  2026-09-25 23:50
- **Mei (24 images): identity holds.** Same face, two braids with red string, wide straw hat, blue padded jacket with knot buttons and patch, brown trousers/cloth shoes in 24/24. Small drifts: patch position moves, blue is brighter/cleaner than the cover's faded blue, hat shape varies slightly. Weakness is **composition, not identity**: the scene words are often ignored (a "classroom" became a bench outdoors with a chalkboard, "climb from behind" showed her from the front) and she is small and centred.
- **Yun (24 images): consistent with himself, but not the cover.** Every image has teal scales, cream belly plates, brown antlers, grey mane; but the face is **cuter and more cartoon (pig-like snout, round eyes)**, smaller and with front legs, less elegant than the cover's long refined head. So strings alone give "a Yun", not "the cover Yun". Pearl reads as a silver bead hanging from the whisker (needs a decision at G1).
- **New artifact found:** tiny face-like blobs and dots on rocks, roofs and ground in many images (Yun sheet especially). Likely caused by the style prefix words "expressive kind faces". Fix: drop that phrase for scenes and for Yun, or add positive scoping (Lesson from the novel job: positive scoping beats negative words).
- Verdict: method A0 (strings + fixed style) is good enough for Mei and the human cast in wide shots, **not enough for cover-exact Yun**. Next: method B, a Yun LoRA (and probably Mei) trained on curated images, plus img2img from the cover crop for the Yun head.

### 13. Delegation plan for local AI written  ·  2026-09-25  ·  who: Claude (at the user's request)
- Added SPEC §9.1: per stage, which local worker does what, what Claude checks, and each worker's known limit.

### 14. User goes to sleep: "I want the video in the morning"  ·  2026-09-26 00:10  ·  who: user, Claude
- Instruction: deliver the finished trailer by morning; no input needed from the user meanwhile.
- Decisions by Claude (recorded so they can be reviewed): (a) gates G1–G5 are self-approved using SPEC §5.4 and the numeric checks; each self-approval is logged with the evidence; (b) Mac kept awake with `caffeinate -dims -t 43200`; (c) status line to the user at least every 5 min (new machine rule); (d) keyframes at 1024×576 (Z Image Turbo), video clips at 1024×576, final upscale to 1920×1080; (e) TTS and Qwen may run beside Draw Things, ACE-Step and MOSS only after the video renders.
- Also found: the first Yun run at 00:03 failed (system Python has no PIL); scripts now use `Project-V/.venv/bin/python`. Nothing had been running between 23:50 and 00:03 (I only work while a turn is active); this was told to the user.

### 15. Cover-reference fix and cover reproducibility  ·  2026-09-26 00:25  ·  who: Claude
- Bug found: the Yun i2i test (`scripts/yun_i2i.py`) used `cover_front_final.png`, which has the title text baked in ("RED THUNDER" appeared in every render). Fixed: reference is now the **art-only** `cover_front4.png` (copied to `input/refs/cover_front_art.png`, crops in `input/canon_src/`).
- Important fact: `cover_front4.png` and my own Z Image Turbo render of the same prompt with seed 733 differ by 0.21/255 on average, i.e. **the cover is exactly reproducible** (same model, prompt, seed, size 1024×1536). So "cover-exact Yun" can be re-rendered at will, and Z Image Turbo is confirmed as the right model.
- The first Yun i2i run (with text) still showed the head is preserved at strengths 0.35–0.65 (i2i keeps the cover head closely); the run will be redone on the art-only crop.

### 16. GitHub check-ins blocked by the permission system  ·  2026-09-26 00:28  ·  who: Claude
- User asked for regular GitHub check-ins. `git commit && git push` to the public repo `justinyang13/Project-V` was denied twice by the auto-mode classifier ("Out-of-Place Publication"; earlier the jCore backup push was denied as "Sensitive-Source Provenance"). Not worked around.
- State: files are staged locally (`git add .gitignore Video-Story1`); nothing committed or pushed. `.gitignore` now excludes the book's full text, bible copy, cover art copies and crops.
- Needs the user: allow the push (add a `Bash(git push:*)` permission rule in Claude Code settings, or approve when asked). Progress is meanwhile recorded in this RUNLOG.

### 17. Keyframes S01–S07 (non-Yun shots)  ·  2026-09-26 00:26  ·  who: Claude + script
- `scripts/keyframes.py jobs/shots_nonyun.json` → `work/kf/<shot>_<seed>.png`, 4 seeds (9101–9104), 1024×576, Z Image Turbo, book style prefix **without** "expressive kind faces" (removed to avoid the face-blob artifact), identity strings from `jobs/identity.json`. ≈ 10 s per image.

### 18. Keyframe selection S01–S07 (self-approved gate G3, part 1)  ·  2026-09-26 00:40  ·  who: Claude
- Viewed `work/kf/sheet_nonyun.jpg`, `sheet_reroll1.jpg`. Picks (recorded in `jobs/selected.json`): S01_9102, S02r_9202, S03_9102, S04_9101, S05_9101, S06r_9202, S07_9101.
- Problems found and fixed: S02 first came out lush green (story needs a drought): re-rendered with "parched pale yellow and brown, cracked ochre soil, no green fields" (S02r, seeds 9201–9204): fixed. S06 gave Mei the map (Hua's prop): reworded, 1 of 4 seeds correct. Known small flaws kept: S06 has a stray paper on the ground; S05 is a daylight classroom, not dim; Mei's hat looks conical in some S02 seeds.

### 19. Yun into the shots: cover head pasted + blended  ·  2026-09-26 00:55  ·  who: Claude + script
- Problem: strings alone give a cuter, smaller Yun (T0.2); LoRA from one image would only learn one view.
- Method (`scripts/yun_compose.py`): render the scene **without** Yun (children, boulder/lake/village, empty mist area) → paste the art-only cover Yun head (crop 230,230,960,810 of `cover_front4.png`, feathered edge) → Z Image Turbo image-to-image at strength 0.4–0.65 with a Yun+scene prompt (`jobs/blend/S*.txt`) to blend light and edges. GrabCut cut-out was tried first and failed (lost antlers/eyes).
- Result (Claude viewing `sheet_S09c.jpg`, `sheet_yunshots.jpg`): **the head stays the cover's design in every shot**, children keep their look, mist blends. S08 uses an upper-head crop (`YUN_CROP=380,250,860,610`) with the boulder strip pasted back in front (`YUN_OCCLUDE`), i2i 0.55. S12 strength 0.65 gives a slightly open mouth and yellowish eye (accepted).
- Picks: S08c_s55, S09c_9302_s40, S10c_s40, S11c_s45, S12c_s65, S13c_s40. All 13 keyframes copied to `input/keyframes/S01–S13.png` (1024×576). G3 self-approved.
- Known weak points: Yun is always the cover's 3/4 view looking down-left (no other angles); no pearl visible except a faint glow; S11 Yun is small in the frame.

### 20. Answer to the user: "shouldn't you use LTX or Wan?"  ·  2026-09-26 00:58  ·  who: Claude
- Yes, LTX-2.3 animates each keyframe (stage 5, started 01:00). Wan 2.2 on the SSD is text-to-video only and cannot animate a given picture (Project-V lesson).

### 21. LTX-2.3 animation queue (seed 101, all 13 shots)  ·  2026-09-26 01:00  ·  who: script `scripts/animate.py`
- Motion prompts in `jobs/motion.json`: painted illustration, everything frozen except a short list of gentle motions; camera never mentioned (Project-V A2/A13; Qwen's research suggested the opposite, empirical lesson wins). Model `ltx_2.3_22b_distilled_1.1_q8p.ckpt`, 145 frames, 1024×576, 8 steps, cfg 1.0; output prores → h264, frames every 12 for contact sheets. Order: S09, S12, S08, S10, S07, S13, S11, S06, S01–S05. Log `work/animate_q1.log`.

### 22. Narration (Qwen3-TTS "Serena")  ·  2026-09-26 00:30  ·  who: Claude + mlx-audio
- Installed free: `mlx-audio` in `Project-V/tools/tts-venv` (uv, Python 3.12; git-ignored). Model `mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit` (Apache-2.0, chosen from the Qwen research report, `research/tts_report.md`), cache `HF_HOME=/Volumes/SSD-4T-LR/AI/hf-cache`. First run failed ("Speech tokenizer not loaded"): macOS `._*` junk files on the exFAT cache; deleted them from my cache folder, then it worked.
- `scripts/narrate.py Serena serena` → `work/tts/lines/serena_N1..N7_000.wav`; text = the book's own back-cover sentences (`jobs/narration.json`, verbatim). Voice instruction: slow, warm, gentle bedtime-story read-aloud. Durations 7.4 / 10.1 / 7.0 / 7.8 / 16.1 / 7.9 / 6.2 s (62.5 s). The `--speed 1.12` option did not shorten it (8.0 s vs 7.4 s for N1, sampling varies), so the timeline uses `atempo 1.08` on the speed-1.0 lines.
- The user said "you pick the voice": Claude picked Serena (the report's "warm, gentle young female"). Not heard by Claude; the user's ears decide.

### 23. Text cards and end card  ·  2026-09-26 00:40  ·  who: Claude + `scripts/cards.py`
- Georgia Italic for the tally line and quotes, Avenir Next Heavy for the end-card title (the cover's font family), colours from the book's cover meta. End card = cover-palette background, the art-only cover on the right, kicker/title/tagline on the left. All words are the book's (title, subtitle, tagline "Some voices shake. Use them anyway.", quotes p024/p049/p060/p090).

### 24. Timeline, assembler, captions, language check  ·  2026-09-26 00:50  ·  who: Claude
- `jobs/timeline.json` (88.0 s total: 13 shots + 6.6 s end card, 0.5 s dissolves, narration and card times), `scripts/assemble.py` (ffmpeg), `scripts/make_srt.py` (15 captions), `scripts/lang_check.py` (blocking; PASS).
- Qwen ledger (`jobs/ledger.csv`) was delegated; its output is thin (many "n/a") so Claude fills gaps later. Qwen was unloaded (`ollama stop`) at 00:35 because memory was at 69 GB used with LTX rendering.

### 25. LTX-2.3 animation, pass 1 (seed 101, all 13 shots)  ·  2026-09-26 00:32–01:13  ·  who: script `animate.py`
- 13 clips, 145 frames each, 1024×576, ≈ 210–285 s per clip (a first `ffmpeg -vsync` frame-extract line failed on every clip; harmless, fixed to `-fps_mode passthrough`). Output frame rate is 25 fps (145 frames = 5.8 s); the assembler re-times to 24 fps.
- Memory note: with Qwen (19 GB) loaded the Mac hit 69 GB used; `ollama stop qwen3.8:27b` fixed it. Rule: unload Qwen before video renders.
- Review (Claude, `progress/06_*.jpg`, `07_*.jpg`, frames 0/70/144 of each clip): good: S01 S02 S04 S05 S07 S09 S10 S11 S12 (Yun's head stays the cover design; children keep their look). **Problems:** S03 has a glitch at ~frame 70 (golden crossed sticks fly through the air); S06 pushes in strongly (faces grow, buffalo cropped); S13 Tao runs out of frame by the end; S08 Yun's head drifts a little on the boulder; S12 Tao's tiger emblem became a round badge (keyframe, blend strength). Plan: pass 2 with seed 202 for S03, S06, S13, S08, S07 (S03/S06/S13 prompts tightened: nothing flies, everyone stays in place).

### 26. Music (ACE-Step 1.5)  ·  2026-09-26 01:15–01:20  ·  who: Claude + `music_gen.py`
- Server `tools/ACE-Step-1.5/start_api_server_macos.sh` (checkpoints on the SSD). 90 s pieces take ≈ 46 s. Round 1 (`trailer_11`, `trailer_22`, prompt with bamboo flute + zither + strings, 72 bpm, D major): both **failed `audio_qc.py`** (13 and 12 harsh/clipping events, sample peaks above 0 dBFS). Rework: post-process (low-pass 9–9.5 kHz, −4 dB, limiter 0.75) cut events to 3; round 2 with a "very soft, warm, mellow, no bright or shrill notes, no bells" prompt (seeds 33/44/55/66) gave, after the same post-process, 10/5/2/1 events.
- Pick: `soft_55` (2 events, both in the first 0.5 s; a 1.5 s fade-in leaves 1 event: hf_ratio 0.33 at 0.5 s, a ratio artifact at near-silence; not audible harshness by measurement, **user to confirm by ear**). Level profile: quiet start (−27 dB), swell −18 dB from 55 to 75 s (matches shots S09–S12), gentle end. File `work/audio/music.wav`. Server stopped afterwards.

### 27. Sound effects (MOSS-SoundEffect)  ·  2026-09-26 01:20  ·  who: Claude + `rain_gen.py`
- 21 clips (7 sounds × 3 seeds), ≈ 10 s each (`jobs/sound_jobs.json`). QC table: only `thunder_1`, `thunder_2`, `thunder_3` passed outright; others flagged for hiss/harsh events. Choices: thunder_1 (single rolling peak at 6 s, mean −22.7 dB), rain_3 (steady 3 dB range), cheer_2 (steady), bamboo_1, pool_1 (steady), bell_1, roomtone_1. Processed by `scripts/sfx_build.py` (low-pass 4.5–8 kHz, gain, fades). Thunder gets a 4.5 kHz low-pass and −3 dB so it rolls warmly, not sharp.

### 28. First full assembly (v1)  ·  2026-09-26 01:23  ·  who: Claude + `assemble.py`
- `output/Video-Story1_trailer_1080p24.mp4`: 88.000 s, 1920×1080, 24 fps, H.264 + AAC 48 kHz stereo, 64 MB. Voice: Serena lines at atempo 1.08; music ducked under voice (sidechain); 8 sound layers; loudnorm. Measured: **−13.8 LUFS integrated, LRA 6.3 LU, true peak −1.4 dBTP**. Picture-only test cut (14 s to render) reviewed frame by frame (`progress/08_*.jpg`). Language check PASS. Later adjustments: cards for "I'll go." and "Because so am I." re-timed to the spoken lines; 2.5 s audio fade-out; true-peak target −2.

### 29. LTX pass 2 (seed 202: S03, S06, S13, S08, S07)  ·  2026-09-26 01:30  ·  who: script
- Started; then pick the better clip per shot (`jobs/clip_choice.json`), re-assemble, re-measure.

### 30. LTX passes 2 and 3, clip choices  ·  2026-09-26 01:30–01:47  ·  who: Claude + script
- Pass 2 (seed 202: S03, S06, S13, S08, S07) and pass 3 (seed 303: S03, S06 with simpler prompts, the words "sticks/bamboo/willow" removed). Frame sheets in `progress/`. Results: **S03_303** clean (dust and clouds drift; the floating-sticks glitch was on seeds 101 and 202); **S06_303** keeps the group framed with faces intact (101 and 202 pushed in); **S13_202** keeps Tao in frame (101 lost him; expression a bit stiffer); **S08_202** Yun rises above the boulder (better than 101); **S07_202** steady. Choices in `jobs/clip_choice.json`: S03→303, S06→303, S07→202, S08→202, S13→202; all others seed 101.
- Known small flaws kept: S12 Tao's tiger emblem reads as a round badge; S06 a stray paper on the ground; S05 daylight classroom; S01 Nainai's notch is implied, not clearly cut.

### 31. Final assembly and delivery check  ·  2026-09-26 01:49  ·  who: Claude + `assemble.py`
- Files in `output/`: `Video-Story1_trailer_1080p24.mp4` (**88.000 s**, 1920×1080, 24 fps, H.264 + AAC 48 kHz stereo, 63.2 MB), `_audio.m4a` (2.9 MB), `_silent_1080p24.mp4` (60.3 MB), `_captions.srt` (15 captions), `_thumbnail.png` (1280×720, cover-style end card), `_description.txt` (the book's own title, subtitle, blurb, tagline).
- Numbers: **−13.9 LUFS integrated, LRA 6.0 LU, peak −1.9 dBFS**; `blackdetect`/`freezedetect`: none; **language check PASS** (5 files, none of the four banned words); narration lines: 0 clicks, 0 clipping, 0 whistle/tone events (`hf_ratio` and dropout flags are consonants and pauses; the piano-tuned limits do not apply to speech).
- Length 88 s: inside the user's 60–90 s window.
- Not done / deferred: the `work/` folder (clips, keyframes, audio stems) is kept, not deleted, so the user can ask for changes; Project-V's cleanup rule ("delete work/ at the end") waits for the user's approval of the trailer. GitHub push is blocked (16).

### 32. What only the user can judge (open items)
1. Listen to the narration (Qwen3-TTS "Serena", speed ×1.08): warmth, pace, any odd words. Claude cannot hear.
2. Listen to the music (ACE-Step `soft_55`): one measured flag at 0.5 s (ratio artifact), otherwise clean; is the swell right for the thunder?
3. Sound effects: joyful thunder at 70.8 s, village cheer, rain; too loud or too quiet?
4. Picture: is Yun cover-exact enough in S09–S12 (head is the cover's, always the same 3/4 view)? Tao's tiger badge in S12.
5. Approvals still open from the SPEC: publishing place, whether to allow `git push` (permission rule).

### 33. Waiting on / next  ·  who: Claude
- Next actions (in parallel, never idle): (a) finish the T0.1 A/B; (b) read Qwen's three reports and verify key claims; (c) prepare the T0.2 test: crop Mei and Yun references from the cover, run method A (klein with reference image), B (LoRA training dry-run to learn time/cost), C (Qwen-Image-Edit-2511: check size and licence before download; user approved free downloads); (d) draft the ledger with Qwen once the user approves the script.
- Waiting on user: review of SPEC v0.1 (open items in SPEC §12).
