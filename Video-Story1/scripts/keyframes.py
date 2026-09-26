#!/Users/justin/Code/Project-V/.venv/bin/python
"""Render keyframe candidates with Z Image Turbo from a shots json.
usage: scripts/keyframes.py jobs/shots_nonyun.json [seeds...]   -> work/kf/<id>_<seed>.png ; prompts recorded in jobs/kf_<jsonname>.log.json
Prompt = book style prefix (minus 'expressive kind faces', which produced tiny face blobs in T0.2) + scene + identity strings + suffix."""
import json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
ID = json.load(open(ROOT / "jobs/identity.json"))
book = json.load(open(ROOT / "input/refs/book_style.json"))["style"]
STYLE = book.replace("expressive kind faces, ", "")
SUFFIX = "Soft vignette edges, no captions, no readable text, no extra people."
shots = json.load(open(ROOT / sys.argv[1]))
seeds = [int(x) for x in sys.argv[2:]] or [9101, 9102, 9103, 9104]
out = ROOT / "work/kf"; out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Volumes/SSD-4T-LR/AI/Models")
rec = []
for sh in shots:
    idents = "; ".join(ID[c] if c in ID else c for c in sh["chars"])
    prompt = f"{STYLE}{sh['scene']}. {idents}. {sh.get('extra','')}{SUFFIX}"
    for seed in seeds:
        f = out / f"{sh['id']}_{seed}.png"
        rec.append({"file": f.name, "shot": sh["id"], "seed": seed, "model": "z_image_turbo_1.0_q8p.ckpt", "size": "1024x576", "prompt": prompt})
        if f.exists(): continue
        subprocess.run(["draw-things-cli", "generate", "--model", "z_image_turbo_1.0_q8p.ckpt", "--no-download-missing", "--disable-preview",
                        "--width", "1024", "--height", "576", "--seed", str(seed), "--prompt", prompt, "--output", str(f)], env=env, capture_output=True, text=True, timeout=600)
        print("ok" if f.exists() else "FAIL", f.name, flush=True)
(ROOT / f"jobs/kf_{pathlib.Path(sys.argv[1]).stem}.log.json").write_text(json.dumps(rec, indent=1))
print("ALLDONE", flush=True)
