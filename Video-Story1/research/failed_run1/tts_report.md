# Local TTS for a children's-storybook narrator — Apple Silicon (M5 Max)

Research note: I verified facts directly from the GitHub/Hugging Face pages linked below; where a search returned nothing (Orpheus, Dia, Parler weights, Sesame CSM specifics, mlx-audio, Qwen3-TTS weights), I say so explicitly rather than guessing.

## Comparison table

| Model | Code licence | Weights licence | Size | Mac GPU (MLX/MPS) / CPU | Naturalness for storytelling | Pace/emotion control | Install & run |
|---|---|---|---|---|---|---|---|
| **Kokoro-82M** | MIT (kokoro pip); Apache 2.0 weights (hexgrad) | **Apache 2.0** ✅ commercial | 82M params, ~327 MB | PyTorch runs on CPU/MPS; `kokoro-onnx` claims near-real-time on M1, ~300 MB (80 MB quantized); `kokoro-coreml` runs it on the ANE (M2 Ultra: 30 s audio in 422 ms ≈ 70× real-time) | Very good for a fixed female voice (af_heart is grade "A" in the model's own VOICES.md); not a clone model | `speed` parameter only; no emotion tags | `uv add kokoro` → `from kokoro import KPipeline; p=KPipeline(lang_code='a'); gen=p("text", voice='af_heart')`; or `uv add kokoro-onnx soundfile` |
| **Chatterbox (Resemble)** — family: 500M, Turbo 350M, Nano 110M, Multilingual V3 500M | MIT (code + weights per resemble-ai) | **MIT** ✅ commercial | 110 M – 500 M | PyTorch; docs show `device="cuda" # or "cpu" / "mps"` — **MPS supported**. Nano: "3× realtime on 8 CPU cores" | Highest of the group — Resemble says it is "consistently preferred" vs ElevenLabs in side-by-sides; zero-shot clone from ~5–10 s of a reference | **Strongest**: CFG/exaggeration knob (500 M), native paralinguistic tags `[laugh] [chuckle] [cough]` on Turbo/Nano | `uv add chatterbox-tts` → `ChatterboxTurboTTS.from_pretrained(device="mps")` + `model.generate(text, audio_prompt_path="ref.wav")` |
| **Piper** | Original repo: MIT, **archived Oct 2025**; successor `OHF-Voice/piper1-gpl` is **GPL-3.0** ⚠️ (not permissive) | Voices are generally permissive (not re-verified this session) | ~20 MB per voice | CPU only (espeak-ng + fast RNN); no GPU/MLX path | Functional but clearly below Kokoro for "warm read-aloud"; many voices, many languages | None (fixed voice, no emotion/pace knobs beyond rate) | `uv add piper-tts` (note: pulls the GPL successor) |
| **Qwen3-TTS** (Alibaba) | Repo is 401-gated this session (login required); I could see from the HF org page that a **Qwen3-TTS collection exists** (models 0.9 B and 2 B, a voice-design/cloning/preset demo space), but I could **not verify the licence text, size, or Mac support** | **Unverified** — Qwen LLMs are usually permissive (Qwen licence, Apache-2.0 for some), but I won't state it for TTS without the page | 0.9 B / 2 B per HF collection card | Unverified (likely PyTorch MPS; no MLX build confirmed) | Unknown — no listen/sample read this session | Voice "design / cloning / presets" per the demo space name | Not provided (could not read the model card) |
| **Orpheus** (lucadiliello) | **Could not be located** (search + direct GitHub URL returned 404/no results in this environment) | Unknown | Unknown | Unknown | Unknown | Unknown | n/a — **treat as a non-candidate until you verify it exists** |
| **Dia** (nariel) | **Could not be located** (same as above) | Unknown | Unknown | Unknown | Unknown | Unknown | n/a |
| **F5-TTS** | **MIT** (code) | **CC-BY-NC** weights (repo README states this explicitly, because of the Emilia training set) ⚠️ **not commercial-safe** | ~335 M (base v1) | PyTorch MPS or CPU (Apple Silicon install documented in the README); an MLX port (`f5-tts-mlx`, by Lucas Newman) is mentioned in the README but I did not verify its licence | Good, but zero-shot clone — quality depends on the reference clip | Reference-audio driven style; no explicit emotion/pace API | `uv add f5-tts` → `f5-tts_infer-cli --model F5TTS_v1_Base --ref_audio ref.wav --ref_text "…" --gen_text "…"` |
| **Parler-TTS** (Parler Labs) | HF model pages returned 401 in this session; **licence of the weights not verified** (I found no open-source statement; treat as unverified until you open the card) | Unknown | ~1 B (large-v1) — unverified this session | CPU/MPS possible via PyTorch; no MLX build confirmed | Decent but below Kokoro/Chatterbox in blind comparisons I've seen elsewhere (not verified here) | Style/prompt control (text prompt describes the voice) | `uv add Parler` → `ParlerTTSWrapper.from_pretrained("parler-tts/parler-tts-large-v1")` — **unverified command** |
| **Sesame CSM** (Common Speech Model) | Not found in this session's searches (Sesame's CSM-1B is released, but I have no licence text to cite) | Unknown | Unknown | Unknown (HF card likely says PyTorch) | Unknown | Unknown | n/a |
| **Newer things I saw in 2026**: `kokoro-coreml` (M5-friendly, ANE-accelerated Kokoro port by mattmireles — 13–70× real-time on M1→M2 Ultra; **fastest local path on Apple Silicon**); Chatterbox family expansion (Turbo/Nano/Multilingual V3); F5-TTS v1 base with better inference. |

## RECOMMENDATION

**Top pick 1 — Chatterbox Turbo (or Nano) — MIT, 350 M (or 110 M)**
- MIT on code *and* weights → safe for commercial use, no CC-BY-NC landmines (F5-TTS) and no GPL-3.0 (piper1-gpl).
- **MPS explicitly supported** in the official example (`device="mps"`); Nano is documented to run 3× real-time on 8 CPU cores — your M5 Max will do far better.
- Zero-shot voice cloning: drop in a 5–10 s clip of a warm female reading a children's story and Chatterbox will match that timbre — no fixed voice names to audition.
- Native `[laugh] [chuckle] [cough]` paralinguistic tags (Turbo/Nano) + CFG/exaggeration knob (500 M) → best-in-class control for a narrator.
- Exact install & run:
  ```bash
  uv add chatterbox-tts
  uv run python -c "from chatterbox.tts_turbo import ChatterboxTurboTTS as M; import torchaudio as ta; m=M.from_pretrained(device='mps'); ta.save('out.wav', m.generate('Once upon a time, in a little blue house…', audio_prompt_path='warm_fEMALE_ref_clip.wav'), m.sr)"
  ```

**Top pick 2 — Kokoro-82M (apache-2.0) via kokoro-onnx or kokoro-coreml**
- Apache 2.0 weights → cleanest commercial posture on the list.
- On your Mac, **kokoro-coreml** is the fastest path (ANE, ~70× real-time on M2 Ultra; 422 ms for 30 s). Pure Python path: **kokoro-onnx** (near-real-time on M1; MIT code + Apache weights).
- 11 fixed US-female voices; for a warm/gentle storybook narrator try, in order:
  1. **`af_heart`** — the canonical Kokoro voice, only "A"-graded female, warm and soft (default on every demo).
  2. **`af_bella`** — A−, "HH hours" of training data, listed as the second-best US female; slightly more energy — good for chapter openers.
  3. **`af_nicole`** — B−, "HH hours", the 🎧 tag hints at a podcast/audiobook-style training set (often the most "read-aloud" of the set).
  4. **`af_sarah`** and **`af_kore`** — C+, more neutral, good A/B candidates.
- Exact install & run:
  ```bash
  # ONNX (Python, MPS/CPU)
  uv init -p 3.12 && uv add kokoro-onnx soundfile
  uv run python -c "import kokoro_onnx, soundfile as sf, numpy as np; m=kokoro_onnx.KPipeline(lang_code='a'); g=m('Once upon a time…', voice='af_heart', speed=0.95); [sf.write(f'p{i}.wav', a, 24000) for i,a in enumerate(g)]"
  ```

**What I would NOT pick for you**
- **Piper** — the active repo is now GPL-3.0 (the MIT `rhasspy/piper` is archived); plus it's the least natural here.
- **F5-TTS** — code is MIT but the weights are **CC-BY-NC**, so not commercial-safe.
- **Orpheus, Dia, Qwen3-TTS, Parler, Sesame CSM** — I could not verify licence/weights/Mac support for these in this session (404s, login-walled HF cards, or empty search results). If you want me to chase any of them, re-run with a logged-in HF session or a direct repo URL.

**Voice names to try, in priority order:** Chatterbox (clone from a 5–10 s warm female sample) → `af_heart` → `af_bella` → `af_nicole` → `af_sarah`.

### Key sources
- https://huggingface.co/hexgrad/Kokoro-82M (Apache 2.0 weights, VOICES.md with af_heart "A")
- https://huggingface.co/hexgrad/Kokoro-82M/raw/main/VOICES.md (voice grades)
- https://github.com/thewh1teagle/kokoro-onnx (MIT code, ~300 MB, M1 near-real-time)
- https://github.com/mattmireles/kokoro-coreml (ANE path, M2 Ultra 70× RT)
- https://github.com/resemble-ai/chatterbox (MIT, 110 M–500 M family, MPS supported, paralinguistic tags)
- https://github.com/rhasspy/piper (archived, MIT) → https://github.com/OHF-Voice/piper1-gpl (GPL-3.0)
- https://github.com/SWivid/F5-TTS (MIT code, **CC-BY-NC weights**, Apple Silicon install documented)
- https://huggingface.co/Qwen (Qwen3-TTS collection: 0.9 B & 2 B, demo space — licence page 401'd this session)
- Chatterbox model zoo: https://www.resemble.ai/learn/models/chatterbox
