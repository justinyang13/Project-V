# Music and ambience playbook (local, free, instrumental)

Used for job 001 (`output/001-snow-tea/001-snow-tea_1hr.mp4`). All local: no cloud, no third-party tracks, no licence questions beyond the model's (ACE-Step 1.5 is MIT-licensed).

## Stack
- **ACE-Step 1.5** (text-to-music) in `tools/ACE-Step-1.5`, API on `127.0.0.1:8001`. Start: `cd tools/ACE-Step-1.5 && ACESTEP_CHECKPOINTS_DIR=/Volumes/SSD-4T-LR/AI/Models/ACE-Step ./start_api_server_macos.sh`. Weights (9.6 GB) live on the SSD; `tools/ACE-Step-1.5/checkpoints` is a symlink to `/Volumes/SSD-4T-LR/AI/Models/ACE-Step` (the `.env` setting alone did NOT redirect downloads).
- `scripts/music_gen.py` — one piece via the API (`--dur`, `--bpm`, `--key`, `--prompt`, `--seed`).
- `scripts/ambience.py` — procedural fire hum + soft wind + gentle crackles (no samples).
- `scripts/music_build.py` — builds the long track: N pieces → per-piece filter + loudness match → equal-power crossfades → slow leveler → ambience mixed under → fades → AAC. Resumable; restarts the music server and retries if it crashes.

## Recipe (60 minutes)
```bash
# music server running, then:
.venv/bin/python scripts/music_build.py --minutes 60 --out output/<job>/music_60min       # ~15 min total
ffmpeg -stream_loop 359 -i output/<job>/<job>_loop10s_1080p24.mp4 -i output/<job>/music_60min.m4a \
  -map 0:v -map 1:a -c copy -t 3600 -movflags +faststart output/<job>/<job>_1hr.mp4        # seconds, no re-encode
```
Result: 1.1 GB, 3600.000 s, 86,400 video frames (exactly 24 × 3600), music ≈ −22.5 LUFS, ambience ≈ −36 LUFS (14 dB under the music).

## What we learned
- **Set tempo and key yourself** (`--bpm 44 --key "D minor"`). With the model's built-in planner on, it ignored "slow" in the prompt and picked 91–120 BPM.
- What the user chose (v3b): *"Very slow, soft, gentle ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, a faint distant low flute and a warm airy pad far in the background… 44 BPM"*. A solo shakuhachi flute at 70 BPM was "too harsh and fast".
- **Soften after generating:** low-pass 6.5 kHz + −3 dB high shelf above 3 kHz; match every piece to −22 LUFS with a fixed gain (not dynamic loudnorm).
- **Piece length: 150 s.** A 240 s request crashed the music server during the VAE decode (diffusion was fine). 150 s is stable (~30 s each). Pieces cross-fade 8 s.
- **A slow leveler is needed for long listening:** without it 10-s windows swung from −34.5 to −16.2 dBFS (std 3.8 dB); with it −32.6 to −18.7 (std 2.7 dB). The remaining dips are natural silences in the piano, filled by the ambience.
- Generating short clips is cheap (~10 s for 30 s of audio), so iterate on style with 30 s clips first and only then build the hour.
- Ambience is generated in 124 s chunks with different seeds and 4 s equal-power crossfades, so an hour never repeats.
- Not verified by ear by Claude (it can't listen): no voice-like artifacts, exact instrument realism. The user reviewed the 30 s clips; the full hour is spot-checked by excerpts.
- Two of three "free Japanese music" sites the user cited as a style reference did not load (cert error / suspended account); the third was a frame wrapper. They were used only as a style hint, nothing was downloaded.

## YouTube notes (from web search on 2026-09-23; verify current policy yourself)
- No YouTube feature loops a short video under a longer audio track: upload one file. 1 h ≈ 1.1 GB (~8 min at 20 Mbps up).
- YouTube's "inauthentic content" (repetitive / mass-produced) rules are enforced per channel and hit ambient/lo-fi channels often; disclose AI-generated content in Studio.
