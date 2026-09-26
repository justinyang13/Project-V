#!/Users/justin/Code/Project-V/.venv/bin/python
"""Render narration lines with Qwen3-TTS (mlx-audio). usage: narrate.py <voice> <prefix> [N1 N2 ...]  -> work/tts/lines/<prefix>_<N>.wav"""
import json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
L = json.load(open(ROOT / "jobs/narration.json")); voice, prefix = sys.argv[1], sys.argv[2]; ids = sys.argv[3:] or list(L)
env = dict(os.environ, HF_HOME="/Volumes/SSD-4T-LR/AI/hf-cache")
for n in ids:
    out = ROOT / "work/tts/lines"; f = out / f"{prefix}_{n}"
    if list(out.glob(f"{prefix}_{n}_*.wav")): continue
    r = subprocess.run([str(ROOT.parent / "tools/tts-venv/bin/python"), "-m", "mlx_audio.tts.generate", "--model", "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit",
        "--text", L[n], "--voice", voice, "--lang_code", "English", "--instruct", "Speak slowly, warmly and gently, like a bedtime story read aloud to a child.",
        "--speed", os.environ.get("TTS_SPEED", "1.0"), "--output_path", str(out), "--file_prefix", f.name], env=env, capture_output=True, text=True)
    print(n, "ok" if list(out.glob(f"{prefix}_{n}_*.wav")) else "FAIL " + r.stderr[-200:], flush=True)
print("NARR_DONE", flush=True)
