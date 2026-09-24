# SPEC — Still image → seamless 10 s ambient loop

Status: **v1.0. Job 001 delivered and approved (2026-09-23).** Sections 3, 6 and 8 describe the original plan; the *as-built* method is in the box below and in `wiki/README.md` → Recipe.
Principle: **local-first.** Local models and plain scripts do as much of the work as possible; Claude is a thin orchestrator that spends tokens only on decisions (§12).
First job: `jobs/001-snow-tea` (snowy zen garden, tea steam, brazier fire)
Companion docs: `wiki/README.md` (repeatable playbook) · `wiki/runs/001-snow-tea.md` (run log)

---

> **As-built changes (from running job 001).**
> - **Model:** LTX-2.3 22B distilled only (Wan 2.2 I2V not installed; no RIFE needed). Draft = final = 1024×576 → upscaled to 1080p inside the mask.
> - **Loop method:** Draw Things caps a request at **201 frames**, so the ≥ 11 s single clip in §6 is impossible. Instead: two 145-frame clips from the same still (different seeds), chained A → B → A with 1 s crossfades = exactly 240 frames. Implemented in `scripts/loop_build.py` (the timeline is in its docstring). Everything else in §6 (composite through feathered masks) is as planned; the color-match step was not needed (brightness std 0.16).
> - **Prompt:** P5 "strict cinemagraph" (`jobs/001-snow-tea/prompts.md`), because descriptive prompts made the camera zoom 15–25 %. The negative prompt is ignored at CFG 1.
> - **QC actually used:** `qc_drift.py`, `qc_motion.py` and the checks inside `loop_build.py`, plus Claude's read of the seam sheet and your viewing. Local vision-model scoring (§12) was **not** used; scripts were written by Claude directly to keep the loop moving. Claude token use was still modest because all rendering and QC ran as background scripts.
> - **Result:** all §2 criteria met; see `output/001-snow-tea/qc_report.md`.

## 1. Goal

Turn one still image into a **10.000 s, 1920×1080, 24 fps video that loops seamlessly**. The last frame must flow into the first so smoothly that a viewer watching it repeat can't find the seam or tell the clip is only 10 s long. The target use is a YouTube ambient video: this 10 s master will later be looped out to 1–10 hours. No audio in this step.

For job 001, three things move:

| Element | Required behavior |
|---|---|
| Snow | Falls slowly and continuously **downward**, outside the doorway only. Flakes vary in size and depth, and density stays steady with no bursts. |
| Brazier fire | Flickers like real fire, with irregular flames and a gently pulsing glow. It stays soft and out of focus, matching the depth of field. |
| Tea steam | One thin, continuous wisp that rises from the cup, curls, and dissolves. It stays attached to the cup and never reads as smoke. |
| Everything else | **Pixel-identical to the source.** No camera drift, no morphing of the shoji, table, blanket, or lamp. |

## 2. Acceptance criteria

A clip ships only when **all** of these hold:

1. Duration exactly 240 frames @ 24 fps; 1920×1080; H.264 master + ProRes 422 HQ master.
2. **Seam:** the frame-to-frame change across the loop point (frame 239 → frame 0) is no bigger than normal playback change: `seam_ratio ≤ 1.3` (§7). A visual check of the seam preview also passes.
3. **Static lock:** locked regions are bit-identical to the plate in every frame, and the garden shows no drift against the shoji frames (`plate_drift ≤ 0.5 px` at 720p).
4. **No global flicker:** after detrending, the animated region's mean luma has a std ≤ 1.0 and no frame-to-frame jump > 1.5 (0–255 scale).
5. **Direction sanity:** ≥ 65 % of moving pixels in the snow area move down, and ≥ 60 % in the steam box move up.
6. **Rubric** (§7.3): every item ≥ 4/5 and the seam item = 5/5, scored by Claude from frame sheets and crops, then **signed off by you** after watching the 60 s preview.

## 3. Approach

Pure image-to-video can't do this job alone, for three reasons: models drift (the room slowly morphs), they rarely produce clean loops, and small details like steam and fire get few pixels. So the pipeline is **hybrid**:

```
source still ─► plate (16:9 crop) ─► model input (720p)
                       │                    │
                       │           Draw Things I2V (Wan 2.2 A14B or LTX-2)
                       │                    │  hero clip ≥ 11 s, continuous
                       │                    ▼
                       │         QC + pick best seed ──► (fps → 24 via RIFE if Wan)
                       │                    ▼
                       │          crossfade-loop build (period 10 s, fade 1 s)
                       │                    ▼
                       │          color-match to plate (one fixed transform)
                       ▼                    ▼
               1080p plate  ◄── composite through feathered masks ──┘
                       ▼
            encode master + 60 s preview ─► final QC ─► your sign-off
```

The key decisions:

- **Masks do the stabilizing.** Only the doorway/garden region and the steam box come from AI video (`jobs/001-snow-tea/mask_overlay_v0.png`). The room, table, cup, blanket, and lamp are the original pixels at full resolution. Mask edges sit on real edges like the shoji frames and table edge, so the join can't be seen. As a side effect, the room stays sharper than any 720p model output.
- **The loop is built, not generated.** The pipeline generates one continuous clip at least 11 s long and makes it loop by crossfading its tail into its head (§6). Snow, fire, and steam are random textures, so a 1 s crossfade is invisible. First/last-frame conditioning (FLF) is only a fallback: it pins snowflakes to the frozen positions in the still, which makes them visibly slow, snap, or reverse near the loop point.
- **One hero clip for all regions** by default, so snow crossing a mask edge always comes from the same clip. Separate region passes for fire or steam (prompts.md §Region passes) are a fallback.
- **The model is picked by A/B test, not assumed.** Expected trade-off:

| | Wan 2.2 A14B I2V | LTX-2 |
|---|---|---|
| Expected strength | Steam and fire physics, adherence to the source image | Native 24 fps; 11 s in one pass (265 frames); faster |
| Expected weakness | 16 fps native, so it needs RIFE interpolation to reach 24 fps. 11 s means 177 frames, past its 81-frame comfort zone, so there's a risk of repetition or degradation. | Possibly weaker fine detail. Needs padding to multiples of 32. |
| Draft settings | 832×480, 81 frames, Lightning LoRA if installed | 768×448, 121 frames |

  Round 1 generates 2 seeds per model at draft settings. The model that scores best on the rubric becomes the hero model. If LTX-2 is within 1 rubric point of Wan, prefer LTX-2 because it needs fewer post steps.

## 4. Stack

| Tool | Use |
|---|---|
| **Draw Things** (local, HTTP API server on `127.0.0.1:7860`) | All generation. Settings > API Server must be on. |
| Models | Wan 2.2 I2V A14B (high-noise + low-noise experts), optional Wan 2.2 Lightning LoRA for drafts, LTX-2 |
| **Python 3.14 venv** (`.venv`) | `numpy`, `opencv-python-headless`, `pillow`, `requests`. Masks, API client, QC, loop build. |
| **ffmpeg** (`/opt/homebrew/bin/ffmpeg`) | Decode/encode, contact sheets, previews |
| **RIFE** (Practical-RIFE v4.x, PyTorch MPS) | **Only if Wan wins.** 16 → 24 fps interpolation. Needs your OK to download its weights. |
| **Ollama** (`127.0.0.1:11434`) + **OpenCode** (`~/.config/opencode/opencode.jsonc`, already pointed at Ollama) | Local LLM work: `qwen3-coder:30b` writes scripts, `qwen3.5:35B` / `qwen3.8:27b` (vision) score QC sheets and draft wiki entries (§12) |
| Claude | Thin orchestrator: plans, makes decisions between rounds, spot-checks the final seam, reviews diffs. Not a worker (§12). |

Machine: Apple M5 Max, 64 GB unified memory, shared by Draw Things and Ollama (see the memory rules in §12.4).

## 5. Pipeline stages

Each stage writes into `work/<job>/r<NN>/` and logs an entry in the run log.

| # | Stage | Script (to build) | Output |
|---|---|---|---|
| 0 | **Setup**: venv, check the DT API with a tiny txt2img call | `scripts/dt_probe.py` | API response schema, noted in the wiki |
| 1 | **Capture DT base configs**: set each model up in the DT app, then use *Copy Configuration* and save the result to `jobs/_dt_base/{wan22_a14b_i2v,ltx2_i2v}.json`. This captures exact model filenames, refiner, refiner start, shift, and sampler as DT names them. | manual (you or Claude) | 2 JSON files |
| 2 | **Prep**: build the plate crop, per-model inputs (resize/pad), feathered masks at every resolution, and a mask overlay for review | `scripts/prep.py` | `plate_1080.png`, `input_<model>.png`, `mask_*.png`, `overlay.png` |
| 3 | **Generate**: merge the base config with the job's size, frames, prompt, and seed, POST to img2img, save frames plus `meta.json` (full request, seed, time taken) | `scripts/dt_generate.py` | `gen/<model>_s<seed>/frames/*.png`, `raw.mp4` |
| 4 | **QC raw** (§7) on every candidate, then rank them | `scripts/qc.py --stage raw` | `qc/*.json`, contact sheets, crops |
| 5 | **Interpolate** to 24 fps (Wan only) | `scripts/interp.py` | `frames24/` |
| 6 | **Loop build + color match + composite** (§6) | `scripts/loop_build.py` | `loop_frames/` |
| 7 | **Encode** the masters and a 60 s preview (6× loop) | ffmpeg (in `loop_build.py`) | `output/<job>/…` |
| 8 | **QC final** (§7) and write `qc/report.md` | `scripts/qc.py --stage final` | report, seam sheet, rubric |
| 9 | **Iterate** (§8) or hand off to you for sign-off | — | wiki entry |

**Draw Things API assumptions to confirm in stage 0.** The API is A1111-style: `POST /sdapi/v1/img2img` takes a JSON body of DT config keys (`model`, `width`, `height`, `steps`, `guidance_scale`, `seed`, `strength`, `num_frames`, `shift`, `refiner_model`, `refiner_start`, `loras`, `sampler`, …) plus `prompt`, `negative_prompt`, and `init_images: [base64]`, and returns `images: [base64…]` with one entry per frame. If the real schema differs, stage 0 records what it actually is and `dt_generate.py` follows that. Starting values for steps, CFG, shift, and refiner start come from DT's recommended preset for each model (captured in stage 1), not from memory.

## 6. Loop construction

Let `H` be the hero clip at 24 fps with `N ≥ 264` frames, `P = 240` (the 10 s period), and `F = 24` (the 1 s fade).

```
for i in 0..P-1:
    if i < F:
        a = smoothstep((i + 0.5) / F)
        out[i] = (1 - a) · H[P + i]  +  a · H[i]
    else:
        out[i] = H[i]
```

Why this is seamless: `out[P-1] = H[239]` and `out[0] ≈ H[240]`, so playing 239 → 0 is the same as the model's own step 239 → 240. The crossfade happens inside the first second, where both inputs are real, continuous motion.

- **Snow ghosting fix (only if QC flags a density dip or doubled flakes in the fade):** switch the exterior region to a *lighten* blend: `out = (1−s)·lerp(A,B,a) + s·max(A,B)` with `s = 4a(1−a)`. It still equals A at a=0 and B at a=1, but flakes keep full brightness mid-fade.
- **Fire:** if the double exposure is visible, shorten fire's fade to 0.5 s with a per-region `F`.
- **Choosing the window:** if the hero clip is longer than 264 frames, search the start offset `o` that minimizes seam cost, and use `H[o : o+264]`.
- **Color match:** compute one fixed per-channel mean/std transform in Lab. It maps `H`'s first-second average inside the animated mask onto the plate inside the same mask. It's applied identically to every frame; a per-frame transform would cause flicker.
- **Composite:** `final = M·upscale(out) + (1−M)·plate`. `M` is the feathered animated mask at 1080p, and the upscale is Lanczos from 720p. The garden is already out of focus, so 720p is enough there.
- **Fallback if no clip reaches 11 s** (Wan chaining fails): use a 5 s period played twice. Every period must divide 10 s, so the full clip still loops exactly.

## 7. Quality control

Claude can inspect frames but can't watch motion, so QC combines numeric motion metrics, frame sheets Claude reads, and your final viewing.

### 7.1 Metrics (`scripts/qc.py`)

| Metric | Definition | Pass |
|---|---|---|
| `seam_ratio` | mean-abs-diff(frame 239 → 0) ÷ median consecutive-frame diff, animated mask, luma | ≤ 1.3 |
| `plate_drift_px` | phase-correlation shift of frame *i* vs frame 0 on static garden texture (fence, trees), max over *i* | ≤ 0.5 px @720p |
| `luma_flicker_std` / `luma_jump` | animated-region mean luma per frame, detrended std / max step | ≤ 1.0 / ≤ 1.5 |
| `color_drift_dE` | ΔE of first-second mean vs last-second mean, animated mask | ≤ 2.0 |
| `snow_down_frac` | Farneback flow in `snow_qc`, fraction of moving pixels with vy > 0 | ≥ 0.65 |
| `snow_count_cv` | bright-blob count per frame (top-hat + threshold) in `snow_qc`, coefficient of variation, plus dip at seam | ≤ 0.15, dip < 20 % |
| `steam_up_frac` | same, steam box, vy < 0 | ≥ 0.60 |
| `fire_activity` | temporal luma std in `fire_qc` (must be > 0: alive, not frozen) + flow magnitude | > threshold set in R1 |
| `lock_exact` | locked pixels == plate, all frames (final only) | true |

### 7.2 Visual artifacts Claude reviews each round
- `sheet_full.png`: 12 evenly spaced frames
- `sheet_seam.png`: frames 228–239 followed by 0–11 (the loop point), full frame and 2× crops of fire and steam
- `crop_fire.mp4`, `crop_steam.mp4`, `seam_preview.mp4` (slowed 0.5×), plus `preview_60s.mp4` for you
- Flow and luma plots (`qc/plots.png`)

### 7.3 Rubric (1–5)
1. Snow naturalness: varied size and depth, calm speed, no upward or sideways movement, none indoors
2. Fire realism: irregular flicker, glow pulse, stays in the brazier
3. Steam realism: continuous, attached to the cup, rises, curls, dissolves, stays thin
4. Stillness: no drift or morphing anywhere
5. Seam: invisible (must be 5)
6. Artifacts: no smearing, pops at mask edges, or duplicate flakes

## 8. Iteration protocol

- **Round 1 (draft A/B):** 2 seeds × 2 models at draft settings, prompts P1/P2. QC raw, pick the hero model.
- **Round 2 (final settings):** 3 seeds on the hero model at final size and length. Pick the best, build the loop, run final QC.
- **Rounds 3–4:** fix only what failed, using the knob table in `prompts.md`. Change at most 2 variables per round and keep the best-so-far output.
- **Stop rule:** if round 4 still fails, stop and report the failing metrics with sheets and a recommendation. Don't keep burning GPU hours without checking in.
- Every round gets a wiki entry: what changed, why, metrics table, sheets, and the decision.

## 9. Layout

```
Video-Zen1/
  SPEC.md                          ← this file
  input/001-snow-tea.webp
  jobs/_dt_base/*.json             ← DT configs copied from the app (stage 1)
  jobs/001-snow-tea/
    job.json                       ← regions, loop params, model sizes, QC thresholds
    prompts.md                     ← P1 (Wan), P2 (LTX-2), knobs, region-pass prompts
    mask_overlay_v0.png            ← region review image
  scripts/                         ← built in the execution phase (mostly by local models, §12)
    run_round.py llm_review.py wiki_draft.py   ← the local-first driver pieces
  work/001-snow-tea/r01…/          ← generations, QC (scratch, not deliverables)
  output/001-snow-tea/
    001-snow-tea_loop10s_1080p24.mp4
    001-snow-tea_loop10s_1080p24_prores.mov
    001-snow-tea_preview60s.mp4
    qc_report.md
  wiki/README.md                   ← playbook for any new image
  wiki/runs/001-snow-tea.md        ← step-by-step log for this image
```

## 10. Risks and open items

| Item | Mitigation |
|---|---|
| DT API schema or video frame return format differs from the assumption | Stage 0 probe. Fallback is DT's scripting console or a manual export. |
| Wan can't reach 11 s coherently | Chain segments (next segment starts from the previous last frame, 0.5 s crossfade at joins) → otherwise 5 s × 2 period |
| RIFE weights download | Ask you before downloading. Skip it entirely if LTX-2 wins. |
| Model animates the frozen specks on the blanket or indoor floor as snow | Irrelevant: those regions are locked to the plate |
| Garden drifts relative to the locked shoji frames (visible sliding) | `plate_drift` gate; reject the seed or apply an inverse-translation stabilization |
| Model changes the lantern or fire brightness over time | Color-drift and flicker gates; switch seed |
| Render time unknown on M5 Max | Log per-run timings in the wiki; use drafts for exploration |
| Local coder model writes subtly wrong loop or QC math | Claude reviews any diff touching §6 or §7.1; each script needs a smoke test on synthetic input |
| Local vision reviewers are weaker judges of seams and steam | Numbers gate; LLM scores only prioritize; Claude spot-checks the final seam (§12.2–12.3) |
| Ollama and Draw Things fight over 64 GB | Sequential runs, unload LLM before render, no `gpt-oss:120b` (§12.4) |

## 11. Kickoff prompt (paste to start execution)

```
Execute SPEC.md for job jobs/001-snow-tea, following the local-first rules in SPEC §12.
Draw Things API server is running on 127.0.0.1:7860 with Wan 2.2 I2V A14B and LTX-2 loaded;
Ollama is running with qwen3-coder:30b, qwen3.5:35B and qwen3.8:27b.
Delegate script writing, QC scoring and wiki drafting to the local models through OpenCode/Ollama;
use Claude only for the decisions listed in §12.2. Start at stage 0, run Round 1 (draft A/B)
through scripts/run_round.py, and log every step in wiki/runs/001-snow-tea.md.
Ask me before downloading RIFE weights. Stop after Round 2 and show me the seam sheet,
metrics table, the 60 s preview and a token/usage note before iterating further.
```

## 12. Local-first orchestration (save Claude tokens)

**Rule:** if a local model or a script can do a step acceptably, it does it. Claude is called only for what they can't do well. All video generation stays in Draw Things with local models (Wan 2.2, LTX-2).

### 12.1 Who does what

| Work | Owner | How |
|---|---|---|
| Image generation and video generation | Draw Things + Wan 2.2 / LTX-2 | HTTP API, via `scripts/dt_generate.py` |
| Prep, loop build, interpolation, encode, contact sheets, all numeric QC (§7.1) | **Plain Python + ffmpeg, no LLM** | Deterministic scripts; cost nothing once written |
| Writing and fixing the scripts in §5 | `qwen3-coder:30b` through OpenCode | One script per task with a short brief that quotes the relevant SPEC section; it must run its own smoke test |
| Rubric scoring from frame sheets and crops (§7.3) | `qwen3.5:35B` (vision); `qwen3.8:27b` as second opinion | `scripts/llm_review.py` sends the sheets to Ollama and writes `qc/llm_review.json` (scores + one line per item) |
| Drafting wiki run-log entries, metrics tables, delivery notes | `qwen3.5:35B` or `qwen3.8:27b` | `scripts/wiki_draft.py` fills the run-log template from the JSON files; Claude only skims |
| Running rounds unattended | `scripts/run_round.py` | Generate → QC → review → write `round_summary.json`, then stop |
| **Decisions between rounds; final seam and rubric spot-check; reviewing script diffs; anything the local models get wrong twice** | **Claude** | Reads `round_summary.json` (a few hundred tokens), not the raw sheets, unless the summary says the models disagree |

### 12.2 When Claude is called (and only then)
1. Plan changes to SPEC, `job.json` or prompts.
2. Picking what to change for the next round when the summary shows a failure (using the knob table in `prompts.md`).
3. **Final sign-off check:** one look at `sheet_seam.png` plus the numeric report, before it goes to you.
4. Escalations: the two local reviewers disagree by ≥ 2 rubric points on any item; a local model fails the same task twice; a script's diff touches the loop math (§6) or the QC thresholds.

### 12.3 Delegation protocol
- **Script tasks:** Claude writes a brief of at most 15 lines (inputs, outputs, the SPEC section, and the acceptance test), then runs `opencode run --model ollama/qwen3-coder:30b "<brief>"`. Claude reviews the diff and the smoke-test output only. If the diff is wrong, send back one round of feedback; if it's still wrong, Claude fixes it and notes the failure in the wiki.
- **Review tasks:** `llm_review.py` sends each of `sheet_full.png`, `sheet_seam.png`, `crop_fire.png` and `crop_steam.png` with the §7.3 rubric and asks for strict JSON. Both vision models score independently; results are merged by taking the lower score per item (conservative).
- **Local reviewers advise, and the numbers gate.** A round passes on the §2 metrics plus your sign-off, and the LLM rubric decides which failures to look at first. A local model's score alone never passes or fails a round.
- **Log what was delegated.** Each run-log step notes which model did it and whether Claude had to correct it, so the wiki shows what local models handle reliably.

### 12.4 Memory and concurrency (64 GB shared)
- **One heavy thing at a time.** Draw Things video generation and Ollama vision models never run together. `run_round.py` runs them in sequence and unloads the LLM before a render (`ollama stop <model>`; also set `OLLAMA_KEEP_ALIVE=0`).
- Never load `gpt-oss:120b` (65 GB) during this project. It doesn't fit next to a video model.
- Estimates, not measured: the 23 GB `qwen3.5:35B` plus a 14B Wan run is tight. Stage 0 measures peak memory (`memory_pressure` / Activity Monitor note) and records real numbers in the wiki. If it swaps, use `qwen3.8:27b` (17 GB) as the only reviewer.

### 12.5 Budget and a fallback
- Target: Claude tokens spent mainly on §12.2 items. Expected per round: one small `round_summary.json` read plus one decision. `run_round.py` prints a line at the end listing which steps ran on which model.
- If the local vision models can't score reliably (they contradict the numbers, or flip on identical input), stop using them for scoring, keep them for scripts and wiki drafts, and record it in the wiki. Claude then reads the seam sheet directly, one image per round.
