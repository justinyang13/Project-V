# RUNBOOK — Video-Story1 (repeatable steps that were verified on this Mac)

Run from `Project-V/Video-Story1/`. Python for scripts: `../.venv/bin/python` (scripts have the shebang). Models: `DRAWTHINGS_MODELS_DIR=/Volumes/SSD-4T-LR/AI/Models`. One heavy model at a time; `ollama stop qwen3.8:27b` before video.

1. **Book refs** → `input/refs/` (`book_style.json` from the book's factory folder; art-only cover `cover_front4.png` → `cover_front_art.png`). Check the cover reproduces: same model/prompt/seed 733 at 1024×1536 → 0.21/255 difference.
2. **Identity strings** → `jobs/identity.json` (from CANON.md). **Shots** → `jobs/shots_*.json` (id, chars, scene).
3. **Keyframes** (Z Image Turbo, 1024×576, ~10 s each): `scripts/keyframes.py jobs/shots_nonyun.json 9101 9102 9103 9104` → `work/kf/`. Contact sheet: `scripts/sheet.py out.jpg 4 500 work/kf/S01_*.png`. Pick → `jobs/selected.json`, copy to `input/keyframes/S##.png`.
4. **Yun shots**: render the scene without Yun (`shots_yunbg2.json`), then `YUN_CROP=… YUN_OCCLUDE=… scripts/yun_compose.py <bg.png> <out_prefix> <x> <y> <height> 0 <strengths> --prompt-file jobs/blend/S##.txt` (cover head pasted with feather, image-to-image blend at 0.4–0.55).
5. **Animate** (LTX-2.3, 145 frames, 1024×576, 8 steps, cfg 1, ~210–285 s per clip): `scripts/animate.py S09:101 S12:101 …` → `work/clips/<shot>_<seed>/clip.mp4`. Motion prompts in `jobs/motion.json` (frozen painting + a short list of gentle motions; no camera words, no objects you don't want).
6. **Narration**: `../tools/tts-venv` (`uv pip install mlx-audio --prerelease=allow`); `scripts/narrate.py Serena serena` (Qwen3-TTS 0.6B 8-bit, `HF_HOME=/Volumes/SSD-4T-LR/AI/hf-cache`, delete `._*` files in it).
7. **Music**: start `tools/ACE-Step-1.5/start_api_server_macos.sh` (`ACESTEP_CHECKPOINTS_DIR=…/ACE-Step`), `../scripts/music_gen.py --tag t --seed N --dur 90 --bpm 72 --key "D major" --prompt "…very soft, warm, mellow…"`; post: `ffmpeg -af "lowpass=f=9000,volume=-4dB,alimiter=limit=0.75:level=disabled"`, fade-in 1.5 s; check with `../scripts/audio_qc.py`. Stop the server after.
8. **Sound**: `../tools/moss-env/bin/python ../scripts/rain_gen.py --jobs jobs/sound_jobs.json --out work/audio/sfx_raw` (~10 s per clip); QC table; `scripts/sfx_build.py` → `work/audio/sfx.json`.
9. **Cards**: `scripts/cards.py` → `work/cards/*.png` (book words only).
10. **Assemble**: edit `jobs/timeline.json` (shot durations, narration starts, card times) and optional `jobs/clip_choice.json` ({"S03":"S03_303"}); `scripts/assemble.py --out output/Video-Story1_trailer_1080p24.mp4` (≈ 15–20 s). `--video-only` for a picture-only test.
11. **Deliver**: `scripts/make_srt.py`; extract audio `ffmpeg -i trailer.mp4 -vn -c:a copy output/…audio.m4a`; silent picture `-an -c:v copy`; `scripts/lang_check.py` (must PASS); loudness `ffmpeg -i … -af ebur128=peak=true -f null -` (target −14 LUFS, TP ≤ −1.5 dBTP).
