# QC report — 001-snow-tea (final: r02)

Deliverables (this folder):
- `001-snow-tea_loop10s_1080p24.mp4` — H.264, 1920×1080, 24 fps, 240 frames = 10.000 s (verified with ffprobe)
- `001-snow-tea_loop10s_1080p24_prores422hq.mov` — ProRes 422 HQ master (221 MB)
- `001-snow-tea_preview60s.mp4` — 6 loops back to back (for checking the seam by eye)
- `r02/` — frames, mask, plate, seam sheet, raw `qc_final.json`

| Check | Result | Limit | |
|---|---|---|---|
| Duration / size / fps | 240 frames, 10.000 s, 1920×1080, 24 fps | exact | ✅ |
| Seam ratio (frame 239→0 vs typical step) | 0.97 | ≤ 1.3 | ✅ |
| Locked pixels identical to source (frames 0, 57, 130, 239) | true | true | ✅ |
| Largest frame-to-frame brightness jump | 0.48 | ≤ 1.5 | ✅ |
| Brightness steadiness (circular detrended std) | 0.16 | ≤ 1.0 | ✅ |
| Camera drift of the source clips | 0.1 px | ≤ 0.7 px | ✅ |
| Snow moving down / steam moving up | 97–98 % / 92–94 % | ≥ 65 % / ≥ 60 % | ✅ |
| Human review (you) | no visible loop point; fire, steam and snow all look right | — | ✅ |

Recipe: LTX-2.3 22B distilled via Draw Things API, prompt P5, 1024×576, 8 steps, two 145-frame clips (seeds 101, 202) → `scripts/loop_build.py`.
Known limits: AI region is generated at 1024×576 and upscaled to 1080p (the garden is out of focus so this isn't visible); snow crossing the mask edge at the door frames was not seen as a problem.
