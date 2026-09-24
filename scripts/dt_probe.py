"""Stage 0 probe: one tiny LTX img2img call to learn request/response format, time and output."""
import base64, io, json, sys, time
import requests
from PIL import Image

BASE = json.load(open("jobs/_dt_base/ltx2_i2v.json"))
W, H, FR = 640, 352, 25
img = Image.open("input/001-snow-tea.webp").convert("RGB").crop((11, 0, 1706, 960)).resize((W, H), Image.LANCZOS)
buf = io.BytesIO(); img.save(buf, "PNG")
KEEP = ["model","steps","guidance_scale","sampler","shift","strength","seed_mode","resolution_dependent_shift","speed_up_with_guidance_embed","guidance_embed","start_frame_guidance","guiding_frame_noise","batch_count","batch_size","clip_skip","sharpness","loras","controls","tiled_decoding","tiled_diffusion","hires_fix","upscaler","refiner_model"]
cfg = dict({k: BASE[k] for k in KEEP if k in BASE}, width=W, height=H, num_frames=FR, seed=12345,
           prompt="Static camera. Snow falls slowly downward outside the doorway. A thin wisp of steam rises from the tea cup. Small fire flickers in the brazier. Photorealistic.",
           negative_prompt="camera movement, zoom, pan, morphing")
cfg["init_images"] = [base64.b64encode(buf.getvalue()).decode()]
t = time.time()
r = requests.post("http://127.0.0.1:7860/sdapi/v1/img2img", json=cfg, timeout=1500)
print("status", r.status_code, "seconds", round(time.time() - t, 1), "bytes", len(r.content))
try:
    j = r.json()
    if r.status_code != 200: print(r.text[:600])
except Exception:
    print(r.text[:500]); sys.exit(1)
print("keys", list(j.keys()))
imgs = j.get("images", [])
print("n images", len(imgs))
import os; os.makedirs("work/probe", exist_ok=True)
for i, b in enumerate(imgs[:60]):
    open(f"work/probe/f{i:03d}.png", "wb").write(base64.b64decode(b.split(",")[-1]))
if imgs:
    print("frame size", Image.open("work/probe/f000.png").size)
