# LTX-2.3 — animating a painted / watercolor illustration (image-to-video)

## What's official (with sources)

**Model & distilled checkpoint** — https://huggingface.co/Lightricks/LTX-2.3
- `ltx-2.3-22b-distilled`: distilled version of the full model, **8 steps, CFG=1** (stated twice on the card, and confirmed on the FP8 card: https://huggingface.co/Lightricks/LTX-2.3-fp8). A "1.1" distilled revision exists with a different aesthetic.
- Hardware rule the card gives explicitly: **width/height must be divisible by 32; frame count must be 8·k + 1**. Otherwise pad with -1 and crop.
- Prompting is officially deferred to their "Prompting guide": https://docs.ltx.io/api-documentation/implementation-guides/prompting-guide.md

**Official prompting guide** (docs.ltx.io, retrieved)
- Single continuous take = **one flowing paragraph, present tense, ~4–8 sentences**, action with concrete verbs, one coherent lighting logic, camera language stated relative to the subject.
- I2V specific: "the prompt describes what should *happen*… focus on **motion and action, camera movement (incl. a static shot), and audio**" — the image already carries appearance.
- Keep the scene focused; keep lighting consistent; start simple and layer.
- Do **not** paste prompts written for other models (Kling/Seedance) unchanged.

**Official two-stage distilled I2V workflow** (ComfyUI-LTXVideo, `example_workflows/2.3/LTX-2.3_T2V_I2V_Two_Stage_Distilled.json`, https://github.com/Lightricks/ComfyUI-LTXVideo)
- Stage 1 at base resolution, then **spatial latent upscaler ×2**, Stage 2 at full resolution.
- Source image re-injection: **Stage 1 strength 0.7** (`LTXVImgToVideoConditionOnly` default 0.7 — leaves room for motion); **Stage 2 strength 1.0** (locks detail). This two-injection scheme is also documented in the beginner I2V tutorial: https://docs.ltx.io/open-source-model/usage-guides/image-to-video.md
- Sampler: `euler_cfg_pp` / dual-CFG guider with **CFG 1** (distilled schedule); a fixed distilled sigma schedule, not a user dial.
- Official LTX-2.5 template defaults (same family, useful as a baseline for 2.3): **768×512 base (→1536×1024 output), 97 frames at 24 fps ≈ 4 s**. The 2.3 two-stage example workflow uses **960×544 base, 121 frames** as its default.
- Recommended ComfyUI path per the model card: built-in **LTXVideo nodes** via ComfyUI Manager.
- For sharper detail at the cost of fidelity, Lightricks ships **IC-LoRA "Pixel Spatial Upscaler"** and **DFR** (detailing IC-LoRA) pipelines (https://github.com/Lightricks/LTX-2).

**Where I could NOT find official guidance (stated as such):** Lightricks does not publish LTX-2.3-specific tips for painterly/watercolor inputs, face/hand stability, or "subtle motion" presets beyond what's above. The face/hand and painterly tips below are best-practice extrapolations from the official prompting structure, not Lightricks-sourced.

## Tips for this specific use case (best-practice, not official)

**Keep faces & hands stable**
- Prompt the subjects as *still, posed, gazing* — e.g. "faces remain still, only hair and fabric move." LTX's guide says appearance alone gives the model little to animate; so *constrain* motion explicitly to avoid the model inventing motion.
- Prefer **medium/wide shots** over close-ups: the guide says close-ups need more detail and are where identity drift shows most.
- Raise the image-injection strength: the 0.7 default leaves "room for natural motion"; for a frozen figure with only background moving, **0.9–1.0 in Stage 1** keeps the face/hands locked at the cost of livelier motion. Stage 2 stays at 1.0.
- Keep the camera **static** (the guide explicitly lists "a static shot" as a valid camera description).

**Keep painterly texture**
- Name the medium and brushwork in the prompt: "hand-painted watercolor illustration, visible paper grain, soft washes, ink linework." The model follows the image's style but the prompt can reinforce it.
- The built-in negative prompt in the 2.5 template includes `cartoon, childish, ugly` — for a watercolor piece, keep the *cartoon* term out of the negative if it's fighting your style, and consider the **Detailer / Pixel Spatial Upscaler IC-LoRA** instead of raw upscaling, which is designed to preserve reference character while adding detail.
- Two-stage upsampling (base → ×2) is the official way to add texture without a heavy re-generate.

**Subtle motion (mist, leaves, cloth, hair)**
- The guide's core rule: *one verb-driven action per sentence, chronological.* Describe each moving element as its own small action and nothing else.
- Avoid compound actions; a crowded action list is exactly what makes the model animate faces.

## Recommended settings (distilled 2.3, two-stage I2V)

| Setting | Value | Source |
|---|---|---|
| Checkpoint | `ltx-2.3-22b-distilled` (or -fp8 / -1.1) | HF card |
| Steps | **8** (fixed distilled schedule) | HF card |
| CFG | **1.0** (guidance off) | HF card + workflow |
| Sampler | `euler_cfg_pp` / `euler_ancestral` | workflow / I2V guide |
| Base resolution | **768×512** (→ 1536×1024), or 960×544 as in the official example | I2V guide / workflow |
| Frames | **97** (≈4 s @24 fps) or **121** (official example default); must be 8k+1 | I2V guide / HF card |
| FPS | **24** | I2V guide |
| Image strength | Stage 1 **0.7 default → raise to 0.9–1.0** for rigid subjects; Stage 2 **1.0** | workflow / I2V guide |
| Camera | **Static** | prompting guide |
| Upscale | spatial latent ×2, optionally + Pixel Spatial Upscaler IC-LoRA | workflow / LTX-2 repo |

## Example prompt template (single flowing paragraph, per official structure)

> "A hand-painted watercolor illustration, soft paper grain and visible washes, with gentle ink linework. Two figures sit at a wooden table, their faces still and their hands resting calmly, gazing gently off-frame; only the light around them shifts. The camera remains completely static, a fixed medium shot with soft natural light from the left. Slowly, thin mist drifts across the background, a few loose leaves flutter down past the window, the woman's hair lifts in a faint breeze, and the hem of her linen dress ripples once and settles. The ink linework and watercolor texture stay consistent and unchanged throughout."

Negative (optional, tailor to your style): `photo, photorealistic, 3d render, plastic, motion blur, warping, deformed hands, flickering`

**Bottom line:** the only hard numbers Lightricks give you are *8 steps, CFG 1, 8k+1 frames, 32-divisible resolution, and image-injection at 0.7/1.0 across two stages*. Everything about faces, hands, and painterly motion is prompt- and strength-driven: lock the subjects in the prompt, make the camera static, name each subtle moving element as its own tiny action, and lean on the two-stage upscale for texture rather than a heavy single-stage re-generate.
