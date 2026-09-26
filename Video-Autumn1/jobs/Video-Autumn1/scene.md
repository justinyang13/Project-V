# Scene brief — Video-Autumn1 (approved 2026-09-24)

**User words:** "yes" to the Claude-proposed scene below (the user let Claude pick all four answers).

## Scene
A quiet stone courtyard of a wooden Japanese tea house at dusk, autumn.
Red and amber maple branches overhang the top-left and top-right of the frame.
Two glowing stone lanterns (tōrō) along a curving stone path.
Foreground: a low wooden bench with a small steaming bowl of tea, and a low iron brazier with glowing embers beside it.
Soft mist skims the ground at the right of the frame.
Warm lantern amber vs cool blue dusk; no people, no animals, no text, no clutter.

## Light & colour
Dusk / blue hour. Warm amber lantern glow in two pools, ember red in the brazier, cool blue-grey stone and shadow everywhere else.

## User changes (round 1, 2026-09-24)
- Keep candidate 1 as the base, but **make the whole place wet, like the rain just stopped** (glossy wet stone, puddles reflecting lantern light, damp wood, droplets on leaves).
- **No falling maple leaves animation** (too hard) — leaves stay in the branches. **Rain effect added later** as a procedural overlay (Video-Zen4 rain pipeline, runbook §R).

## Moving elements (by zone)
- **Mid (two lanterns):** faint lantern light flicker
- **Foreground (bowl):** thin steam curling up
- **Mid (brazier):** ember glow, faint flicker
- **Bottom / right:** slow mist drifting right
- **Top:** maple foliage swaying very gently (wet leaves, no falling)
- **Later, stage 7.5:** procedural rain overlay (straight down, subtle, splashes on stone/roof/bench — approved settings `--strength 0.9 --splash 0.96 --size 0.5 --light 0.5`, SPEC §1.4b)
Frozen: tea house, walls, windows, bench, tea bowl, stone path, stone lanterns, branches.

## Sound
- Music: soft piano with a faint koto, ~44 BPM, D minor / G minor (validated at stage 3 sample)
- Ambience: light wind + leaf rustle, possibly light rain tail (wet scene) — validate at stage 3 before relying on it
- Levels: music −22 LUFS, ambience −36 LUFS (14 dB under)

## Folder
`Video-Autumn1` — series: Autumn Temple (posting-plan week 2).
