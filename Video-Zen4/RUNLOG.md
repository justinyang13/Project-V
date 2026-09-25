# RUNLOG — Video-Zen4 (Jiufen alley at night, rain) — STOPPED 2026-09-24 by the user

Not finished: no 1-hour video was made. Resume point: choose the quiet-dip fix for the piano (`scripts/upcomp.py` B or C, or a steadier piano prompt), rebuild the mix, get the mixed listening pack approved, then mux 360 loops (Runbook §9). `work/` (11 GB scratch) is kept; `output/` holds the approved silent loop.

## Decisions / approvals
- Scene 1 (mystical fungal forest) was dropped by the user after the first image round. Scene 2: the real Jiufen alley (user's photo + a style reference), in the style of a rainy night with lanterns, neon and a bay below. Final image from FLUX.2 klein 9B (seed 12, round 4 candidate 6).
- Background: the sea/waves could not be made to move (the video model boils the water in place). The user asked for a backdrop that needs no motion: cliff with terraces and a temple (candidate 7), stream removed.
- Text on signs was replaced with generic words (`jobs/Video-Zen4/text_fix.json`); replacing posters with new ones was rejected by the user and rolled back to the originals. Coffee table, cup and steam removed (option 5 of the table-removal edits, pasted into the approved picture only in the changed corner).
- Motion in the approved loop (v12): procedural rain and splashes, lantern and neon flicker. No video-model clips are used. Loop point 0.57 against 0.59 for a normal frame step.
- Audio: piano + pad approved (D minor, 44 BPM); rain from MOSS-SoundEffect (clip r1), level "subtle" (rain −36 LUFS under music −22 LUFS).

## What failed and why (see Lessons D9–D14, R1–R7, and SPEC §1.4b)
- Rain took eight rounds: white lines, too heavy, no depth, big drops distracting, too big and too white. Approved: `rain_overlay.py --strength 0.9 --splash 0.96 --size 0.5 --light 0.5`.
- Video model: all three drift probes zoomed 7.5 % (30–38 px) at 145 frames; the region-wise stabilizer (`scripts/stabilize.py`) brought this to about 1 px.
- Finished hour: the whole-hour `audio_qc` failed (901 events) because of the rain; the piano alone had 3 tiny events. The user then reported the music goes quiet every ~5 s (17 % of 1 s windows more than 6 dB under the median).

## Files
`jobs/Video-Zen4/` has the scene, prompts, job.json (regions, splash surfaces), text fixes, rain jobs and the composition script. Large images and all scratch are not in git.
