I have enough verified detail. Here's the report.

# Local TTS for a warm, gentle English female children's-storybook narrator (M5 Max, 64 GB, Python via uv)

All candidates below run locally and free. I focus on ones with a first-party **MLX build for Apple Silicon** or clean MPS/CPU support, since that's your hardware.

## Per-model notes

**1. Kokoro-82M (hexgrad/Kokoro-82M) + mlx-audio (Blaizzy/mlx-audio)** — Best fit.
- Code: mlx-audio **MIT**; kokoro code Apache/MIT; **weights Apache-2.0** (explicitly "Apache-licensed," production/deployment welcome).
- Size: 82M params (~355 MB bf16 on HF).
- Mac: runs natively on Apple GPU via MLX (mlx-community/Kokoro-82M-bf16/8bit/6bit/4bit). No CUDA.
- Naturalness: high for the size; several fixed voices; `af_heart` is a warm American-English female.
- Pace: `speed=` param. No emotion control.
- Install: `uv tool install --force mlx-audio --prerelease=allow` (or `pip install mlx-audio`).
- Run: `mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 --text "..." --voice af_heart`

**2. Chatterbox (resemble-ai/chatterbox)** — Very strong expressive option.
- **Code and weights MIT** (README: "Licensed under MIT").
- Size: 0.5B (~2.57 GB fp16 on HF).
- Mac: MLX build via mlx-audio (mlx-community/chatterbox-fp16 / chatterbox-multilingual-v3).
- Naturalness: benchmarked vs ElevenLabs; expressive. Zero-shot voice cloning — you can clone a warm female reference clip.
- Pace/emotion: unique **exaggeration** + **cfg** control (README gives pacing/emotion tuning recipes).
- Install: `pip install mlx-audio` (for Mac) or `pip install chatterbox-tts` (CUDA path).
- Run: `python -m mlx_audio.tts.generate --model mlx-community/chatterbox-fp16 --text "..."` (add `ref_audio=` in the Python API to clone a voice).

**3. Qwen3-TTS (Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice / 0.6B)** — Strongest built-in female voices + emotion control.
- **Code and weights Apache-2.0** (verified LICENSE).
- Size: 0.6B (~0.9B params BF16) or 1.7B.
- Mac: MLX build via mlx-audio (mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit); also MPS via `qwen-tts`.
- Naturalness: strong; 9 premium timbres incl. **"Serena – warm, gentle young female"** and **"Vivian – bright young female."**
- Pace/emotion: full natural-language **instruct** control (tone, rate, emotion).
- Install: `pip install mlx-audio` (MLX) or `pip install -U qwen-tts`.
- Run: `mlx_audio.tts.generate --model mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit --text "..." --voice Serena --lang_code English`

**4. Piper (rhasspy/piper → now OHF-Voice/piper1-gpl)**
- License: **MIT** (original) / GPL (new piper1-gpl repo) — verify which you need for commercial use.
- Size: tiny per-voice (~60–100 MB); CPU-only, no GPU.
- Mac: CPU (no MLX/MPS; fine on Apple silicon).
- Naturalness: fast but noticeably less natural than the above — best for realtime/low-resource, not premium storytelling.
- Pace/emotion: no fine control.
- Install: `pip install piper-tts`.
- Run: `python -m piper --model en_US-lessac-medium --output_file out.wav -- "Once upon a time..."`

**5. Orpheus (canopyai/Orpheus-TTS)**
- **Apache-2.0** (GitHub API license field).
- Size: Llama-3B backbone (~3B).
- Mac: not MLX-native; PyTorch (MPS/CPU) or llama.cpp no-GPU path. vLLM path is CUDA.
- Naturalness: "SOTA… superior to SOTA closed-source" claim; fixed voices: **tara, leah, jess** (top-ranked, English).
- Pace/emotion: emotive tags; `repetition_penalty`/`temperature` shift pace.
- Install: `pip install orpheus-speech`.
- Run: `OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod").generate_speech(prompt, voice="tara")` (see README; ~Colab example).

**6. Dia (nari-labs/dia)**
- **Apache-2.0**.
- Size: 1.6B (~4–8 GB).
- Mac: PyTorch; README states "tested on GPUs (CUDA)," "Docker for ARM/MacOS" is TODO — so **no clean MPS/MLX path**.
- Naturalness: excellent, dialogue-focused, emotion + nonverbal tags, voice cloning.
- Pace/emotion: audio-prompt + emotion control.
- Install: `pip install git+https://github.com/nari-labs/dia.git` (or HF transformers main).
- Run: `uv run example/simple.py`.
- Caveat: not ideal for your Mac without the CUDA path.

**7. F5-TTS (SWivid/F5-TTS)**
- **Code MIT** (verified LICENSE).
- Size: ~0.3–0.5B (v1 Base).
- Mac: PyTorch on **Apple Silicon explicitly supported** (`pip install torch torchaudio`), MPS works.
- Naturalness: very good; voice cloning from a reference clip.
- Pace/emotion: via reference clip + flow steps; no direct emotion dial.
- Install: `pip install f5-tts` (or editable).
- Run: `f5-tts_infer-cli --model F5TTS_v1_Base --ref_audio ref.wav --ref_text "..." --gen_text "Once upon a time..."`

**8. Sesame CSM-1B (sesame/csm-1b)**
- License: **gated** on HF ("agree to share your contact information") — not freely open; also conversational, not storybook.
- Size: 1B (~6.2 GB F32 on HF).
- Mac: MLX build exists (mlx-community/csm-1b); transformers-native.
- Naturalness: conversational voice-agents, not narration.
- Pace/emotion: audio-context driven.
- Install: `pip install mlx-audio` (MLX) or transformers ≥4.52.1.
- Run: `python -m mlx_audio.tts.generate --model mlx-community/csm-1b --text "..."`.
- Verdict: gated + wrong use-case — skip for this task.

## RECOMMENDATION

**Top 1 — Qwen3-TTS 0.6B CustomVoice (MLX)** — purpose-built female voices with natural-language emotion/pace control; Apache-2.0; runs natively on your M5 via MLX. Voices to try: **Serena** ("warm, gentle young female" — ideal for kids' stories) and **Vivian** ("bright young female"). Add an instruct like *"Speak slowly, warmly and gently, like a bedtime story."*

**Top 2 — Chatterbox 0.5B (MLX)** — MIT, expressive, with exaggeration/cfg dials; best if you want to **clone a specific warm female reference clip** for a consistent narrator across a whole book. Try `exaggeration=0.5, cfg=0.5` (default) or lower cfg (~0.3) for slower, gentler pacing.

**Honorable mention — Kokoro-82M (MLX)**: fastest, lightest (355 MB), Apache-2.0, zero fuss — voice **`af_heart`** is a lovely warm female and it's the simplest "just works" pick if Qwen/Chatterbox feel heavy.

Quick start (uv):
```bash
uv tool install --force mlx-audio --prerelease=allow
mlx_audio.tts.generate --model mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit \
  --text "Once upon a time, in a land far away..." --voice Serena --lang_code English --play
```

Sources: huggingface.co/hexgrad/Kokoro-82M · github.com/hexgrad/kokoro · github.com/Blaizzy/mlx-audio (README) · huggingface.co/ResembleAI/chatterbox · huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice · github.com/canopyai/Orpheus-TTS (README + GitHub API) · github.com/nari-labs/dia (README) · github.com/SWivid/F5-TTS (README + LICENSE) · github.com/OHF-Voice/piper1-gpl (README) · huggingface.co/sesame/csm-1b.

Not found / not verified: Piper's exact new-repo license terms (MIT vs GPL split); Orpheus weight HF licence string (HF pages returned 401).
