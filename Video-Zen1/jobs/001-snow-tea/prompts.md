# Prompts — 001-snow-tea

Source: `input/001-snow-tea.webp`. A Japanese tatami room at night. Open shoji doors look onto a snowy zen garden with stone lanterns and a fire in an iron brazier. A cup of tea steams on a low table, beside a knit blanket and a paper floor lamp.

**What should move:** snow falling (outside only), the brazier fire flickering, and steam rising from the cup.
**What must stay still:** everything else. The compositing step locks the room to the source pixels anyway, but a prompt that asks for stillness also keeps the camera and the garden from drifting.

Prompt rules that apply to both models:
- Describe **motion**, not the picture. The image already supplies the picture.
- Name the camera as locked **once, at the start**, and back it up in the negative prompt.
- Give each moving element its own direction and speed: snow falls *down, slowly*; steam rises *up, thin*; fire *flickers in place*.
- No events and no story. Nothing appears, nothing enters, the light doesn't change.

---

## P1 — Wan 2.2 A14B I2V (hero candidate A)

Wan responds best to a medium-length, concrete description. Keep it under about 120 words.

**Positive**
```
Static locked-off shot on a tripod, the camera does not move. A quiet traditional Japanese room at night looking out through open shoji doors onto a snowy zen garden. Soft snowflakes fall slowly and steadily straight down across the garden, in many sizes, some large and out of focus near the doorway, drifting gently in still air. In the background on the right, a small fire burns in a dark iron brazier, its flames flickering and licking upward naturally, casting a softly pulsing warm glow. On the low wooden table, a thin, translucent wisp of white steam rises continuously from the hot cup of tea, curling and swirling slowly upward and fading into the air. The room, shoji screens, table, blanket and lamp stay perfectly still. Photorealistic, calm, cozy, cinematic, shallow depth of field.
```

**Negative**
```
camera movement, camera shake, zoom, pan, tilt, dolly, parallax, handheld, scene change, cut, morphing, warping, melting, flickering exposure, brightness pulsing, color shift, snow falling upward, snow blowing sideways, blizzard, snow indoors, thick smoke, steam from the table, steam detached from the cup, fire spreading, explosion, sparks shower, people, hands, animals, birds, text, watermark, subtitles, low quality, blurry, jpeg artifacts, distorted, deformed, static frame, frozen, slow motion stutter
```

## P2 — LTX-2 I2V (hero candidate B)

LTX works best with one flowing paragraph in present tense that starts with the main action and then covers camera, details, and light. Keep it under about 200 words. If Draw Things generates LTX-2 audio, turn it off (audio is out of scope).

**Positive**
```
Snow falls gently and steadily over a quiet Japanese zen garden at night, seen from inside a dim tatami room through wide-open shoji doors. The camera is completely static on a tripod, framing the doorway, a low dark wooden table in the foreground and a glowing paper floor lamp on the right. Snowflakes of many sizes drift slowly straight down in calm air, the nearest ones large, soft and out of focus, the distant ones tiny specks against the dark trees and snow-covered stone lanterns. At the far right of the garden a small fire burns in a black iron brazier, its orange flames flickering and dancing in place and softly pulsing light onto the snow. On the table, a delicate, thin ribbon of white steam rises continuously from a hot cup of amber tea, curling, twisting and slowly dissolving as it climbs. Nothing else moves; the room is perfectly still and the light is constant. Photorealistic, cinematic, warm lamplight against cool blue snow, shallow depth of field, calm and cozy winter night.
```

**Negative**
```
camera motion, zoom, pan, shake, cut, transition, morphing, warping, flicker, exposure change, color shift, snow falling upward, sideways blizzard, snow inside the room, thick smoke, fire spreading, sparks, people, hands, animals, text, watermark, low quality, distortion, frozen frame
```

---

## P3 — LTX-2.3, static-first (round 1b: fixes camera push-in seen with P2)

Cause found in R1: with P2 the LTX-2.3 draft zoomed in ~15 % and shifted ~124 px in 5 s. The model is distilled (CFG 1), so the negative prompt does nothing; the fix has to be in the positive prompt.

**Positive**
```
A completely still photograph of a quiet Japanese room at night, locked on a tripod: the camera never moves, never zooms, never pushes in, the framing stays exactly the same in every frame. Only three things move: fine snowflakes drift slowly straight down outside the open doorway; a small fire flickers in the black iron brazier at the back of the garden; and a thin wisp of white steam rises from the cup of hot tea on the low wooden table. The room, shoji screens, table, blanket, lamp, stone lanterns and trees are perfectly frozen and do not shift at all. Photorealistic, cinematic, warm lamplight against cool blue snow, shallow depth of field.
```

**Negative** (ignored at CFG 1; kept for when CFG > 1)
```
camera movement, zoom, push in, dolly, pan, tilt, parallax, shake, morphing, warping, exposure change, color shift, people, text, watermark
```

## P4 — LTX-2.3, cinemagraph wording

**Positive**
```
Cinemagraph: a perfectly static, locked-off photograph with only tiny looping motion. Fixed camera, fixed framing, no zoom, no movement of the viewpoint. Only the falling snow outside the doorway, the flickering flame of the brazier in the garden and the thin rising steam from the tea cup are alive. Everything else is frozen still. Photorealistic, calm, cozy winter night.
```

**Negative**
```
camera movement, zoom, push in, dolly, pan, tilt, shake, morphing, people, text
```

## P5 — LTX-2.3, strict cinemagraph (round 1c)

Result of round 1b: words like "never zooms / never pushes in" (P3) made drift *worse* (20-25 % zoom); the plain cinemagraph wording (P4) cut drift ~10x (2 % zoom, 11 px in 3 s). P5 pushes P4 further and never mentions camera moves.

**Positive**
```
Cinemagraph loop. One single locked photograph on a tripod: the framing is identical in every frame, the doorway, table, cup, blanket, lamp, lanterns and trees stay pixel-still. The only motion in the entire image is tiny snowflakes falling gently downward outside, the small brazier flame flickering in the garden, and thin steam curling up from the tea cup. Photorealistic, calm, cozy winter night.
```

**Negative**
```
camera movement, zoom, dolly, pan, tilt, shake, morphing, people, text
```

---

## Iteration knobs (change one or two per round and log it in the wiki)

| Symptom seen in QC | Prompt change | Setting change |
|---|---|---|
| Camera or garden drifts, zooms, or parallaxes | Start with "Completely static camera, locked-off tripod shot." and add "no camera movement" at the end | Lower CFG a little; try another seed; Wan: lower `shift` by 1 |
| Snow too sparse or too faint | "dense, steady snowfall, many visible flakes" | — |
| Snow too fast or blizzard-like | "very slowly, lazily drifting down, peaceful light snowfall" | — |
| Snow moves sideways or upward | "falling straight down in windless air" + negative "wind, gusts" | Try another seed |
| Fire frozen or barely moving | "lively flames constantly flickering and dancing" | If still weak, use R-FIRE below |
| Fire too big or spreading | "small contained fire in the brazier" + negative "large fire, bonfire" | — |
| Steam looks like smoke or is too thick | "thin, delicate, barely visible translucent steam" | — |
| Steam detaches or jumps | "a continuous unbroken wisp rising directly from the tea surface" | Use R-STEAM below |
| Steam missing | "steam clearly rising from the cup" at the start of the prompt | CFG +0.5 |
| Global light pulsing | Negative: "light flicker, exposure pulsing, lamp flicker" | Different seed |

## Region passes (fallback only, used when the hero clip gets one region wrong)

Crop the region with 2–3× its size as context, upscale the crop to model resolution, animate it, scale it back down, and composite it through that region's mask. This gives the model far more pixels for the small fire and steam.

**R-FIRE**, crop ≈ source `[1040, 250, 1240, 450]`
```
Static close shot. A small fire burns in a black iron brazier in a snowy garden at night, orange flames flickering, licking and dancing naturally in place, soft glow pulsing gently on the surrounding snow, a few snowflakes falling slowly. Camera does not move. Photorealistic, out of focus, soft bokeh.
```

**R-STEAM**, crop ≈ source `[900, 340, 1190, 720]`
```
Static close shot. A thin, translucent wisp of white steam rises continuously from a hot cup of tea on a dark wooden table, curling and swirling slowly upward and dissolving into the air, snowy garden softly blurred in the background with gentle snowfall. Camera does not move. Photorealistic, calm.
```
Note: with R-STEAM, the snow inside the steam box comes from a different clip than the hero clip. Only use it if the steam box's feathered edge doesn't show flakes popping (check the seam and edge crops).
