# Models: where they live and the rule

**Rule:** all models live in one flat folder, `/Volumes/SSD-4T-LR/AI/Models` (exFAT SSD, no subfolders, no symlinks between models). Draw Things uses it as its External Model Folder. **Check that folder before any download; never download a file that exists.** New downloads go there.

| Files (in `/Volumes/SSD-4T-LR/AI/Models`) | Used for |
|---|---|
| `ltx_2.3_22b_distilled_1.1_q8p.ckpt`, `ltx_2.3_audio_video_vae_f16.ckpt`, `ltx_2.3_spatial_upscaler_x1.5_f16.ckpt`, `ltx_2.3_spatial_upscaler_x2_1.1_f16.ckpt`, `gemma_3_12b_it_qat_q8p.ckpt` (+`-tensordata`) | **Video (LTX-2.3 image-to-video)** — the model job 001 used |
| `ltx_2_19b_distilled_q6p.ckpt`, `ltx_2_audio_video_vae_f16.ckpt` | Older LTX-2 19B (not used) |
| `wan_v2.2_a14b_hne_t2v_q8p.ckpt`, `wan_v2.1_video_vae_f16.ckpt`, `umt5_xxl_encoder_q8p.ckpt` (+tensordata) | Wan 2.2 **text-to-video** high-noise expert (can't animate a still; unused) |
| `flux_2_klein_9b_i8x.ckpt`, `flux_1_vae_f16.ckpt`, `flux_2_vae_f16.ckpt`, `z_image_turbo_1.0_q8p.ckpt`, `qwen_3_8b_q8p.ckpt`, `qwen_3_vl_4b_instruct_q8p.ckpt` (+tensordata), `custom_prompt_style.json` | Image models (not used here) |
| `ACE-Step/` (9.6 GB) | Music model weights (ACE-Step 1.5, MIT). `tools/ACE-Step-1.5/checkpoints` is a symlink to this folder |

Other local software: Ollama models (`gpt-oss:120b` 65 GB — never load during renders, `qwen3.5:35B`, `qwen3-coder:30b`, `qwen3.8:27b`) exist but were **not used** for this pipeline.

If image-to-video with Wan is ever wanted, the **I2V** experts must be added (not installed). Consolidation history (2026-09-23): 15 files were copied from Draw Things' sandbox to the SSD, verified by exact byte size, then deleted from the sandbox.

**FLUX.2 klein 9B as an image editor (verified 2026-10-17):** `~/.claude/bin/dt-cli-26.0928.0/draw-things-cli generate --local --no-download-missing --model flux_2_klein_9b_i8x.ckpt --prompt-file p.txt --image crop.png --strength 1.0 --width 1280 --height 1280 --seed S` edits a crop in 4 steps (~13 s at 1280², ~6 s per step on a busy machine). Give it a **crop** (≤ 1280 px), say what to switch off and "keep everything else exactly the same"; always use `--local` (otherwise the CLI may use Draw Things cloud compute). Alignment with the original is good (median flow 0.2–1 px) and it can switch a lamp off convincingly, **but pasting its pixels back into a finished frame never looked right** (the edit repaints the surroundings, so a patch shows). Use it for stills or for ideas, not for patches inside an approved picture (Lessons S11–S13). Depth Anything V2 Small (`depth_map.py`, run with `Tools/moss-env`) gives the depth map the snow needs.

