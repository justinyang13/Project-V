The user refused the file write. I'll deliver the report inline instead.

---

# Keeping 4 Painterly Storybook Characters Consistent with Z-Image Turbo + draw-things-cli

## 0. What the CLI itself tells us (from `draw_things_cli_help.txt`)

- `train lora` trains a LoRA from a folder of images + matching `.txt` captions; flags: `--steps`, `--rank`, `--scale`, `--learning-rate`, `--caption-dropout`, `--resolution`, `--width`, `--height`, `--name`, `--output`, `--resume`, `--dry-run`.
- `generate` has `--image` + `--strength 0…1` (input is aspect-preserving, center-cropped to the output size) and `-s/--seed`.
- `--config-json` takes `JSGenerationConfiguration`. **Key note from the help text:** for a local LoRA not registered in `custom_lora.json`, you must include `loras[].version` (e.g. `"flux1"`) so the CLI can build per-invocation LoRA metadata. The `loras[]` array is how multiple LoRAs are declared.

## 1. Can a LoRA trained on Z-Image be applied via `generate --config-json loras`?

**Yes — with two caveats.**

**(a) It must be a Z-Image LoRA.** LoRA weights are tied to the base architecture; a Flux LoRA will not load into Z-Image. Train with a Z-Image base (`Tongyi-MAI/Z-Image-Turbo` or `-Z-Image`) and infer with a Z-Image checkpoint.

**(b) `loras[].version` must match the architecture.** The help text only shows `"flux1"` as an example; the supported value for a Z-Image (S3-DiT) LoRA is **not confirmed** in the help text. Action: check the app's `custom_lora.json` schema, or just **register the LoRA in `custom_lora.json`** (help text implies registered LoRAs don't need the version hint). If neither works, fall back to ai-toolkit inference or ComfyUI, both of which stack Z-Image LoRAs natively.

### Recommended single-character LoRA hyperparameters

From the verified production config in the Battlemage Z-Image port of ostris/ai-toolkit and the dataset guide:

| Param | Value | Note |
|---|---|---|
| Base | `Tongyi-MAI/Z-Image-Turbo` (or base) | Turbo training needs the `ostris/zimage_turbo_training_adapter` (de-distillation LoRA) merged during training so the 8-step speed is preserved |
| Network | `lora` | |
| Rank (`linear`) | **16** | rank 8 worked as smoke test; 16 is the production value |
| `linear_alpha` | 16 | match rank |
| `steps` | **1500–3000** | 3000 used with a 7-image set; with 15–20 images, 1500–2000 is enough. Judge by fixed-seed A/B, not loss |
| `learning_rate` | **1e-4** (adamw) | |
| `batch_size` | 1 | grad ckpt on, `cache_latents_to_disk`, `unload_text_encoder` |
| `resolution` | **512/768/1024 buckets** | min 768 short side |
| `trigger_word` | unique per character | |
| `save_every` | 250 | keep 4 checkpoints, pick best by A/B at a **fixed seed** |

### Dataset (per character, 15–30 images)

- **15–30 images**, optimum ~20. Below 15 → overfit; >50 → fine-tuning territory.
- **Required shot variety:** front portrait, 3/4 (both sides), profile, face close-up, waist-up, full body, different expressions / lighting / backgrounds.
- No duplicates or near-duplicates, no cropped/obscured face, no multiple subjects, no extreme angles.
- **1024×1024** native (or 1024 on the long side, aspect preserved).
- Z-Image Turbo is trained on **natural-language prompts**, so captions must be natural English sentences, **15–35 words**, same element order in every file: `[trigger], [media type], [shot type] of a [man/woman], [clothing], [pose/action], [expression], [background], [lighting]`.
- **Caption rule:** describe what you do **not** want baked in (clothing, pose, lighting, background, expression). Do **not** describe face/eyes/skin/hair if that is the identity — those get bound to the trigger.
- Keep the **painterly style in the inference prompt**, not the captions — that way the LoRA learns identity only and you can re-style freely.

### Trigger words

Pick unique, uncommon tokens, e.g. `merrygirl01`, `storyboy01`, `eldersister01`, `emberdragon01`. **Never reuse a word** between characters.

## 2. Consistency via img2img + fixed seeds

- **`--image` + `--strength` (0…1):** use a good hero image of that character as the seed.
  - `0.20–0.35` → strong composition + pose lock, character drifts toward the LoRA identity.
  - `0.45–0.65` → re-illuminate / recolor while keeping silhouette.
  - Start at **~0.30**; only go lower if the face is drifting.
- **`-s/--seed`:** pick one seed that gives you the face you like for that character and **reuse it** across the series; change only pose/scene and `--strength`.
- **`--width`/`--height`:** keep the **same aspect ratio** for all shots of the same character (the CLI center-crops to the requested size).
- **`--negative-prompt`:** add `different person, extra face, two people, realistic photo, 3d render` to stay painterly and single-subject. (Z-Image-Turbo runs at `guidance_scale=1` — no CFG — per the HF card.)
- **Inference prompt with LoRA active:** `merrygirl01, soft watercolor storybook illustration, [shot type] of a young girl, [outfit], [pose], [expression], [background], [lighting]`. Trigger word is mandatory; the style phrase keeps the painterly look consistent.
- **Fixed-seed A/B** when choosing a checkpoint: same prompt/seed/strength, different LoRA step → pick the one where the face is most recognizable (this is exactly the workflow the Battlemage repo uses).

## 3. Two character LoRAs in one picture

- **Declare both in `loras[]`** in `--config-json` (two entries, each with `path`, `scale` ≈ 0.8–1.0, and the correct `version`).
- **Name who is who in the prompt:**
  `merrygirl01 and storyboy01, soft watercolor storybook illustration, two children standing side by side in a sunlit garden, the girl on the left in a red dress, the boy on the right in a blue shirt, both smiling, warm afternoon light`
- **Scales:** start at **0.85 / 0.85**. If one character bleeds into the other, drop the dominant one to ~0.7 and raise the other to ~1.0.
- **Composition helps:** distinct side, distinct clothing, distinct pose per character — the model uses these cues to route features to the right trigger.
- **Fixed seed** matters even more here; small seed changes swap which face gets which trigger.
- **If the CLI's `loras[]` with two Z-Image LoRAs misbehaves**, ComfyUI's `LoraLoaderModel` nodes stack LoRAs natively and are the most reliable path.
- **No two-LoRA training is needed** — each character LoRA is trained independently on the same Z-Image base and composes at inference.

## RECOMMENDATION

1. **Base model:** **Z-Image-Turbo** (8 NFE, ~16 GB, `guidance_scale=1`) for the painterly storybook look — it's the model you're already planning to use and the community LoRA pipeline is built around it. Use **Z-Image** base (50-step) if you need negative prompts / more diversity.
2. **Train 4 LoRAs** (one per character) with ostris/ai-toolkit — or draw-things-cli if it exposes the same knobs — on **15–20 diverse 1024px images**, **rank 16**, **lr 1e-4 adamw**, **1500–2000 steps** (3000 if the set is <10 images), **512/768/1024 buckets**, **batch 1**, **save every 250**, judge by **fixed-seed A/B**. For Turbo, use the **`ostris/zimage_turbo_training_adapter`** de-distillation adapter.
3. **Dataset prep:** use `afloy011-spec/lora-dataset-prep` (`--type character --trigger <tok>`) — it dedupes, checks blur, enforces the 15–35-word natural-language caption formula, and flags attribute-sticking (the #1 cause of "character looks wrong").
4. **Single-character inference:**
   ```
   draw-things-cli generate \
     --model <z_image_turbo> \
     --image hero_<char>.png --strength 0.30 \
     --seed 42 --width 1024 --height 1024 \
     --prompt "<trigger>, soft watercolor storybook illustration, <shot> of <desc>, <pose>, <expression>, <background>, <lighting>" \
     --negative-prompt "different person, extra face, two people, realistic photo, 3d render" \
     --config-json '{"loras":[{"path":"<char>.safetensors","scale":0.9,"version":"<zimage-arch>"}]}'
   ```
   Confirm the exact `version` string for Z-Image in the app's `custom_lora.json` schema, or register the LoRA there and drop the version field.
5. **Two-character scene:** same command, two entries in `loras[]` at 0.85/0.85, name both characters with distinct sides/clothing, keep the validated seed.
6. **Fallback:** if `loras[].version` won't accept a Z-Image value, use **ComfyUI** (native Z-Image + multi-LoRA stacking) or **ai-toolkit inference** for multi-LoRA scenes; keep draw-things-cli for the clean single-character case.

### Key URLs
- CLI help: `/Users/justin/Code/Project-V/Video-Story1/research/draw_things_cli_help.txt`
- Z-Image-Turbo model card: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- Turbo training adapter: https://huggingface.co/ostris/zimage_turbo_training_adapter
- Verified production LoRA config (rank 16, 3000 steps, lr 1e-4): https://github.com/pcwynne/ai-toolkit-xpu-battlemage-zimage → `config/xpu_examples/zimage_turbo_lora_prod.yaml`
- Dataset + caption formula (15–30 imgs, 1024px, natural-language captions, 15–35 words): https://github.com/afloy011-spec/lora-dataset-prep → `reference.md`
- Base trainer: https://github.com/ostris/ai-toolkit
