#!/usr/bin/env python3
"""Score candidates <id>_s<seed>.png vs a face reference set; pick the best seed per id.
Usage: pick_by_face.py cand_dir --ref r1.png [r2.png] --out picks.json [--min 0.5]
Images with no detectable face (e.g. back views) are kept with score null, flagged for a visual check."""
import argparse, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from face_score import embed, ref_set
a = argparse.ArgumentParser(); a.add_argument("dir"); a.add_argument("--ref", nargs="+", required=True)
a.add_argument("--out", required=True); a.add_argument("--min", type=float, default=0.5); o = a.parse_args()
E, c = ref_set(o.ref); by = {}
for p in sorted(glob.glob(os.path.join(o.dir, "*_s*.png"))):
    m = re.match(r"(.+)_s(\d+)\.png$", os.path.basename(p)); e, w = embed(p)
    s = None if e is None else round(float(e @ c), 3)
    by.setdefault(m.group(1), []).append(dict(file=p, seed=int(m.group(2)), face_px=w, score=s))
picks = {}
for k, L in by.items():
    L.sort(key=lambda r: -1 if r["score"] is None else r["score"], reverse=True); b = L[0]
    picks[k] = dict(best=b, all=L, passed=(b["score"] is not None and b["score"] >= o.min))
    print(f"{k:8} best s{b['seed']} score {b['score']} {b['face_px']}px {'PASS' if picks[k]['passed'] else 'CHECK'}  all={[r['score'] for r in L]}")
json.dump(picks, open(o.out, "w"), indent=1)
