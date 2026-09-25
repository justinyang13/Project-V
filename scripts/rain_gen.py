"""Text-to-ambience with MOSS-SoundEffect (Apache 2.0, local, MPS). Replaces the procedural rain of ambience.py.
Run with the tools/moss-env Python (Python 3.12, torch, transformers 5.0.0), from the video folder:
  ../tools/moss-env/bin/python ../scripts/rain_gen.py --jobs jobs/<id>/rain_jobs.json --out work/rain
jobs file: [{"tag": "r1", "prompt": "...", "dur": 20, "seed": 1}, ...]  (1 s = 12.5 tokens; the model is loaded once)
Weights: /Volumes/SSD-4T-LR/AI/Models/MOSS-SoundEffect (+ MOSS-Audio-Tokenizer). Writes <out>/<tag>.wav (mono/stereo as the model returns)."""
import argparse, json, os, time
import numpy as np, soundfile as sf, torch
from transformers import AutoModel, AutoProcessor

M = "/Volumes/SSD-4T-LR/AI/Models/MOSS-SoundEffect"; T = "/Volumes/SSD-4T-LR/AI/Models/MOSS-Audio-Tokenizer"
ap = argparse.ArgumentParser(); ap.add_argument("--jobs", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
dev = "mps" if torch.backends.mps.is_available() else "cpu"; dt = getattr(torch, a.dtype)
proc = AutoProcessor.from_pretrained(M, trust_remote_code=True, codec_path=T)
proc.audio_tokenizer = proc.audio_tokenizer.to(dev)
t0 = time.time()
model = AutoModel.from_pretrained(M, trust_remote_code=True, attn_implementation="sdpa", torch_dtype=dt).to(dev).eval()
print(f"model loaded in {time.time()-t0:.0f}s on {dev} ({a.dtype})", flush=True)
sr = int(proc.model_config.sampling_rate)
for j in json.load(open(a.jobs)):
    f = os.path.join(a.out, j["tag"] + ".wav")
    if os.path.exists(f): print("exists", f); continue
    torch.manual_seed(int(j.get("seed", 1))); t1 = time.time()
    conv = [[proc.build_user_message(ambient_sound=j["prompt"], tokens=int(round(j["dur"] * 12.5)))]]
    batch = proc(conv, mode="generation")
    with torch.no_grad():
        out = model.generate(input_ids=batch["input_ids"].to(dev), attention_mask=batch["attention_mask"].to(dev),
                             max_new_tokens=int(j["dur"] * 12.5) + 64)
    msg = proc.decode(out)[0]; audio = msg.audio_codes_list[0].float().cpu().numpy()
    audio = audio.T if audio.ndim == 2 else audio
    sf.write(f, audio, sr); print(f"{j['tag']}: {len(audio)/sr:.1f}s @ {sr} Hz in {time.time()-t1:.0f}s -> {f}", flush=True)
