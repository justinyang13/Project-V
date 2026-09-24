# Project-V — repeatable "scene idea → 1-hour ambient loop video" pipeline

**Start here:** `wiki/SPEC.md` (spec), `wiki/runbook.md` (exact commands), `wiki/lessons.md` (what failed and why). Browsable version: `wiki/html/index.html`.

## The job in one paragraph
The user gives a one-line scene idea; Claude generates the image (Z Image Turbo via `draw-things-cli`), animates only what should move (LTX-2.3 image-to-video, masks over the locked original), builds a seamless 10-second loop, makes soft piano music + ambience locally (ACE-Step 1.5), and delivers a 1-hour 1080p video, the audio, and the silent loop. The user's channel is "Zen Hour Music"; see `wiki/posting-plan.md`.

## Standing rules (from the user)
- **Approve first, render later:** get the user's approval on the image, what animates (plain-words list + mask overlay), and the audio sample before any long video render. Then the final reviews: the loop, and the listening pack of the hour's audio.
- **One folder per video:** `Project-V/Video-<Shortname><n>/` (e.g. `Video-Zen3`). Run from inside it; shared scripts are `../scripts/…`, Python is `../.venv/bin/python`. The repeatable steps and HTML live only in `Project-V/wiki/`.
- **Use `draw-things-cli`, never the Draw Things app**, for images and video, so closing the app can't affect a render. (CLI video is still unverified: validate it at stage 0.) The CLI has no "projects"; the video folder is the project.
- **Audio must be soft:** check every music piece and the final hour with `scripts/audio_qc.py` (screech, harshness, scratch, crackle, clicks, clipping, dropouts); regenerate bad pieces; give the user the listening pack. Claude cannot hear: report measurements and let the user's ears decide.
- **Keep only three final files per video** in `output/`: `<id>_1hr_1080p24.mp4`, `<id>_audio_60min.m4a`, `<id>_loop10s_1080p24_silent.mp4`. Delete all other output and `work/` at the end.
- **Models:** one flat folder `/Volumes/SSD-4T-LR/AI/Models`; never download a model that already exists there; new downloads go there.
- **Camera drift is the main risk:** use the cinemagraph prompt (never mention the camera) and measure drift on 3 seeds before final clips.
- One heavy model at a time on the 64 GB Mac (video, music, LLMs never together).

## Layout
`wiki/` (SPEC, runbook, lessons, music, models, posting-plan, `html/`, `html-src/`, `archive/`) · `scripts/` (shared) · `tools/ACE-Step-1.5` (git-ignored) · `.venv/` (git-ignored) · `Video-*/` (one per video: `input/ jobs/ output/ work/ README.md RUNLOG.md qc-report.md`). `Video-Zen2` and `Video-BeachSunset1` predate this layout; leave them alone unless asked.

## Git
One private repo `justinyang13/Project-V` (small files only; videos, scratch, tools and venvs are git-ignored). Rebuild HTML with `.venv/bin/python scripts/build_docs.py` before committing doc changes.
