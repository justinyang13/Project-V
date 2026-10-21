#!/usr/bin/env python3
"""4K (3840x1608 scope) AI upscale per shot with SeedVR2 3B fp16 (resumable). Input = clips/<id>/chosen.mp4 trimmed to what the cut uses
(edit/timeline), cropped to 2.388:1. Output = upscale/<id>_4k.mp4 (10-bit h265). Run with family-lora-venv python.
Usage: upscale_run.py --film <dir> [--only A01,A02]"""
import argparse, json, os, subprocess, time, cv2
a = argparse.ArgumentParser(); a.add_argument("--film", required=True); a.add_argument("--only", default=""); o = a.parse_args()
F = os.path.abspath(o.film); only = set(filter(None, o.only.split(",")))
T = json.load(open(f"{F}/edit/timeline_v1.json")); S = json.load(open(f"{F}/story/SHOTLIST.json"))["shots"]
NODE = "/Users/Maxi/Documents/Default Project/ComfyUI/custom_nodes/ComfyUI-SeedVR2_VideoUpscaler"; PY = "/Users/Maxi/Documents/Default Project/ComfyUI/.venv/bin/python"
os.makedirs(f"{F}/upscale/src", exist_ok=True)
for s in S:
    i = s["id"]
    if i == "T01" or (only and i not in only): continue
    out = f"{F}/upscale/{i}_4k.mp4"
    if os.path.exists(out): continue
    want = T[i][1] - T[i][0]; cap = cv2.VideoCapture(f"{F}/clips/{i}/chosen.mp4"); fps = cap.get(cv2.CAP_PROP_FPS) or 25
    n = int(round(want * fps)); w, h = int(cap.get(3)), int(cap.get(4)); cw = int(round(h * 3840 / 1608 / 2) * 2); x0 = max(0, (w - cw) // 2)
    src = f"{F}/upscale/src/{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{F}/clips/{i}/chosen.mp4", "-frames:v", str(n), "-vf", f"crop={min(cw, w)}:{h}:{x0}:0", "-c:v", "libx264", "-crf", "6", "-pix_fmt", "yuv420p", "-an", src], check=True)
    t0 = time.time()
    r = subprocess.run([PY, "inference_cli.py", src, "--model_dir", "../../models/SEEDVR2", "--dit_model", "seedvr2_ema_3b_fp16.safetensors", "--resolution", "1608",
                        "--batch_size", "9", "--uniform_batch_size", "--temporal_overlap", "2", "--vae_encode_tiled", "--vae_decode_tiled", "--color_correction", "lab",
                        "--video_backend", "ffmpeg", "--10bit", "--output", out], cwd=NODE, capture_output=True, text=True)
    ok = os.path.exists(out); print(i, "ok" if ok else "FAIL", f"{n} frames {time.time()-t0:.0f}s ({(time.time()-t0)/n:.1f} s/frame)", "" if ok else (r.stdout + r.stderr)[-300:], flush=True)
