# Video-Zen1 — snowy zen tea room, 1 hour

First video made with the pipeline in `../wiki/SPEC.md`. Snow falls outside the doorway, a small fire flickers in the garden, tea steams; soft piano with quiet fire and wind ambience.

- **Final files (local only, `output/`):** `001-snow-tea_1hr_1080p24.mp4` (1.1 GB, exactly 1 h) · `001-snow-tea_audio_60min.m4a` · `001-snow-tea_loop10s_1080p24_silent.mp4`
- **Log:** [RUNLOG.md](RUNLOG.md) · **QC:** [qc-report.md](qc-report.md)
- **Recipe:** image `input/001-snow-tea.webp` (made by the user in Draw Things, Z Image Turbo); masks/prompts in `jobs/001-snow-tea/`.
- **Known issue:** the audio has some screechy/scratchy moments (see `../wiki/lessons.md` D7). It predates the softness check. To fix: rebuild the hour with `music_build.py` (Runbook §8) and re-mux onto the silent loop (Runbook §Swap).
- Note: this video's file names use the old id `001-snow-tea`.
