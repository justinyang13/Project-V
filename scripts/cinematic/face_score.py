#!/usr/bin/env python3
"""ArcFace (insightface buffalo_l) face similarity vs a reference set.
Usage: face_score.py --ref a.png [b.png ...] --img x.png [y.png ...] [--json out.json]
Prints per image: largest face width (px), cosine vs ref centroid, max vs any ref.
Run with /Users/Maxi/Code/Tools/family-lora-venv/bin/python."""
import argparse, json, os, sys, numpy as np, cv2
from insightface.app import FaceAnalysis
_app = None
def app():
    global _app
    if _app is None:
        _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=-1, det_size=(1024, 1024))
    return _app
def embed_img(im):
    h, w = im.shape[:2]; pad = int(0.25 * max(h, w))
    im = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(128, 128, 128))
    s = 1.0
    if max(im.shape[:2]) > 2600:
        s = 2600 / max(im.shape[:2]); im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    fs = app().get(im)
    if not fs: return None, 0
    f = max(fs, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    return f.normed_embedding, int((f.bbox[2]-f.bbox[0]) / s)
def embed(path):
    im = cv2.imread(path)
    if im is None: return None, 0
    return embed_img(im)
def ref_set(paths):
    E = [e for e in (embed(p)[0] for p in paths) if e is not None]
    if not E: sys.exit("no face in reference images")
    c = np.mean(E, axis=0); return np.array(E), c / np.linalg.norm(c)
if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("--ref", nargs="+", required=True)
    a.add_argument("--img", nargs="+", required=True); a.add_argument("--json")
    o = a.parse_args(); E, c = ref_set(o.ref); rows = []
    for p in o.img:
        e, w = embed(p)
        r = dict(file=p, face_px=w, vs_centroid=None if e is None else round(float(e @ c), 3),
                 vs_best=None if e is None else round(float(max(E @ e)), 3))
        rows.append(r); print(f"{os.path.basename(p):40} {w:5d}px  centroid {r['vs_centroid']}  best {r['vs_best']}")
    if o.json: json.dump(rows, open(o.json, "w"), indent=1)
