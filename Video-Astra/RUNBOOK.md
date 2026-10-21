# Video-Astra: RUNBOOK (settings that passed)

## 4K upscale (SeedVR2, benched 2026-10-20)
```
cd "/Users/Maxi/Documents/Default Project/ComfyUI/custom_nodes/ComfyUI-SeedVR2_VideoUpscaler"
../../.venv/bin/python inference_cli.py <scope_clip.mp4> --model_dir ../../models/SEEDVR2 \
  --dit_model seedvr2_ema_3b_fp16.safetensors --resolution 1608 --batch_size 9 --uniform_batch_size \
  --temporal_overlap 2 --vae_encode_tiled --vae_decode_tiled --color_correction lab --output <out.mp4>
```
~14 s/frame, fits in memory. Input must already be cropped to 2.39:1.
