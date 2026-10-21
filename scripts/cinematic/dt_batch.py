#!/usr/bin/env python3
"""Run a batch of Draw Things CLI image jobs from a JSON file; skips outputs that exist.
jobs.json: {"model": "...", "defaults": {"width":..,"height":..,"steps":..,"cfg":..}, "config": {...optional --config-json...},
            "jobs": [{"id": "d01", "prompt": "...", "refs": ["a.png"], "seeds": [1,2], "width":..., "height":...}]}
Usage: dt_batch.py jobs.json outdir [--only id1,id2] [--timeout 600]"""
import json, os, subprocess, sys, time, argparse
CLI = os.path.expanduser("~/.claude/bin/dt-cli-26.0928.0/draw-things-cli")
a = argparse.ArgumentParser(); a.add_argument("jobs"); a.add_argument("out")
a.add_argument("--only", default=""); a.add_argument("--timeout", type=int, default=900); o = a.parse_args()
J = json.load(open(o.jobs)); os.makedirs(o.out, exist_ok=True); base = os.path.dirname(os.path.abspath(o.jobs))
only = set(filter(None, o.only.split(",")))
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Users/Maxi/Code/Models")
for j in J["jobs"]:
    if only and j["id"] not in only: continue
    d = {**J.get("defaults", {}), **{k: v for k, v in j.items() if k in ("width", "height", "steps", "cfg", "strength")}}
    for seed in j.get("seeds", [1]):
        out = os.path.join(o.out, f"{j['id']}_s{seed}.png")
        if os.path.exists(out): continue
        cmd = [CLI, "generate", "--model", j.get("model", J["model"]), "--no-download-missing", "--disable-preview",
               "--prompt", j["prompt"], "--seed", str(seed), "--output", out]
        for k in ("width", "height", "steps", "cfg", "strength"):
            if k in d: cmd += [f"--{k}", str(d[k])]
        if j.get("negative") or J.get("negative"): cmd += ["--negative-prompt", j.get("negative") or J["negative"]]
        for r in j.get("refs", []): cmd += ["--image", r if os.path.isabs(r) else os.path.join(base, r)]
        cfg = j.get("config", J.get("config"))
        if cfg: cmd += ["--config-json", json.dumps(cfg)]
        t = time.time()
        try:
            p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=o.timeout)
            ok = p.returncode == 0 and os.path.exists(out)
            print(f"{j['id']} s{seed} {'ok' if ok else 'FAIL'} {time.time()-t:.0f}s" + ("" if ok else " " + (p.stderr or p.stdout)[-300:]), flush=True)
        except subprocess.TimeoutExpired:
            print(f"{j['id']} s{seed} TIMEOUT", flush=True)
