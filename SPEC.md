# SPEC — Image → 1-hour ambient loop video (v2, generic)

**Input:** one image. **Output:** a 1-hour, 1080p, 24 fps YouTube-ready video with original music and ambience, plus the separate audio track and a silent 10-second loop so the audio can be swapped later.

Status: v2.0 · 2026-09-23 · derived from job 001 (`001-snow-tea`), which produced the reference result. Everything here was done once, end to end, by Claude driving local tools. Items not yet proven are marked **[UNVERIFIED]**.

Companion docs: [Runbook](wiki/runbook.md) (exact commands) · [Lessons](wiki/lessons.md) (what failed and why) · [Music](wiki/music.md) · [Models](wiki/models.md) · [Job 001 log](wiki/runs/001-snow-tea.md) · HTML versions in `docs/` (open `docs/index.html`).

---

## 1. Contract

### 1.1 What you provide
An image file. Nothing else is required. If the image has something that should *not* animate (or a specific mood for the music), say so in one line; otherwise Claude decides.

### 1.2 What you get (per job `<id>` = `NNN-slug`)
Kept in `output/<id>/`:

| File | What | Notes |
|---|---|---|
| `<id>_1hr_1080p24.mp4` | The final video | 3600.000 s, 1920×1080, 24 fps, H.264 + AAC 256 kbps, about 1.1 GB. Upload this. |
| `<id>_audio_60min.m4a` | The full-length mix (music + ambience) | Kept separately so the audio can be replaced later. About 110 MB. |
| `<id>_loop10s_1080p24_silent.mp4` | The seamless 10-second loop, no audio | The master picture. Re-mux with any audio to make a new long video (see Runbook §M). |

Everything else (frames, test clips, samples, ProRes, previews) is scratch and gets deleted at the end (stage 9).

### 1.3 Human touchpoints (only these need you)
1. **Optional:** confirm the "what moves" list and mask overlay (stage 2), if Claude asks.
2. **Sign-off A — the loop (stage 6):** watch the 10-second loop repeating; say whether you can see the loop point and whether the fire/steam/snow (or equivalent) look right.
3. **Sign-off B — the music (stage 7):** listen to 30-second samples; pick one; then approve the same sample with ambience added.
4. **Sign-off C — the hour (stage 8):** listen to the two excerpts and spot-check the full file.
5. Upload to YouTube yourself (see §10).

### 1.4 Roles
| Who | Does |
|---|---|
| **Claude** | Looks at the image, decides what moves, draws the masks, writes the prompts, runs the stages, reads the QC numbers and contact sheets, decides what to change between attempts, writes the wiki entry. Cannot hear audio or watch motion. |
| **Scripts** (`scripts/`) | All rendering, compositing, measuring, encoding. Deterministic. |
| **Draw Things** (LTX-2.3, local) | Image-to-video. **Use `draw-things-cli`, not the app** (standing rule from the user: closing the app must not affect renders). **[UNVERIFIED]** — job 001 was rendered through the app's HTTP API; the CLI path must be validated at the start of the next job (§5, stage 0). |
| **ACE-Step 1.5** (local, MIT) | Music generation. |
| **You** | The sign-offs above. |

---

## 2. The pipeline at a glance

```
image ─► 1 Intake ─► 2 Scene analysis ─► 3 Prompt ─► 4 Drift probe ─► 5 Two clips (A,B)
                     (job.json + masks)                (pick seeds)         │
                                                                             ▼
   9 Deliver ◄─ 8 Full hour ◄─ 7 Music+ambience ◄─ [Sign-off A] ◄─ 6 Loop build + QC
   + cleanup     (mux, QC)      (30 s samples)                       (composite on locked plate)
   [Sign-off C]  [Sign-off B]
```

Design principles (each one paid for by a failure in job 001):
1. **Only the parts that should move come from AI video.** Everything else is the original image, pixel-locked by a mask. This is what makes the loop stable.
2. **The loop is built, not generated.** Never ask the model to loop. Make two clips from the same image and chain A → B → A with crossfades.
3. **Measure the camera first.** Image-to-video models drift and zoom. If the camera moves, nothing else matters. Test drift on 2–3 seeds before rendering anything final.
4. **Describe a photograph, not a scene.** The prompt says what is frozen and lists the only things that move. Never write "the camera does not move".
5. **One heavy thing at a time on the 64 GB Mac.** Video model, music model and LLMs never run together.
6. **Every stage has numbers.** A stage is done when its gate passes, not when it looks fine.

---

## 3. Environment (one-time setup, already done on this machine)

| Item | Where / value |
|---|---|
| Machine | Apple M5 Max, 64 GB unified memory, macOS |
| Project | `/Users/justin/Code/Project-V/Video-Zen1` (private GitHub repo `justinyang13/Video-Zen1`) |
| Models folder (flat, single) | `/Volumes/SSD-4T-LR/AI/Models` (exFAT SSD). Draw Things is set to it as its External Model Folder. **Never download a model that already exists there.** New downloads go there. |
| Video model | `ltx_2.3_22b_distilled_1.1_q8p.ckpt` (+ Gemma 3 12B encoder, LTX 2.3 VAE, upscalers) already in the models folder |
| Music model | ACE-Step 1.5 at `tools/ACE-Step-1.5` (git-ignored; re-clone with `git clone https://github.com/ACE-Step/ACE-Step-1.5.git`, then `uv sync`). Weights on the SSD in `/Volumes/SSD-4T-LR/AI/Models/ACE-Step`; `tools/ACE-Step-1.5/checkpoints` is a **symlink** to that folder. |
| Python | `.venv` (Python 3.14) with `numpy opencv-python-headless pillow requests markdown pygments`. ACE-Step has its own `.venv` (Python 3.12) via `uv`. |
| Other tools | `ffmpeg`, `uv`, `gh` (logged in as `justinyang13`), `draw-things-cli` (Homebrew tap `drawthingsai/draw-things`) |
| Access | Claude app has **Full Disk Access** (needed once to read Draw Things' sandbox; can be turned off) |

---

## 4. Parameters (defaults that worked; change only with a reason)

| Parameter | Value | Why |
|---|---|---|
| Plate crop | 16:9 crop of the image, scaled to 1920×1080 | Output size |
| Generation size | **1024×576** (multiples of 64!) | Draw Things rounds down to a multiple of 64 and squashes the picture otherwise |
| Clip length | **145 frames** (8n+1) each, two clips | Draw Things caps one request at **201 frames**; LTX needs 8n+1 |
| Loop | period 240 frames = 10.000 s at 24 fps; crossfade 24 frames (1 s), equal-power / smoothstep | 240 = 2 × 120; exactly 360 loops = 1 hour |
| Video model settings | 8 steps, sampler TCD Trailing, shift 5, CFG 1 (the distilled model ignores the negative prompt and guidance overrides) | Recommended preset of the model |
| Seeds | probe 101, 202, 303; clips A and B use two seeds that passed | Drift is seed-dependent |
| Music pieces | 150 s each, 8 s crossfades, ~26 pieces for 1 h | 240 s pieces crashed the music server |
| Music style | slow soft piano, 40–46 BPM, keys D minor / F major / A minor / C major / G minor | Chosen by the user; see [Music](wiki/music.md) |
| Loudness | music −22 LUFS, ambience −36 LUFS (14 dB under), final peak ≤ 0.89 | Comfortable for hours |
| Audio filters | low-pass 6.5 kHz, high-shelf −3 dB above 3 kHz, slow leveler (−8…+3 dB over ~20 s) | Removes harshness and loudness swings |
| Final encode | H.264 stream-copied from the loop (no re-encode), AAC 256 kbps, `-movflags +faststart` | 1.1 GB per hour |

---

## 5. Stages

Legend: **C** = Claude does it · **S** = script does it · **U** = user sign-off.

### Stage 0 — Preflight (S/C, ~2 min)
- Models present in `/Volumes/SSD-4T-LR/AI/Models`; disk free ≥ 10 GB; SSD mounted.
- Nothing heavy running (`ollama ps` empty; no stray renders; `pgrep -fl "DrawThings|acestep"`).
- **For CLI rendering:** ask the user to quit the Draw Things app (the CLI loads its own ~35 GB copy of the model).
- **[UNVERIFIED] Validate the CLI once** before relying on it: render one 145-frame clip with
  `DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models draw-things-cli generate --model ltx_2.3_22b_distilled_1.1_q8p.ckpt --no-download-missing --image plate.png --frames 145 --width 1024 --height 576 --seed 101 --prompt-file prompt.txt -o clip.mov --video-format prores422hq`,
  extract frames with ffmpeg, and check that (a) frame count and size are right, (b) drift ≤ 0.7 px (stage 4), (c) the settings match the API path (steps 8, TCD Trailing, shift 5, CFG 1; override with `--config-json` if not), (d) whether the 201-frame cap applies. Record the result in `wiki/lessons.md`. If the CLI fails, fall back to the HTTP API (Runbook §G-API) and tell the user.

### Stage 1 — Intake (C, 1 min)
1. Copy the image to `input/<id>.<ext>` with `<id>` = next number + slug (e.g. `002-forest-cabin`).
2. Read the size; view the image.
3. Create `jobs/<id>/` and copy `jobs/001-snow-tea/job.json` and `prompts.md` as starting points.

### Stage 2 — Scene analysis and masks (C, 10–20 min) → `job.json`
1. **Motion inventory.** List every element that could move and decide how. Use the catalog in §6. Anything not listed as moving stays frozen.
2. **Crop.** Choose a 16:9 crop of the source (`plate.crop`). Prefer cropping small margins over letterboxing.
3. **Regions** (polygons in **source pixels**):
   - `animated`: the area where AI motion is allowed. Its edges must sit on **real edges** in the picture (door/window frames, table edges, object silhouettes) so the join is invisible.
   - `lock`: foreground objects that overlap the animated area and must stay pixel-identical (table, cup, blanket, lamp…).
   - `qc_only`: small boxes around each effect to measure (snow area, steam box, fire box). Not composited.
4. **Draw an overlay and look at it** (tint the animated area; outline lock/QC boxes; also view a 2× zoom of the tricky part). Adjust until edges are right. Save as `jobs/<id>/mask_overlay_v0.png`. Expect 2–3 adjustments.
5. **Watch for:** frozen particles in the still that sit in *locked* areas (e.g. snow specks on a blanket) — lock them so they can't animate; steam/smoke that starts inside a lock region — start the steam box just above the object's rim; light sources that should flicker; reflections.
6. **Output:** `jobs/<id>/job.json` (schema in §7).
- **Gate:** overlay reviewed; polygons on real edges; every moving thing is inside an animated region.

### Stage 3 — Prompt (C, 5 min) → `jobs/<id>/prompts.md`
Use template P5 (§8). Fill `{FROZEN}`, `{MOTION}`, `{MOOD}`. Only name things that must move, with direction and speed.

### Stage 4 — Drift probe (S+C, ~10 min)
For seeds 101, 202, 303 render a 121-frame clip at 1024×576 and measure:
- `qc_drift.py` → **worst drift ≤ 0.7 px** (camera zoom/shift of the room; on job 001 good seeds gave 0.1 px).
- `qc_motion.py` → the effects actually move: snow **moving down ≥ 65 %**, steam **moving up ≥ 60 %**, fire/flicker **activity > 0** (frame diff and luma std over time). Edit the region table at the top of the script for the new image (formula in Runbook §Q).
- Contact sheets (full frame, plus crops of each effect) — Claude looks at them.
- **Gate:** ≥ 2 seeds pass. If < 2: change the prompt using the levers in §9 (max 4 rounds), then rerun. If still failing: see §9 "fallback: stabilize".

### Stage 5 — Two clips (S, ~6 min)
Render clip **A** and clip **B**: 145 frames each, the two best seeds, same prompt. Both start from the identical image, so they cannot drift apart.

### Stage 6 — Loop build and QC (S+C, ~2 min) → Sign-off A
`loop_build.py` builds the 240-frame loop: `[0,24)` B's tail fades into A's head; `[24,120)` A; `[120,144)` A fades into B; `[144,240)` B. AI pixels are composited only through the feathered animated mask, over the original plate at 1080p; locked pixels stay identical.
- **Gates:** `seam_ratio ≤ 1.3` · `locked_pixels_identical = true` · `luma_std_detrended ≤ 1.0` · `luma_max_jump ≤ 1.5`.
- Claude looks at the seam sheet (frames 232–239 then 0–7) and one full-size frame.
- **U — Sign-off A:** the user watches the loop repeating. Job 001: loop point invisible; fire, steam, snow right.
- Then keep the loop MP4; the frames are scratch.

### Stage 7 — Music and ambience (S+C+U, ~10 min) → Sign-off B
1. Start the ACE-Step server; generate **three 30-second samples** in different styles (default trio: low flute + pad, soft piano + faint flute, koto + faint flute), each **with an explicit `--bpm` (~44–48) and `--key`** (the model's own planner ignores "slow"). Soften and level them (Music §Recipe). Send to the user.
2. **U:** picks one. If none: adjust the prompt from their words (slower, softer, less reverb, different instrument) and repeat (each sample takes ~10 s).
3. Add ambience at −14 dB under the music; send a mixed 30 s plus an ambience-only louder version.
4. **U — Sign-off B:** approves level and character of the ambience.
- Claude cannot hear: never claim it "sounds good". Report only measurements (LUFS, tempo, key) and the user's verdict.

### Stage 8 — Full hour (S, ~15 min) → Sign-off C
`music_build.py --minutes 60` generates ~26 pieces (150 s), crossfades them, applies the slow leveler, mixes the ambience (generated in 124 s chunks with different seeds), fades in 3 s / out 10 s, and writes the AAC. Then mux with the looped video (stream-copy, no re-encode).
- **Gates:** duration exactly **3600.000 s**; video packets **86,400**; integrated ≈ −22.5 LUFS; peak ≤ 0.89; **no 3-second near-silent stretch**; 10-second-window loudness std ≤ ~3 dB with no window > 6 dB above the median.
- **U — Sign-off C:** listens to two excerpts (one across the first crossfade, one at the midpoint) and spot-checks the file.

### Stage 9 — Deliver, clean up, document (C, ~5 min)
1. Rename to the three final names (§1.2); delete everything else under `output/` and all scratch (`work/`).
2. Fill `wiki/runs/<id>.md` (what was done, numbers, verdicts, surprises); add anything new to `wiki/lessons.md`.
3. `python scripts/build_docs.py` to regenerate `docs/*.html`.
4. Commit and push to the private repo.
5. Tell the user the file paths and remind them of the YouTube steps (§10).

---

## 6. Motion catalog

What was **proven** in job 001: snow, fire, steam. Others are expectations only.

| Effect | Prompt phrase (goes in `{MOTION}`) | Direction / speed | Measure | Status |
|---|---|---|---|---|
| Snow | "tiny snowflakes falling gently downward outside" | down, slow | `moving_down ≥ 65 %` | **Proven** (97–98 %) |
| Fire / candle / lantern flame | "the small brazier flame flickering" | in place, irregular | luma std over time > 0, shape changes | **Proven** |
| Steam from a cup | "thin steam curling up from the tea cup" | up, thin | `moving_up ≥ 60 %` | **Proven** (92–94 %) |
| Rain | "fine rain falling straight down" | down, fast-ish | as snow | [UNVERIFIED] |
| Smoke / incense | "a thin thread of smoke rising and curling" | up | as steam | [UNVERIFIED] |
| Fog / mist | "slow drifting mist" | sideways, very slow | flow magnitude | [UNVERIFIED] |
| Falling leaves / petals | "a few leaves drifting slowly down" | down, slow, sparse | as snow | [UNVERIFIED] |
| Water ripples / stream | "gentle ripples on the water" | local | frame diff | [UNVERIFIED] |
| Clouds / stars twinkle | — | — | — | [UNVERIFIED], likely hard |

Rules: at most **3–4 moving things** per image; every one needs a region; describe direction and speed; never use "wind/gust" unless intended.

---

## 7. `job.json` schema

```json
{
  "id": "002-forest-cabin",
  "source": "input/002-forest-cabin.webp",
  "source_size": [W, H],
  "plate": { "crop": [x0, y0, x1, y1], "output_size": [1920, 1080] },
  "loop":  { "period_s": 10.0, "fps": 24, "crossfade_s": 1.0 },
  "regions": {
    "exterior": { "role": "animated", "poly": [[x,y], ...], "feather_px": 4 },
    "steam":    { "role": "animated", "poly": [[x,y], ...], "feather_px": 8 },
    "lock_table": { "role": "lock", "poly": [[x,y], ...] },
    "fire_qc":  { "role": "qc_only", "poly": [[x,y], ...] },
    "snow_qc":  { "role": "qc_only", "poly": [[x,y], ...] }
  }
}
```
All polygons are in **source pixels**. `loop_build.py` requires a region named `exterior` (used for the feather width) — keep that name for the main animated area. Full working example: `jobs/001-snow-tea/job.json`.

---

## 8. Prompt templates

**P5 — strict cinemagraph (video, the one that works):**
```
Cinemagraph loop. One single locked photograph on a tripod: the framing is identical in every frame, {FROZEN} stay pixel-still. The only motion in the entire image is {MOTION}. Photorealistic, calm, {MOOD}.
```
Job 001: `{FROZEN}` = "the doorway, table, cup, blanket, lamp, lanterns and trees"; `{MOTION}` = "tiny snowflakes falling gently downward outside, the small brazier flame flickering in the garden, and thin steam curling up from the tea cup"; `{MOOD}` = "cozy winter night".

**Do not write:** "the camera does not move / never zooms / never pushes in" (made drift *worse*: 20–25 % zoom), long descriptive scene text (15 % zoom), or rely on the negative prompt (ignored at CFG 1).

**Music prompt (approved on job 001):** *"Very slow, soft, gentle ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, a faint distant low flute and a warm airy pad far in the background. Peaceful, calm, tender, sleepy, {SCENE}. no drums, no percussion, no vocals, no sharp sounds."* with `--bpm 44` and a key. `{SCENE}` = e.g. "Japanese winter night".

---

## 9. When something fails (decision table)

| Symptom | Likely cause | Do this |
|---|---|---|
| Camera zooms or shifts (drift > 0.7 px) | Prompt primes camera motion; seed | Use P5; remove camera words; fewer moving things; try more seeds. **Fallback [UNVERIFIED]:** stabilize each frame to frame 0 with a similarity transform (features in the room area), then fill the thin edge with replicated pixels |
| Only 1 of 3 seeds passes | Normal (seed-dependent) | Try seeds 404, 505; use the passing seed for A and any second passing seed for B; if only one passes, use it for both A and B with a different noise (different seed but the same prompt) and re-check drift on the built loop |
| Effect too weak/absent (steam, fire) | Too many things in the prompt | Put the weak effect first in `{MOTION}`; say "clearly visible"; as last resort, a separate close-up clip of just that region composited through its mask (see `jobs/001-snow-tea/prompts.md` region passes) **[UNVERIFIED]** |
| Snow moves up or sideways | Model artifact | Add "falling straight down"; other seed |
| Visible seam at mask edge | Polygon not on a real edge | Redraw on the frame/edge; increase `feather_px` 4 → 8 |
| Seam ratio > 1.3 | Big change between A's tail and B's head | Different seed for B; lengthen `crossfade_s` to 1.5 |
| Brightness pulsing | Model drifts in exposure | Different seed; check `luma_std_detrended` |
| Draw Things HTTP 422 | Sent the full config dump / size not multiple of 64 / frames > 201 | Send only the whitelisted keys (Runbook §G-API); check size and frame count |
| Music server dies mid-request | 240 s piece crashes VAE decode | 150 s pieces; `music_build.py` restarts and retries automatically |
| Music model downloading to the wrong disk | `.env` path ignored | `checkpoints` symlink to the SSD (Environment §3) |
| "Too harsh / too fast" | Planner picked 91–120 BPM; bright top end | Set `--bpm` and `--key`; low-pass; describe "warm, low, rounded" |
| Out of memory / slow | Two heavy models loaded | Quit the Draw Things app before CLI; stop the music server before video; `ollama stop <model>` |

**Stop rule:** after 4 failed prompt rounds in stage 4, stop and report the numbers and contact sheets to the user with a recommendation; do not burn more GPU time unattended.

---

## 10. YouTube notes (from web search, 2026-09-23 — check current policy yourself)
- No YouTube feature loops a short video under a longer audio track: upload the one-hour file. 1.1 GB ≈ 8 min at 20 Mbps upload (30 min at 5 Mbps), plus YouTube's processing time.
- In YouTube Studio: **Create → Upload videos**, fill title/description, answer the **altered or synthetic content** question with **Yes** (AI-generated video and music).
- YouTube's "inauthentic content" (repetitive / mass-produced) policy is enforced **per channel** and is reported to hit ambient/lo-fi channels often. Vary the scenes and music across videos; don't upload dozens of near-identical hours.
- The music is generated locally with an MIT-licensed model; no third-party tracks are used. The user cited free Japanese BGM sites as a *style* reference only; nothing was downloaded from them.

---

## 11. Budget (job 001 actuals, M5 Max 64 GB)

| Item | Machine time |
|---|---|
| Drift probes (3 × 121 frames @ 1024×576) | ~8 min |
| Clips A + B (2 × 145 frames) | ~6 min |
| Loop build + QC | ~1 min |
| Music: samples | ~1 min (10 s each once the model is downloaded) |
| Music: 26 pieces + ambience + mix + AAC | ~15 min |
| Mux | seconds |
| **Total (happy path)** | **~30–35 min**, plus your listening time |

First-run extras (already done): ACE-Step model download 9.6 GB (~12 min at 2.2 MB/s).
Job 001 actually took longer because of the camera-drift investigation (~8 test clips) and prompt/music iterations.

---

## 12. Known limits and next improvements (not done)
1. **Job-specific hard-coding.** `qc_motion.py` has the region table hard-coded for job 001; `music_build.py` has the music prompt as a constant; `ambience.py` only makes fire/wind/crackle. A new image needs Claude to edit these (Runbook §Q, §M). Best next step: read all of it from `job.json`.
2. **CLI switch** is required by the user but **[UNVERIFIED]** (stage 0).
3. **Single orchestrator** (`pipeline.py` running all stages) does not exist; stages are run one by one from the Runbook.
4. **Other ambience types** (rain, waves, forest, night insects) need new synthesizers.
5. **Other lengths** (30 min, 3 h, 10 h) only need `--minutes` and `-stream_loop` changed; not run.
6. **Wan 2.2 I2V** isn't installed (only the T2V expert is); LTX-2.3 was enough.
7. Local vision-model QC (Ollama) was planned but not used; Claude read the sheets directly.
