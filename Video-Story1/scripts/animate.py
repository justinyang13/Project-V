#!/Users/justin/Code/Project-V/.venv/bin/python
"""Animate keyframes with LTX-2.3 (Draw Things CLI). usage: animate.py S09:101 S09:202 S12:101 ...   (shot:seed). Skips clips that exist.
Output: work/clips/<shot>_<seed>/{input.png,prompt.txt,raw.mov,clip.mp4,frames/,meta.json}. 145 frames, 1024x576, 8 steps, cfg 1, prores -> also h264 mp4."""
import json, os, pathlib, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
M = json.load(open(ROOT / "jobs/motion.json"))
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Volumes/SSD-4T-LR/AI/Models")
for job in sys.argv[1:]:
    shot, seed = job.split(":"); out = ROOT / f"work/clips/{shot}_{seed}"; (out / "frames").mkdir(parents=True, exist_ok=True)
    if (out / "meta.json").exists(): continue
    (out / "prompt.txt").write_text(M[shot]); subprocess.run(["cp", str(ROOT / f"input/keyframes/{shot}.png"), str(out / "input.png")])
    cmd = ["draw-things-cli", "generate", "--model", "ltx_2.3_22b_distilled_1.1_q8p.ckpt", "--no-download-missing", "--disable-preview", "--image", str(out / "input.png"),
           "--prompt-file", str(out / "prompt.txt"), "--frames", "145", "--width", "1024", "--height", "576", "--seed", seed, "--steps", "8", "--cfg", "1.0",
           "--output", str(out / "raw.mov"), "--video-format", "prores422hq"]
    t = time.time(); r = subprocess.run(cmd, env=env, capture_output=True, text=True); secs = round(time.time() - t, 1)
    (out / "cli.log").write_text(r.stdout + "\n" + r.stderr)
    if not (out / "raw.mov").exists(): print("FAIL", job, r.returncode, flush=True); continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / "raw.mov"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out / "clip.mp4")])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out / "raw.mov"), "-vf", "select='not(mod(n,12))'", "-fps_mode", "passthrough", str(out / "frames/f%02d.png")])
    json.dump({"seconds": secs, "cmd": cmd}, open(out / "meta.json", "w"))
    print("done", job, secs, "s", flush=True)
print("QUEUE_DONE", flush=True)
