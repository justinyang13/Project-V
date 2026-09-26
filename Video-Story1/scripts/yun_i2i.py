#!/Users/justin/Code/Project-V/.venv/bin/python
"""Yun cover-exact test: image-to-image from the cover head crop with Z Image Turbo at several strengths.
Usage (from Video-Story1/): scripts/yun_i2i.py   -> work/yun_i2i/<strength>_<seed>.png, record in jobs/yun_i2i.json"""
import json, os, pathlib, subprocess
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "work/yun_i2i"; out.mkdir(parents=True, exist_ok=True)
src = out / "src_1024x896.png"
Image.open(ROOT / "input/canon_src/yun_head_cover_crop.png").convert("RGB").resize((1024, 896), Image.LANCZOS).save(src)
STYLE = "Warm glowing storybook illustration in gouache and colored pencil, soft blue-green mist, rich but gentle colors, no text, no writing, no letters: "
YUN = ("Yun, a gentle serpentine sea-green teal dragon with rows of carp scales, pale gold-cream belly plates on the neck, soft brown branching stag antlers, "
       "a fine grey-white feathery mane and brows, pointed ears, wide worried amber eyes, a long refined snout with a thin white whisker curling from the nose, no wings, "
       "mist curling round his neck like a scarf, seen among soft white clouds with misty green mountains behind")
env = dict(os.environ, DRAWTHINGS_MODELS_DIR="/Volumes/SSD-4T-LR/AI/Models")
rec = []
for st in (0.35, 0.5, 0.65):
    for seed in (8101, 8102, 8103, 8104):
        f = out / f"s{int(st*100)}_{seed}.png"
        rec.append({"file": f.name, "strength": st, "seed": seed, "size": "1024x896", "src": "input/canon_src/yun_head_cover_crop.png", "prompt": STYLE + YUN})
        if f.exists(): continue
        subprocess.run(["draw-things-cli", "generate", "--model", "z_image_turbo_1.0_q8p.ckpt", "--no-download-missing", "--disable-preview",
                        "--image", str(src), "--strength", str(st), "--width", "1024", "--height", "896", "--seed", str(seed),
                        "--prompt", STYLE + YUN, "--output", str(f)], env=env, capture_output=True, text=True, timeout=600)
        print("ok" if f.exists() else "FAIL", f.name, flush=True)
(ROOT / "jobs/yun_i2i.json").write_text(json.dumps(rec, indent=1))
(out / "done.flag").write_text("done")
