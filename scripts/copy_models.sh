#!/bin/bash
# Copy DT models that are not yet on the SSD into the SSD's category folders. Copy only, never deletes.
M=~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models
V=/Volumes/SSD-4T-LR/AI/Models/Video
for f in ltx_2.3_22b_distilled_1.1_q8p.ckpt ltx_2.3_audio_video_vae_f16.ckpt ltx_2.3_spatial_upscaler_x1.5_f16.ckpt ltx_2.3_spatial_upscaler_x2_1.1_f16.ckpt umt5_xxl_encoder_q8p.ckpt umt5_xxl_encoder_q8p.ckpt-tensordata wan_v2.1_video_vae_f16.ckpt wan_v2.2_a14b_hne_t2v_q8p.ckpt; do
  if [ -e "$V/$f" ]; then echo "SKIP exists: $f"; continue; fi
  echo "$(date +%T) copying $f"
  cp -X "$M/$f" "$V/$f.part" && mv "$V/$f.part" "$V/$f" && echo "$(date +%T) done $f"
done
echo ALLDONE
