#!/Users/justin/Code/Project-V/.venv/bin/python
"""T0.2 candidate batch: renders varied scenes of Mei and Yun with Z Image Turbo, the book style prefix and the CANON identity strings.
Usage (from Video-Story1/): scripts/t02_batch.py            (skips files that exist; logs every prompt+seed to jobs/t02/prompts.json)"""
import json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
ST = json.load(open(ROOT / "input/refs/book_style.json"))
STYLE = ST["style"]
MEI = "Mei is a small thin 11-year-old girl with warm light skin sunburnt across the nose, big dark eyes, two short black braids tied with red string, a faded blue padded jacket with cloth knot buttons and a patched elbow, dark brown trousers, brown cloth shoes, and a wide straw hat"
YUN = "Yun is a gentle serpentine sea-green teal dragon with rows of carp scales, pale gold-cream belly plates, soft brown branching stag antlers, a soft grey-white feathered mane and brows, pointed ears, wide worried amber eyes, a broad soft snout with a thin white whisker curling from the nose, no wings, mist curling round him like a scarf"
PEARL = ", and a round grey-white pearl under his chin"
SCENES = {
 "mei": [
  ("portrait_worried", "close portrait of Mei facing the viewer with a worried little frown, misty bamboo behind her"),
  ("walk_side", "Mei walks on a dirt path through a bamboo forest, seen from the side, carrying a small bamboo pole with two small buckets"),
  ("climb_back", "Mei seen from behind climbing worn stone steps up into thick white mist"),
  ("sit_glad", "Mei sits on a mossy rock looking up with a glad small smile, soft light through bamboo"),
  ("classroom", "Mei stands at a wooden bench in a dim schoolroom, one hand gripping the bench, chalkboard behind her"),
  ("tea_full", "full-length Mei stands holding a small red-paper bundle of tea in both hands, misty mountains and grey tile roofs behind her"),
 ],
 "yun": [
  ("head_front", "close-up of Yun's head and long neck facing the viewer, amber eyes wide, soft white mist around him"),
  ("behind_rock", "Yun's head and antlers peek over a grey boulder at the edge of a small dark almost-dry mountain lake with cracked mud and pine trees"),
  ("over_roofs", "Yun's long body coils in the air above grey tile roofs of a mountain village at dusk, lanterns glowing below"),
  ("low_angle", "low angle view of Yun looking down worriedly, mist drifting, green bamboo at the edge"),
  ("profile", "Yun in side profile, mouth closed, floating through a misty valley of green terraces"),
  ("into_cloud", "Yun rises into a dark gathering storm cloud, body trembling, his pearl glowing, mist around him"),
 ],
}
SEEDS = [7101, 7102, 7103, 7104]
out = ROOT / "work/t02"; out.mkdir(parents=True, exist_ok=True)
rec = ROOT / "jobs/t02"; rec.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Volumes/SSD-4T-LR/AI/Models")
log = []
for who, scenes in SCENES.items():
    for name, scene in scenes:
        for seed in SEEDS:
            ident = MEI if who == "mei" else YUN + (PEARL if name in ("into_cloud", "head_front") else "")
            prompt = f"{STYLE}{scene}. {ident}. Spot illustration with soft vignette edges, expressive faces, no captions, no readable text."
            f = out / f"{who}_{name}_{seed}.png"
            log.append({"file": f.name, "who": who, "scene": name, "seed": seed, "model": "z_image_turbo_1.0_q8p.ckpt", "size": "1024x576", "prompt": prompt})
            if f.exists(): continue
            subprocess.run(["draw-things-cli", "generate", "--model", "z_image_turbo_1.0_q8p.ckpt", "--no-download-missing", "--disable-preview",
                            "--width", "1024", "--height", "576", "--seed", str(seed), "--prompt", prompt, "--output", str(f)], env=env, capture_output=True, text=True, timeout=600)
            print("ok" if f.exists() else "FAIL", f.name, flush=True)
(rec / "prompts.json").write_text(json.dumps(log, indent=1))
(out / "done.flag").write_text("done")
