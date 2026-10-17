# QC report — The First Tram and Corner Store (2026-10-17)

## Picture
- Loop: 60 s, 1440 frames, 24 fps, procedural (no AI video, so no camera drift). Raw frames loop exactly (frame 1439 → 0 differs like any normal frame step, ~0.15/255).
- Snow v5 approved (5 depth layers, ~2,330 flakes, random speed/size/drift, 22 % white, 30 % crisp). Flicker v9 approved (one failing bulb, relit in linear light from an AI "lamp off" picture; other lamps steady; an event at least every 4.2 s).
- 4K frame checked at 30 s. Both hours decode cleanly around a loop boundary (30:00) and in the last 10 s.

## Audio
- Music: style A (approval 3), 26 ACE-Step pieces, each passed audio_qc after retakes. Whole hour first FAILED (2 harsh, 143 loud-note warnings, 16.4 % quiet 1 s windows) → upcomp 8/0.75/1.8 + two local soft lowpass spots → **music alone: 0 harsh, 52 loud-note warnings, 7.3 % quiet windows**.
- Ambience alone (snow bed from 7 checked MOSS clips + hum −12.9 dB + 11 distant tram bells): 0 events.
- Final mix: −21.8 LUFS, true peak −4.5 dBFS, **0 harsh events, 41 loud-note warnings, pass**. Claude cannot hear: the listening pack (12 × 5 s: the 4 biggest note jumps, both fixed spots, 3 bells, 3 random) is for the user's ears.

## Deliverables (output/)
| File | Size |
|---|---|
| Video-The-First-Tram-and-Corner-Store_1hr_1080p24.mp4 | 979 MB, 3600.000 s, H.264 1920×1080 + AAC 256k |
| Video-The-First-Tram-and-Corner-Store_1hr_4k24.mp4 | 2.80 GB, 3600.000 s, H.264 3840×2160 + AAC 256k |
| Video-The-First-Tram-and-Corner-Store_audio_60min.m4a | 116 MB |
| Video-The-First-Tram-and-Corner-Store_loop60s_1080p24_silent.mp4 | 14.4 MB |
| Video-The-First-Tram-and-Corner-Store_loop60s_4k24_silent.mp4 | 44.7 MB |

**Final review approved (2026-10-17):** "Approve and save". `work/` deleted; only the five files in `output/` remain (git-ignored).
