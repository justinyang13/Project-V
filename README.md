# Video-Zen1 — scene idea → 1-hour ambient loop video

Give Claude a one-line scene idea; it makes the image (you pick from 4) and gives back a one-hour 1080p video with original music and ambience, plus the audio track and a silent 10-second loop.

- **The spec:** [SPEC.md](SPEC.md) · **commands:** [wiki/runbook.md](wiki/runbook.md) · **what failed and why:** [wiki/lessons.md](wiki/lessons.md)
- **Browser version:** open `docs/index.html` (regenerate with `python scripts/build_docs.py`).
- **First job:** `001-snow-tea` — snowy zen garden, steaming tea, brazier fire → [log](wiki/runs/001-snow-tea.md).

## Next time — paste this to Claude Code, in this project, with your scene idea
```
Run SPEC.md for this scene idea: <e.g. rainy temple at night>. I want the one-hour video as the output.
Follow the stages and gates in SPEC.md, use draw-things-cli for images and video (validate video first, stage 0),
stop for my four sign-offs (image, loop, music sample, final excerpts), then deliver only the three final files
and clean up.
```

## What's in the repo (and what isn't)
In git: `SPEC.md`, `wiki/`, `docs/`, `docs-src/`, `scripts/`, `jobs/`, `input/`.
**Not in git** (see `.gitignore`): `output/` (videos), `work/` (scratch), `tools/ACE-Step-1.5` (re-clone, see SPEC §3), `.venv/`, model files (on the SSD `/Volumes/SSD-4T-LR/AI/Models`).

## Final files for job 001 (local only): `output/001-snow-tea/`
`001-snow-tea_1hr_1080p24.mp4` (1.1 GB, exactly 1 hour) · `001-snow-tea_audio_60min.m4a` (110 MB) · `001-snow-tea_loop10s_1080p24_silent.mp4` (2.8 MB)
