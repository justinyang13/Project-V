# Video-Story2 — sci-fi explorer + worn companion robot (learning test)

Goal: learn image-to-video with LTX-2.3 on a hyper-photoreal still; how long a single clip can be.
Started 2026-09-26. Status: length test done; nothing final yet.

## Files
- `input/explorer_robot.png` — approved still (1728x960; East Asian explorer in travel gear + small worn egg-shaped robot, night, ringed teal/magenta moon). Made from the prompts in this chat with Z Image Turbo.
- `jobs/motion_prompt.txt` — LTX motion prompt used (no camera words; gentle motion).
- `run.sh FRAMES W H SEED` — LTX-2.3 image-to-video via `draw-things-cli` (8 steps, cfg 1, ProRes -> h264). Output `work/runs/<f>f_<w>x<h>_s<seed>/clip.mp4`.
- `output/story2_test_*.mp4` — the three test clips (git-ignored, local only).

## Length test (768x448, seed 101, 25 fps output)
| Frames | Length | Render | Result |
|---|---|---|---|
| 241 | 9.6 s | 4 min | good; slow push-in, explorer turns away |
| 361 | 14.4 s | 5 min | good; faces/robot consistent; best trade-off |
| 481 | 19.2 s | 9 min | works, but last third drifts (camera pushes in, robot leaves frame) |

## Next
- Add "the framing does not change" and "the explorer stays in place" to curb the push-in; try seeds 202/303 at 361 frames (or 249 frames for exactly 10 s).
- Optional: upscale to 1080p (LTX x1.5 upscaler), add ambience/music (ACE-Step, MOSS), then final review.
