# The First Tram and Corner Store

60-second seamless loop → 1-hour ambient video for Zen Hour Music: light snow over a dusk street with a tram and a corner store; the big front lamp is a failing bulb that flickers now and then. **Status (2026-10-17): approved and delivered; uploaded to YouTube as a private video for the user to publish.**

- **Source:** `input/Video-The-First-Tram-and-Corner-Store.png` = copy of `Project-I/images/AnimePaint/4K/4K_020.png` with the store stripes recoloured (`jobs/Video-The-First-Tram-and-Corner-Store/recolor_stripes.py`). The Project-I file is not touched.
- **Picture:** procedural, no AI video: `../scripts/still_loop.py` (snow v5, bad-bulb flicker v9 from `jobs/Video-The-First-Tram-and-Corner-Store/lamp_off_big_s101.png`, branch sway, window shimmer) from `jobs/Video-The-First-Tram-and-Corner-Store/job.json` and the depth map.
- **Audio:** piano style A + snowy-night ambience, see `jobs/Video-The-First-Tram-and-Corner-Store/music.md`.
- **Files:** brief `jobs/Video-The-First-Tram-and-Corner-Store/scene.md` · overlay `jobs/Video-The-First-Tram-and-Corner-Store/mask_overlay_v0.png` · log `RUNLOG.md` · checks `qc-report.md` · upload draft `jobs/Video-The-First-Tram-and-Corner-Store/youtube.md`.

## Commands (from this folder)
```bash
../.venv/bin/python jobs/Video-The-First-Tram-and-Corner-Store/recolor_stripes.py work/Video-The-First-Tram-and-Corner-Store/source_original_4K_020.png input/Video-The-First-Tram-and-Corner-Store.png
/Users/Maxi/Code/Tools/moss-env/bin/python ../scripts/depth_map.py --job Video-The-First-Tram-and-Corner-Store
../.venv/bin/python ../scripts/still_loop.py --job Video-The-First-Tram-and-Corner-Store --crf 18 --out output/Video-The-First-Tram-and-Corner-Store_loop60s_1080p24_silent.mp4
../.venv/bin/python ../scripts/still_loop.py --job Video-The-First-Tram-and-Corner-Store --size 3840 2160 --crf 16 --out output/Video-The-First-Tram-and-Corner-Store_loop60s_4k24_silent.mp4
ffmpeg -stream_loop 59 -i output/Video-The-First-Tram-and-Corner-Store_loop60s_1080p24_silent.mp4 -i output/Video-The-First-Tram-and-Corner-Store_audio_60min.m4a -map 0:v -map 1:a -c copy -t 3600 -movflags +faststart output/Video-The-First-Tram-and-Corner-Store_1hr_1080p24.mp4
```
## Output
`Video-The-First-Tram-and-Corner-Store_1hr_1080p24.mp4` (979 MB) · `Video-The-First-Tram-and-Corner-Store_1hr_4k24.mp4` (2.80 GB) · `Video-The-First-Tram-and-Corner-Store_audio_60min.m4a` · `Video-The-First-Tram-and-Corner-Store_loop60s_1080p24_silent.mp4` · `Video-The-First-Tram-and-Corner-Store_loop60s_4k24_silent.mp4`
