"""Generate one image-to-video clip with draw-things-cli (headless; the Draw Things app must be closed). Same interface as dt_generate.py (API path).
python ../scripts/dt_clip_cli.py --job Video-Zen3 --round r01 --tag t_s101 --seed 101 --w 1024 --h 576 --frames 121 --pkey P5
Writes work/<job>/<round>/<tag>/{input.png, prompt.txt, raw.mov, frames/f0000.png..., meta.json, cli.log}. Run from the video folder."""
import argparse, json, os, re, subprocess, time
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True); ap.add_argument("--round", required=True); ap.add_argument("--tag", required=True)
ap.add_argument("--seed", type=int, required=True); ap.add_argument("--w", type=int, default=1024); ap.add_argument("--h", type=int, default=576)
ap.add_argument("--frames", type=int, default=121); ap.add_argument("--pkey", default="P5")
ap.add_argument("--model", default="ltx_2.3_22b_distilled_1.1_q8p.ckpt"); ap.add_argument("--steps", type=int, default=8); ap.add_argument("--cfg", type=float, default=1.0)
a = ap.parse_args()
assert a.w % 64 == 0 and a.h % 64 == 0 and (a.frames - 1) % 8 == 0, "w,h multiples of 64; frames 8n+1"
job = json.load(open(f"jobs/{a.job}/job.json"))
text = open(f"jobs/{a.job}/prompts.md").read()
sec = next(s for s in re.split(r"^## ", text, flags=re.M) if s.startswith(a.pkey))
pos = re.findall(r"```\n(.*?)\n```", sec, flags=re.S)[0].strip()
out = f"work/{a.job}/{a.round}/{a.tag}"; os.makedirs(f"{out}/frames", exist_ok=True)
img = Image.open(job["source"]).convert("RGB").crop(tuple(job["plate"]["crop"])).resize((a.w, a.h), Image.LANCZOS); img.save(f"{out}/input.png")
open(f"{out}/prompt.txt", "w").write(pos)
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Volumes/SSD-4T-LR/AI/Models")
cmd = ["draw-things-cli", "generate", "--model", a.model, "--no-download-missing", "--disable-preview", "--image", f"{out}/input.png",
       "--prompt-file", f"{out}/prompt.txt", "--frames", str(a.frames), "--width", str(a.w), "--height", str(a.h), "--seed", str(a.seed),
       "--steps", str(a.steps), "--cfg", str(a.cfg), "--output", f"{out}/raw.mov", "--video-format", "prores422hq"]
t = time.time(); r = subprocess.run(cmd, env=env, capture_output=True, text=True); secs = round(time.time() - t, 1)
open(f"{out}/cli.log", "w").write(r.stdout + "\n" + r.stderr)
if r.returncode or not os.path.exists(f"{out}/raw.mov"): raise SystemExit(f"FAILED rc={r.returncode}; see {out}/cli.log\n" + (r.stdout + r.stderr)[-1500:])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/raw.mov", "-start_number", "0", f"{out}/frames/f%04d.png"], check=True)
n = len([f for f in os.listdir(f"{out}/frames") if f.endswith(".png")]); sz = Image.open(f"{out}/frames/f0000.png").size
json.dump({"seconds": secs, "n_frames": n, "frame_size": sz, "cmd": cmd}, open(f"{out}/meta.json", "w"), indent=1)
print(f"done {a.tag}: {n} frames {sz} in {secs}s -> {out}")
