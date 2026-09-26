# SPEC — Video-Story1: "Mei and the Dragon Who Feared Thunder" book trailer

Status: **v0.2: trailer produced 2026-09-26 (see RUNLOG 25–33); the spec below is the plan as written, with the actual method changes recorded in RUNLOG and LESSONS** · v0.1 2026-09-25 · Companion files: [CANON.md](CANON.md) (the locks) · [RUNLOG.md](RUNLOG.md) (the running record of every step) · `research/` (local-AI reports) · `input/refs/` (book text, bible, style, cover art).
Items not yet proven on this machine are marked **[UNVERIFIED]** and become Stage 0 tests. Values marked **[TBD-S0]** are set from the Stage 0 results, not guessed.

---

## 1. Contract

### 1.1 What this is
A **60–90 second trailer** (target ≈ 75 s) that "brings the book to life": the book's own painted look, the book's own characters, moving gently, with a read-aloud narrator, soft music and sound, and on-screen words taken **only from the book**. It is a trailer, not the whole story. It is also the proving ground for a repeatable book-to-video method.

### 1.2 Decisions already made by you (2026-09-25)
| # | Decision |
|---|---|
| D1 | Length: 60–90 s trailer. |
| D2 | 16:9 landscape for YouTube, 1920×1080, 24 fps. |
| D3 | Look matches the book watercolor/gouache art "down to exact" (CANON §1). |
| D4 | Yun is the **cover version, exactly** (serpentine; CANON §3). |
| D5 | Narrator voice: Claude picks (candidates researched by local AI; Stage 0). Narrator only, no character voices, no lip-sync; key quoted lines appear as on-screen text. |
| D6 | Soft music with traditional instruments; the thunder sounds joyful, not scary. |
| D7 | Not for the Zen Hour Music channel. The language rule applies: the words "Chinese", "Taiwanese", "Japanese", "Korean" never appear. Use **the book's titles and words only** (title, subtitle, tagline, blurb sentences, chapter tally lines, quoted dialogue). |
| D8 | Free downloads are allowed (open licence, no cost). Claude states name, size and licence in RUNLOG before each download. |
| D10 | **Picture model: Z Image Turbo for this project only** (decided 2026-09-25 after T0.1: it reproduces the book/cover look, FLUX.2 klein does not). The standing "FLUX.2 klein only" rule stays for other Project-V videos. |
| D9 | Work is documented step by step (§10). Local AI does as much as it can (§9). |

### 1.3 What you get (`output/`)
| File | What |
|---|---|
| `Video-Story1_trailer_1080p24.mp4` | The trailer: 1920×1080, 24 fps, H.264 + AAC 256 kbps, ≈ 75 s (60–90 s). |
| `Video-Story1_audio.m4a` | The full mix (narration + music + sound), kept separately. |
| `Video-Story1_silent_1080p24.mp4` | The picture only, to re-mux with other audio. |
| `Video-Story1_captions.srt` | Captions = the narration and on-screen lines (book words). |
| `Video-Story1_thumbnail.png` | 1280×720 thumbnail from the cover art (book title only). |
Kept in the folder besides `output/`: `SPEC.md`, `CANON.md`, `RUNLOG.md`, `RUNBOOK.md`, `LESSONS.md`, `input/` (canon sheets, refs, approved keyframes), `jobs/` (prompts, seeds, ledger, settings). Scratch in `work/` is deleted at the end.

### 1.4 Approvals (the only times you are needed)
| Gate | You approve | Before |
|---|---|---|
| **G1** Canon sheets | Mei, Tao, Hua, Nainai, Yun (cover-exact, plus how the pearl is drawn), Uncle Shi, Yeye Gu, Old Grey, and the key places. | any shot is made |
| **G2** Script + shot list | The 13 shots, the words, the timing. | keyframes |
| **G3** Keyframes | One still per shot, as contact sheets, each already checked against the checklist (§5.4). | any video render |
| **G4** Animatic | Stills + temporary narration + temporary music, in order, with timing. | heavy rendering |
| **G5** Motion | 3 hero shots animated (Yun reveal, bridge, thunder) then the rest. | the full mix |
| **G6** Final | The finished trailer (you watch, you listen; Claude cannot hear or watch, so it gives measurements). | delivery |

---

## 2. Draft trailer script (all words from the book) — for G2

Total ≈ 75 s: 13 shots of about 4.5–6 s, then a 6 s end card. Narration lines are the book's own back-cover sentences; the two quoted lines are the book's dialogue (p024, p049, p060, p090). On-screen lines are book text too.

| Shot | Sec | Picture (book page it grows from) | Who is in it | Narration (verbatim from the book) | On screen |
|---|---|---|---|---|---|
| S01 | 6.0 | Dawn kitchen: Nainai cuts a notch in the bamboo stick, Mei watches [p001] | Nainai, Mei | "Every morning Mei's grandmother cuts a notch in a bamboo stick, and every morning the sky stays empty." | *Days without rain: 114* |
| S02 | 5.5 | Terraces, yellow seedlings, Uncle Shi pours tea from the thermos on them [p004] | Uncle Shi (Mei small, far) | "The wells of Bamboo Ridge Village are almost dry, the rice seedlings are turning yellow," | |
| S03 | 5.0 | Shrine at midday: the paper dragon lying still, a cloudless sky [p014] | Uncle Shi, Auntie Fen, villagers | "and the rain-asking at the shrine has failed." | |
| S04 | 5.0 | Yeye Gu with an oil lamp, mist ribbon on the far mountain [p017] | Yeye Gu | "Then someone remembers the old story of the dragon of Black Pool, high on the mountain." | |
| S05 | 5.5 | Mei stands up in the meeting, hand on the bench [p024–025] | Mei, Uncle Shi, Nainai | "Mei, who freezes whenever she has to speak up, is the only one who says, 'I'll go.'" | *"I'll go."* |
| S06 | 5.5 | Bamboo forest path, striped light [p031] | Mei, Tao, Hua, Old Grey | "With her chatty little brother in yellow rain boots, a know-it-all classmate who is secretly afraid of heights, and a patient water buffalo," | |
| S07 | 5.5 | Rope bridge, Hua steps out, Mei walks backwards facing her [p039] | Mei, Hua (Tao, Old Grey ahead) | "she climbs through bamboo, over a rope bridge and into the clouds." | |
| S08 | 5.0 | Black Pool: mist, cracked mud, one amber eye over a rock [p050] | Yun (eye, antler), Mei, Tao, Hua small | "At the top she finds a dragon who is kind, polite and absolutely terrified of his own thunder." | *"I am very sorry, but nobody is here."* |
| S09 | 6.0 | **Hero:** Yun rises from behind the rock, mist scarf, exact cover design [p051 + cover] | Yun, the children small | (music only) | |
| S10 | 6.0 | Mei small before Yun, eye to eye [p060] | Mei, Yun | "Can a girl who cannot raise her voice help a dragon who will not raise his?" | *"Because so am I."* |
| S11 | 5.0 | Village dusk, lanterns, drum, pots; Yun rises out of the bamboo, pearl glowing [p088–090] | Mei, villagers, Yun | (music swell) | *"We are here."* |
| S12 | 4.5 | **Hero:** the thunder: Yun above the roofs, mouth open, gold ripples; village answers [p092–093] | Yun, villagers, Old Grey | (thunder + drums + shouts) | |
| S13 | 5.5 | The first rain: Tao stomps a puddle in the yellow boots, Nainai laughs, Mei looks up [p094–095] | Tao, Mei, Nainai, Yun small above | (rain, music) | |
| End | 6.0 | Cover art (still, slow push-in) | Mei, Yun | (music out) | **MEI AND THE DRAGON WHO FEARED THUNDER** · *One Dry Spring, One Shy Dragon and One Very Small Voice* · *Some voices shake. Use them anyway.* |

Narration ≈ 105 words ≈ 40 s at a warm read-aloud pace; the rest is music, sound and silence. **[TBD-S0]** final durations are re-cut to the recorded narration at G4.
Open for G2: keep the "sound of nothing" opening (2 s of near-silence) · whether the trailer should show the thunder or hold it back · caption style.

---

## 3. Pipeline at a glance
```
0 Tech tests ► 1 Canon sheets ─G1─► 2 Script+ledger ─G2─► 3 Keyframes ─G3─► 4 Animatic ─G4─►
   5 Animate (3 hero shots, then all) ─G5─► 6 Audio (voice, music, sound, mix) ► 7 Assemble+text ─G6─► 8 Deliver+clean up
```
Design principles (each from a failure in Project-V or this book):
1. **Consistency is the product.** Text prompts alone drift (the book proves it). Every image uses the locked identity strings *and* approved reference images (§5).
2. **Approve first, render later.** Nothing heavy runs until G1–G4 pass.
3. **Every stage has numbers.** A stage is done when its gate passes, not when it looks fine.
4. **Motion never touches identity.** If the video model bends a face, the shot falls back to a still painting with procedural motion (§6.3).
5. **No words inside pictures.** Text is added in the edit with the book's fonts (T2I cannot spell).
6. **One heavy model at a time** on the 64 GB Mac (image, video, TTS, music, big LLMs never together; a small Qwen may run beside Draw Things).
7. **Never idle** (§9): long jobs run in the background with time limits; something useful runs meanwhile.

---

## 4. Stage 0 — Tech tests (each ends with a written verdict in RUNLOG)
| Test | Question | Method | Pass gate |
|---|---|---|---|
| **T0.1 Style match** (done) | Does the image model reproduce the book's look "down to exact"? | Same book prompt (CANON §1 + cover prompt), FLUX.2 klein 9B (your standing choice for Project-V) vs the book's original generator Z Image Turbo, 3 seeds each, side by side with the cover. | You judge "same look". If only Z Image Turbo matches, Claude asks you for a one-time exception for Video-Story1. **Result 2026-09-25: Z Image Turbo matches the cover almost exactly (seed 733), klein 9B does not (RUNLOG 7–8). Decision needed from you (§12 item 2).** |
| **T0.2 Consistency method** | Which method keeps Mei / Tao / Hua / Yun identical across poses? | A: Z Image Turbo with the canon crop as image-to-image start (low strength) plus the identity strings and locked seeds (the book's method, made stricter). B: a small **character LoRA** per character, trained locally (`draw-things-cli train lora`). C: Qwen-Image-Edit-2511 (free, Apache 2.0) edit-from-reference. Each renders the same 6 test poses/places for Mei and for Yun. | Checklist score ≥ 95 % of must-have attributes (§5.4) on ≥ 5 of 6 poses **[TBD-S0 for exact threshold]**; multi-character frame (Mei + Yun) also passes. Pick the method with the best score; keep the runner-up as fallback. |
| **T0.3 Image-to-video on painting** | Will LTX-2.3 keep a painted face stable and keep the painted texture? | One Mei + Yun keyframe, 3 seeds, 145 frames at 1024×576 (Project-V lesson A19: test at the final length), gentle-motion prompt. Measure drift (`qc_drift.py`), luma drift, face/hand look on frame contact sheets. | Camera drift, luma drift and identity checks pass **[TBD-S0 thresholds from the best sample]**; otherwise use the §6.3 fallback for that shot type. |
| **T0.4 Upscale to 1080p** | 1024×576 → 1920×1080 without mush | Lanczos vs LTX spatial upscaler ×1.5/×2 (both installed) on one clip. | Painted line and paper grain still visible; you agree on a 2×2 crop. |
| **T0.5 Narrator voice** | Which free local TTS sounds warm and natural? | Candidates from `research/tts_report.md` (Kokoro-82M, Chatterbox, others). Read S01 + S05 lines, 2 voices each. | Claude picks by measured cleanliness (no clicks, steady level) and shortlist; you hear 2 finalists at G4. |
| **T0.6 Sound & music** | Do ACE-Step and MOSS give the needed cues? | 30 s ACE-Step music prompt (bamboo flute, zither, soft strings); MOSS clips: bamboo wind, distant bell, soft rain, joyful thunder. | `audio_qc.py` clean on music and beds; thunder allowed to be loud but must not clip or startle (peak ≤ −3 dBFS, no harsh band). |

---

## 5. Consistency system (the core)

### 5.1 Canon sheets (Stage 1, gate G1)
For each main character: full-body front, 3/4, side, back, and 5 faces (neutral, worried, glad, amazed, sad) in the exact book style on a plain cream ground; for Yun: head close-up (the cover head), full serpentine body in mist, and three states of the pearl. For places: Black Pool, the shrine yard, the kitchen, the bridge, the bamboo path, the terraces (dry, and wet/green), each in day and in dusk/night where used. Props on one sheet. Files: `input/canon/<name>_<view>.png`, an index `input/canon/INDEX.md` (seed, model, method, prompt). **Yun's head must match the cover crop; G1 compares them side by side.**

### 5.2 Identity strings
CANON §2–3 strings are pasted verbatim, in a fixed order, into every prompt (script `scripts/story_prompt.py` builds prompts from a shot record; no hand-typing).

### 5.3 Continuity ledger (`jobs/ledger.csv`, drafted by Qwen from the book text, corrected by Claude)
One row per shot: shot id · book page · day (114–120) · time of day · weather/sky state · location · characters present · for each: clothing/props/pose/expression · water & ground state · seedling colour · pearl state · Mei's bangs · tally line shown · camera (framing, direction of gaze) · left/right positions (screen direction stays consistent across a scene) · notes. No keyframe is made without its row.

### 5.4 Keyframe checklist (Claude, on every image)
For each character in frame, tick each **must-have** (Mei: two braids + red string, blue padded jacket with knot buttons, straw hat; Tao: green tiger shirt, yellow boots, gap teeth; Hua: red jacket, yellow ribbon; Nainai: grey bun, dark blue jacket; Yun: cover-exact head, antlers, mane, scales, amber eyes, no wings; plus the world/state items in the ledger row). Also: **no text or letters in the image, no extra people, correct hands (5 fingers) and correct number of characters.** Score = ticks ÷ must-haves. Fail → reroll (new seed, up to 3), then change method for that shot. Every reroll is logged.
Secondary check: a local vision model or colour probes (e.g. yellow pixels in Tao's boot region) **[UNVERIFIED]**; never a replacement for Claude's own look at each image.

### 5.5 What is fixed for the whole film
Aspect 16:9 · painterly style prefix · palette per CANON §1 · lens: gentle wide/medium, no fisheye · screen direction (village at left, mountain path leading right and up) · character scale (Yun is farmhouse-sized; Mei reaches Tao's shoulder... Tao is 7, Mei 11, Hua tallest of the children).

---

## 6. Images and motion

### 6.1 Keyframes (Stage 3)
Model: **Z Image Turbo** (`z_image_turbo_1.0_q8p.ckpt`, decision D10; the book's own generator, so the same style prefix and seeds reproduce its look); 1920×1088 (Draw Things rounds to a multiple of 64; crop to 1920×1080), 4 candidates per shot (seeds in `jobs/`), the method chosen in T0.2. Contact sheets per scene with ids and seeds. All settings, prompts and seeds are saved in `jobs/keyframes.json`.

### 6.2 Animate (Stage 5)
LTX-2.3 22B distilled via `draw-things-cli generate --image <keyframe>` **[verified in Project-V A20]**, 145 frames (≈ 6.04 s, 8n+1) at 1024×576, one clip per shot, trimmed to the shot length, then upscaled per T0.4. Prompt = "photograph the painting" style from Project-V: list what stays frozen and the few gentle motions (mist drifting, bamboo leaves swaying, hair and cloth moving slightly, lantern flicker, breathing), **never mention the camera**; slow push-in is added in the edit, not asked of the model. 3 seeds per hero shot, 2 per other shot, best chosen by the numbers and by Claude's frame sheets.
Gates per clip **[TBD-S0]**: camera drift, luma drift over the full 145 frames, first/last-frame identity against the keyframe (checklist on frames 1, 36, 72, 108, 145), no morphing hands, painterly texture kept (no photoreal drift).

### 6.3 Fallback: painting with procedural motion
If a clip fails twice, the shot is built from the approved still: depth map (Depth Anything V2 Small, installed) for a slow 2.5-D parallax push, plus procedural layers made seamless by construction (drifting mist, bamboo/leaf sway, dust, lantern flicker, rain from `rain_overlay.py`). Identity is perfect by design. Any shot may use this; hero shots try video first.

### 6.4 Assembly of picture
ffmpeg cut of the 13 clips + end card, gentle 8–12-frame crossfades or hard cuts on beats (chosen at G4), colour matched shot to shot (one grade for the whole film), 1080p24. Title and text cards drawn in HTML with the cover's fonts and colours (`#fff1c9` title, `#ffcf6a` accent) and composited with ffmpeg.

---

## 7. Audio (Stage 6)
| Layer | Tool | Notes |
|---|---|---|
| Narration | local TTS chosen in T0.5 | Warm, gentle, female read-aloud, unhurried; lines only from §2; pauses tuned at G4. Claude cannot hear: it checks for clicks, level steadiness and clipping numerically; you approve by ear. |
| Music | ACE-Step 1.5 (`scripts/music_gen.py`), instrumental | Bamboo flute + zither + soft strings, pentatonic, warm; Claude sets bpm/key (start ~72 bpm, D major pentatonic) and writes the prompt; 30 s tests then one ≈ 80 s piece with an intro that leaves room for voice and a swell at S11–S12. Checked with `audio_qc.py` (screech, harshness, clicks, clipping, dropouts). |
| Sound | MOSS-SoundEffect (`scripts/rain_gen.py` style) | Bamboo wind, distant bell/Old Grey's brass bell, the "sound of nothing" opening, drum + pots + spoons, **joyful thunder**, soft rain. Many clips fail QC in Project-V (19/49): generate many, keep the clean ones. |
| Mix | ffmpeg | Music ducked under narration; final ≈ −14 LUFS integrated, true peak ≤ −1 dBTP; ebur128 report saved in `qc-report.md`. Thunder peak allowed higher than music but ≤ −3 dBFS pre-master, no clipping. |

---

## 8. Text and captions
- Everything on screen is from §2 (book words). Two kinds: tally card ("Days without rain: 114") and quote cards. Serif italic for tally as in the book; the end card uses the cover's title lockup. Composed as HTML → PNG/alpha → ffmpeg overlay, timed to the narration.
- Captions: `.srt` from the narration timings (book words only).
- **Language check (automatic, blocking):** a script greps every text file, caption, card and metadata field for "Chinese|Taiwanese|Japanese|Korean"; any hit fails the build.

---

## 9. Roles and never-idle rules
| Who | Does |
|---|---|
| **Claude** | Director/QA: plans, writes prompts and specs, views every image and contact sheet, applies the checklist, reads the numbers, decides rerolls, talks to you at gates. Cannot hear or watch motion: uses frame sheets, measurements and your ears. |
| **qwen3.8:27b** (Ollama, direct API) | Research (`research/*.md`), first-draft ledger from the book text, caption/SRT timing draft, text-language check reviews, log summaries. Its output is spot-checked (it invents details; registry lesson). |
| **qwen3-coder:30b** | Draft helper scripts (prompt builder, checklist sheet maker, mixers); Claude reviews before use. |
| **Draw Things CLI** | Images (Z Image Turbo; klein only for tests), LoRA training, LTX-2.3 image-to-video. Never the app. |
| **ACE-Step, MOSS, TTS** | Music, sound, voice. |
| **Scripts** (`Project-V/scripts/` + new `Video-Story1/scripts/`) | Deterministic rendering, measuring, mixing, QC. |
| **You** | The gates G1–G6. |

Never-idle rules (from your Claudestrator rules): every job has a time limit and runs in the background; progress is checked (output growing, process alive, `ollama ps`); on a stall: retry smaller → restart the service → switch model/tool → do it directly; while one thing renders, something else advances (e.g. keyframes render while Qwen drafts the ledger and research). Only one heavy model at a time.


### 9.1 Delegation plan for local AI (v1, 2026-09-25)
Principle: Claude owns goals, prompts that decide the look, every look at pictures, and every gate. Local models do the bulk work that has a checkable answer. Every local output passes Claude's quality gate; up to 3 rework rounds, then Claude does it.

| Stage | Local worker | Task | Claude checks | Known limit |
|---|---|---|---|---|
| Research (0) | qwen3.8 + web tools | TTS, LoRA, LTX reports (`research/`) | Spot-check licences, install lines | Invents details; search needed a fallback |
| 2 Script/ledger | qwen3.8 | Draft `jobs/ledger.csv` from the book text per shot; find the exact book sentences for each narration/on-screen line | Every row against CANON; verbatim check by script (`grep` the book) | Pulls in later plot, slips on numbers |
| 2 Language check | script + qwen3.8 | Grep all text for the four banned words; Qwen lists any wording not in the book | Claude reads the flagged list | Qwen judgement is ~50 % false positives |
| 3 Keyframes | Z Image Turbo (Draw Things CLI) | 4 candidates per shot, from `story_prompt.py` | Claude views every contact sheet, applies §5.4 | Ignores scene words sometimes; tiny face blobs |
| 3 Keyframe pre-filter | script | Cheap probes before Claude looks: no text-like regions, colour probes (Tao's yellow, Hua's red), image size | Final call by Claude | Colour probes cannot see faces |
| 1/3 Character LoRA | Draw Things CLI `train lora` | Train Yun (and Mei if needed) on the curated set | Claude compares 6 poses against the cover | Time and quality unverified |
| Scripts | qwen3-coder:30b | Draft `story_prompt.py`, contact-sheet maker, checklist sheet, mixer, SRT builder | Claude reviews and runs on a test before use | Untested so far |
| 5 Animate | LTX-2.3 (Draw Things CLI) | 2-3 seeds per shot, overnight queue | Numbers via `qc_drift.py`, then Claude's frame sheets | Face warp risk; fallback in §6.3 |
| 6 Voice | Qwen3-TTS (Serena), Chatterbox, Kokoro | Read the narration lines, 2 voices each | Numeric audio check; user listens | Claude cannot hear |
| 6 Music / sound | ACE-Step, MOSS | 30 s tests then the piece; 50 sound clips filtered by QC | `audio_qc.py`, user listens | MOSS rejects ~60 % of clips |
| 4/7 Captions | qwen3.8 + script | Draft SRT from narration timings | Timing check against the audio length | |
| Every stage | qwen3.8 | Summarise logs, draft RUNLOG entries from job files | Claude edits and signs the entry | Its summaries can invent events |

Rules: (1) hand Qwen the source text and ask only for what is in it; never feed its own summaries back. (2) One heavy model at a time; small Qwen may run beside Draw Things (verified). (3) Use `QWEN_DEADLINE` and background runs; check with `pgrep`/`ollama ps`. (4) Record every delegated job (prompt, model, time, verdict) in RUNLOG.

---

## 10. Documentation (your request: record the steps as much as possible)
- **`RUNLOG.md`** (the "rundown file"): every step in order with date/time, what and why, exact command, parameters, seeds, model, outputs, numbers, decisions and who made them, failures and what was tried next. Updated **as work happens**, not afterwards. Entry template at the top of the file.
- **`RUNBOOK.md`**: only proven, repeatable commands (written once a step is verified), so a future book can follow it.
- **`LESSONS.md`**: what failed and why, in the Project-V table style.
- **`jobs/`**: prompts, seeds, settings, ledger, keyframe records: everything needed to re-render.
- **`RUNLOG.html`**: built with `../.venv/bin/python ../scripts/build_docs.py` (Project-V convention); rebuilt at each gate.
- Local-AI outputs (research, drafts) are kept in `research/` with the prompt that produced them.
- Git: `Video-Story1/` small files only (videos, models, scratch git-ignored); commit at each gate **only when you ask** (public repo: no secrets).

---

## 11. Risks (ranked)
1. **Character drift** across shots (main risk): mitigated by §5, measured in T0.2 and at G3.
2. **Yun cover-exactness**: the cover is a single image; the pearl is not shown; two-character (Mei + Yun) frames may bleed features. Mitigation: T0.2 tests two-character frames; LoRA/reference sheets from the cover crop; composite Mei over a Yun plate as a last resort (paint-in with masks).
3. **Video model bends faces or turns painting photoreal**: T0.3 + fallback §6.3.
4. ~~Style mismatch of the image model~~ resolved by D10. New risk: Z Image Turbo has no native reference-image input, so consistency relies on strict prompts + seeds + image-to-image + LoRAs (T0.2).
5. **Narrator sounds robotic**: T0.5; you choose at G4.
6. **Sound effects unsafe** (thunder startling, rain noise): QC + your ears.
7. **Time**: ≈ 13 shots × 2–3 attempts × ≈ 3.5 min video render ≈ 2–3 h GPU; keyframes ≈ 1 h; LoRA training time **[UNVERIFIED]**.

## 12. Open items for you (answer when convenient)
1. Approve this draft (or send changes): shot order, words, the "sound of nothing" opening.
2. ~~Z Image Turbo exception~~ **Decided: yes, this project only (D10).**
3. Where will you publish the trailer (a book/story channel?), and do you want it uploaded by Claude or by you? (Default: you upload.)
4. Should the trailer end on the cover (default) or on a new painted end frame?
