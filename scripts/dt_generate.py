"""Generate one clip via the Draw Things API. Usage:
python scripts/dt_generate.py --job 001-snow-tea --round r01 --tag ltx_s1 --seed 101 --w 1024 --h 576 --frames 121
Writes work/<job>/<round>/<tag>/{frames/*.png, raw.mp4, meta.json}."""
import argparse, base64, io, json, os, re, subprocess, time
import requests
from PIL import Image

KEEP = ["model", "steps", "guidance_scale", "sampler", "shift", "strength", "seed_mode",
        "resolution_dependent_shift", "speed_up_with_guidance_embed", "guidance_embed",
        "start_frame_guidance", "guiding_frame_noise", "batch_count", "batch_size", "clip_skip",
        "sharpness", "loras", "controls", "tiled_decoding", "tiled_diffusion", "hires_fix",
        "upscaler", "refiner_model"]

def prompts(path, key):
    text = open(path).read()
    sec = re.split(r"^## ", text, flags=re.M)
    sec = next(s for s in sec if s.startswith(key))
    blocks = re.findall(r"```\n(.*?)\n```", sec, flags=re.S)
    return blocks[0].strip(), blocks[1].strip()

ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--round", required=True)
ap.add_argument("--tag", required=True); ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--w", type=int, default=1024); ap.add_argument("--h", type=int, default=576)
ap.add_argument("--frames", type=int, default=121); ap.add_argument("--pkey", default="P2")
ap.add_argument("--base", default="jobs/_dt_base/ltx2_i2v.json")
ap.add_argument("--set", nargs="*", default=[], help="overrides key=value (json values)")
a = ap.parse_args()
assert a.w % 64 == 0 and a.h % 64 == 0 and (a.frames - 1) % 8 == 0, "w,h multiples of 64; frames 8n+1"

job = json.load(open(f"jobs/{a.job}/job.json"))
pos, neg = prompts(f"jobs/{a.job}/prompts.md", a.pkey)
base = json.load(open(a.base))
img = Image.open(job["source"]).convert("RGB").crop(tuple(job["plate"]["crop"])).resize((a.w, a.h), Image.LANCZOS)
buf = io.BytesIO(); img.save(buf, "PNG")
cfg = {k: base[k] for k in KEEP if k in base}
cfg.update(width=a.w, height=a.h, num_frames=a.frames, seed=a.seed, prompt=pos, negative_prompt=neg,
           init_images=[base64.b64encode(buf.getvalue()).decode()])
for kv in a.set:
    k, v = kv.split("=", 1); cfg[k] = json.loads(v)

out = f"work/{a.job}/{a.round}/{a.tag}"; os.makedirs(f"{out}/frames", exist_ok=True)
img.save(f"{out}/input.png")
t = time.time()
r = requests.post("http://127.0.0.1:7860/sdapi/v1/img2img", json=cfg, timeout=6 * 3600)
secs = round(time.time() - t, 1)
r.raise_for_status()
frames = r.json()["images"]
for i, b in enumerate(frames):
    open(f"{out}/frames/f{i:04d}.png", "wb").write(base64.b64decode(b.split(",")[-1]))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", f"{out}/frames/f%04d.png",
                "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", f"{out}/raw.mp4"], check=True)
sz = Image.open(f"{out}/frames/f0000.png").size
meta = {"seconds": secs, "n_frames": len(frames), "frame_size": sz,
        "request": {k: v for k, v in cfg.items() if k != "init_images"}}
json.dump(meta, open(f"{out}/meta.json", "w"), indent=1)
print(f"done {a.tag}: {len(frames)} frames {sz} in {secs}s -> {out}")
