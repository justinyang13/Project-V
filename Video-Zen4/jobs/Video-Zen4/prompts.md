# Prompts — Video-Zen4

Source: `input/Video-Zen4.png` (FLUX.2 klein 9B, seed 12). A rainy night in a Jiufen-style hillside alley: wet stone stairs down to a rocky bay with breaking waves, fishing boats and a lighthouse; a teal wooden restaurant with a wooden bar, stools and glowing lanterns; neon signs on both sides; a coffee cup with a short steam wisp on the foreground table.

**What moves (video model):** ocean waves and foam, boat rocking and lamp shimmer, coffee steam, lantern glow flicker, neon flicker. **Added later by a rain layer:** rain and wet-stone splashes over the whole frame. **Frozen:** sky and clouds (user), buildings, stairs, railings, table, cup, rocks, lighthouse, wires and bulbs.

Wording rules (Lessons A2, A13): never name the camera, "tripod", "framing", "locked" or "steady". Rain is not in the prompt (the rain layer adds it).

## P5 — strict cinemagraph (video)

**Positive**
```
Cinemagraph loop. One single photograph: the buildings, walls, stone stairs, railings, wet paving, wooden table, coffee cup and saucer, rocks, lighthouse, sky, clouds, mountains, wires and string bulbs stay pixel-still. The only motion in the entire image is ocean waves rolling gently toward the rocks with white foam washing over them, the small fishing boats rocking softly with their lamps shimmering on the water, thin short steam curling up from the coffee cup, the paper lanterns glowing with a soft warm flicker, and the neon signs flickering softly. Photorealistic, calm, moody seaside night.
```

**Negative** (ignored at CFG 1, kept for the record)
```
camera movement, zoom, pan, scene change, morphing, warping, brightness pulsing, people, animals, text, watermark, blurry, low quality
```

## P6 — short "still photograph" (round 2 after all 3 P5 seeds zoomed in 7.5 % / 30-38 px, Lessons A12)

**Positive**
```
A still photograph of a rainy seaside alley at night. Nothing in the scene changes or moves except the ocean waves breaking on the rocks, the small boats rocking gently on the water, thin steam rising from the coffee cup, and the lanterns and neon signs flickering softly.
```

## P7 — describe the frozen things by name, motion last

**Positive**
```
Photograph of a seaside alley: the stone stairs, railings, buildings, wooden table, coffee cup, rocks, lighthouse, sky and mountains are exactly as in the photograph and stay in place. Only the following move: waves breaking and foaming on the rocks, boats rocking gently, a thin wisp of steam rising from the coffee cup, warm lantern flicker, soft neon flicker.
```
