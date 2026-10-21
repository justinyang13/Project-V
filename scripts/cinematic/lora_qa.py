#!/usr/bin/env python3
"""Render the fixed QA suite for LoRA checkpoints x weights (optionally with reference images).
Usage: lora_qa.py suite.json outdir --ckpts a.ckpt b.ckpt --weights 0.85 [--seeds 101] [--refs r1.png ...] [--tag name]
Writes outdir/<tag or ckpt-stem>_w<weight>/<id>_s<seed>.png via dt_batch.py."""
import argparse, json, os, subprocess, sys, tempfile
a = argparse.ArgumentParser(); a.add_argument("suite"); a.add_argument("out")
a.add_argument("--ckpts", nargs="+", required=True); a.add_argument("--weights", nargs="+", type=float, default=[0.85])
a.add_argument("--seeds", nargs="+", type=int); a.add_argument("--refs", nargs="*", default=[]); a.add_argument("--tag", default="")
a.add_argument("--only", default=""); o = a.parse_args()
S = json.load(open(o.suite)); here = os.path.dirname(os.path.abspath(__file__))
for ck in o.ckpts:
    for w in o.weights:
        J = dict(S); J["config"] = {"loras": [{"file": ck, "weight": w}]}
        jobs = []
        for j in S["jobs"]:
            j = dict(j)
            if o.seeds: j["seeds"] = o.seeds
            if o.refs: j["refs"] = [os.path.abspath(r) for r in o.refs]
            jobs.append(j)
        J["jobs"] = jobs
        d = os.path.join(o.out, f"{o.tag or ck.replace('.ckpt','')}_w{w}")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(J, f)
        cmd = [sys.executable, os.path.join(here, "dt_batch.py"), f.name, d] + (["--only", o.only] if o.only else [])
        print("==", d, flush=True); subprocess.run(cmd)
