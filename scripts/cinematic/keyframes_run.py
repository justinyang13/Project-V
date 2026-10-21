#!/usr/bin/env python3
"""Keyframe pipeline per shot (resumable): Qwen-Image 2.1 composes the frame -> auto-QA -> best Qwen seed ->
Flux Klein 9B edit (LoRA + refs: frame, canon face, sheet full body) swaps face/hair/suit -> auto-QA -> chosen.png.
noface shots: Qwen only. Writes keyframes/<id>/{q_s*.png, e_*.png, qa.json, chosen.png}. Visual review by Claude after.
Usage (family-lora-venv): keyframes_run.py --film <dir> [--only A03,B02] [--qseeds 1 2] [--eseeds 1 2]"""
import argparse, json, os, shutil, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__)); CVENV = "/Users/Maxi/Documents/Default Project/ComfyUI/.venv/bin/python"
a = argparse.ArgumentParser(); a.add_argument("--film", required=True); a.add_argument("--only", default="")
a.add_argument("--qseeds", nargs="+", type=int, default=[1, 2]); a.add_argument("--eseeds", nargs="+", type=int, default=[1, 2])
a.add_argument("--lora", default="astra3_klein9b_1200_lora_f32.ckpt"); a.add_argument("--lw", type=float, default=0.5); o = a.parse_args()
F = os.path.abspath(o.film); P = json.load(open(f"{F}/keyframes/prompts.json")); only = set(filter(None, o.only.split(",")))
REF = [f"{F}/bible/refs/face_ref_closeup.png", f"{F}/bible/refs/astra_canon_front.png"]
CANON, BODY = f"{F}/bible/refs/astra_canon_front.png", f"{F}/bible/refs/full_front_x4.png"
EDIT = ("Edit the first image. Replace the woman's face with the exact face of the woman in the second image (same East Asian young woman, soft oval face, "
        "eye shape, nose, lips, light grey eyes, {marks}, silver-white hair in a high ponytail with long side-swept bangs). Replace her armor with the exact armor "
        "design of the third image: glossy white ceramic plates over a charcoal-black bodysuit with {leds}, high black collar, black hexagonal knee rings, white boots{state}. "
        "Keep her pose, her tall slim body proportions, every prop, the lighting, the camera framing, the background and the colours exactly as in the first image.")
MARKS = {"on": "thin glowing light-blue streak marks below the outer corners of both eyes", "dim": "faint dim blue streak marks below the outer corners of both eyes", "off": "dark unlit streak marks below the outer corners of both eyes"}
LEDS = {"on": "thin glowing blue LED lines along the plate edges", "dim": "thin dim blue LED lines", "off": "dark unlit LED lines"}
STATE = {"S0": "", "S1": ", with light grey ash dust on it", "S2": ", with grey ash dust on it and a jagged crack across the right shoulder plate", "S3": ", with ash dust and a crack across the right shoulder plate", "S4": ", with ash dust and a crack across the right shoulder plate"}
def batch(jobs, out, model, cfg=None):
    J = dict(model=model, defaults=dict(steps=4, cfg=1.0) if "flux" in model else {}, jobs=jobs)
    if cfg: J["config"] = cfg
    p = f"{out}/_jobs.json"; json.dump(J, open(p, "w")); subprocess.run([sys.executable, f"{H}/dt_batch.py", p, out])
def qa(imgs, extra=()):
    if not imgs: return {}
    j = f"{os.path.dirname(imgs[0])}/_qa.json"
    subprocess.run([CVENV, f"{H}/identity_qa.py", "--ref", *REF, "--img", *imgs, "--no_face_ok", "--json", j, *extra], capture_output=True)
    return {r["file"]: r for r in json.load(open(j))} if os.path.exists(j) else {}
SH = {s["id"]: s for s in json.load(open(f"{F}/story/SHOTLIST.json"))["shots"]}
for k in P:
    i = k["id"]
    if only and i not in only: continue
    d = f"{F}/keyframes/{i}"; os.makedirs(d, exist_ok=True)
    if os.path.exists(f"{d}/chosen.png"): continue
    st = SH[i]["state"]; mk = "off" if st == "S4" else "dim" if st == "S3" else "on"
    if k.get("mode") == "flux_scene":  # environment-only inserts where Qwen keeps adding people: plain Flux Klein, no LoRA, no refs
        batch([dict(id="f", prompt=k["prompt"], seeds=[1, 2, 3], width=2176, height=896)], d, "flux_2_klein_9b_i8x.ckpt")
        fs = sorted(f"{d}/{f}" for f in os.listdir(d) if f.startswith("f_s") and f.endswith(".png"))
        shutil.copy(fs[0], f"{d}/chosen.png"); json.dump(dict(flux=fs, chosen=fs[0], note="scene: visual pick pending"), open(f"{d}/qa.json", "w"), indent=1)
        print(i, "flux scene done", flush=True); continue
    if k.get("mode") == "flux":  # extreme close-ups of her: Flux Klein + LoRA + her refs, short framing-first prompt
        batch([dict(id="f", prompt=k["flux_prompt"], refs=[CANON, REF[0]], seeds=[1, 2, 3], width=2176, height=896)], d,
              "flux_2_klein_9b_i8x.ckpt", {"loras": [{"file": o.lora, "weight": o.lw}]})
        fs = sorted(f"{d}/{f}" for f in os.listdir(d) if f.startswith("f_s") and f.endswith(".png"))
        shutil.copy(fs[0], f"{d}/chosen.png"); json.dump(dict(flux=fs, chosen=fs[0], note="ECU: visual pick pending"), open(f"{d}/qa.json", "w"), indent=1)
        print(i, "flux ECU done", flush=True); continue
    qp = k["prompt"].replace("astra, a young East Asian android woman", "A tall slim young East Asian android woman, 168 cm, realistic adult proportions about 8 heads tall, long slender legs,").replace("Astra", "the android woman")
    batch([dict(id="q", prompt=qp, seeds=o.qseeds, width=2176, height=896)], d, "qwen_image_2.1_q8p.ckpt")
    qs = sorted(f"{d}/{f}" for f in os.listdir(d) if f.startswith("q_s") and f.endswith(".png"))
    if k["kind"] in ("noface", "detail"):
        shutil.copy(qs[0], f"{d}/chosen.png"); json.dump(dict(qwen=qs, chosen=qs[0], note="noface: visual pick pending"), open(f"{d}/qa.json", "w"), indent=1)
        print(i, "noface done", flush=True); continue
    qq = qa(qs)
    def qscore(p):  # prefer frames whose body measures right; then a visible face
        r = qq.get(os.path.basename(p), {}); t = r.get("torso")
        return (0 if r.get("face_px", 0) == 0 else 1, 1 if (t is None or t >= 3.6) else 0, r.get("suit_white", 0) + r.get("suit_dark", 0))
    def body_ok(p):
        t = qq.get(os.path.basename(p), {}).get("torso"); return t is None or t >= 3.6
    if not any(body_ok(q) for q in qs):  # body gate on the composition: try more Qwen seeds before editing
        batch([dict(id="q", prompt=qp, seeds=[s + 10 for s in o.qseeds], width=2176, height=896)], d, "qwen_image_2.1_q8p.ckpt")
        qs = sorted(f"{d}/{f}" for f in os.listdir(d) if f.startswith("q_s") and f.endswith(".png")); qq = qa(qs)
        if not any(body_ok(q) for q in qs): print(i, "WARN no Qwen frame passes the torso gate", flush=True)
    best = max(qs, key=qscore)
    ep = EDIT.format(marks=MARKS[mk], leds=LEDS[mk], state=STATE[st])
    batch([dict(id=f"e_{os.path.basename(best)[:-4]}", prompt=ep, refs=[best, CANON, BODY], seeds=o.eseeds, width=2176, height=896)], d,
          "flux_2_klein_9b_i8x.ckpt", {"loras": [{"file": o.lora, "weight": o.lw}]})
    es = sorted(f"{d}/{f}" for f in os.listdir(d) if f.startswith("e_") and f.endswith(".png"))
    eq = qa(es, ("--leds_off",) if mk == "off" else ())
    def escore(p):
        r = eq.get(os.path.basename(p), {}); fails = set(r.get("auto_fail", [])) - {"suit_leds", "hair"}
        return (0 if fails else 1, r.get("face") or 0)
    ch = max(es, key=escore); shutil.copy(ch, f"{d}/chosen.png")
    json.dump(dict(qwen=qq, qwen_best=best, edits=eq, chosen=ch), open(f"{d}/qa.json", "w"), indent=1)
    r = eq.get(os.path.basename(ch), {}); print(i, "chosen", os.path.basename(ch), "face", r.get("face"), "torso", r.get("torso"), "fails", r.get("auto_fail"), flush=True)
