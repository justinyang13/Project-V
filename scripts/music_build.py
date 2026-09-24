"""Build a long ambient track: N piano pieces (ACE-Step, local) crossfaded + procedural ambience, leveled, encoded.
python scripts/music_build.py --minutes 60 --out output/001-snow-tea/music_60min
Needs the ACE-Step API running on :8001. Steps are resumable: existing files in work/music/long/ are reused."""
import argparse, glob, os, re, subprocess, sys
import numpy as np

SR = 48000
ap = argparse.ArgumentParser()
ap.add_argument("--minutes", type=float, default=60); ap.add_argument("--piece", type=float, default=150)
ap.add_argument("--xfade", type=float, default=8); ap.add_argument("--out", required=True)
ap.add_argument("--work", default="work/music/long"); ap.add_argument("--music_lufs", type=float, default=-22); ap.add_argument("--amb_lufs", type=float, default=-36)
a = ap.parse_args()
T = a.minutes * 60; W = a.work; os.makedirs(W, exist_ok=True); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
PROMPT = ("Very slow, soft, gentle ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, "
          "a faint distant low flute and a warm airy pad far in the background. Peaceful, calm, tender, sleepy, Japanese winter night. "
          "no drums, no percussion, no vocals, no sharp sounds.")
KEYS = ["D minor", "F major", "A minor", "D minor", "C major", "G minor"]; BPMS = [44, 40, 46, 42]

def run(cmd, **k): return subprocess.run(cmd, check=True, capture_output=True, text=True, **k)
def decode(path, af="anull"):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", af, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], check=True, capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).astype(np.float64)
def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", path], input=x.astype(np.float32).tobytes(), check=True)
def lufs(x):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "ebur128", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr.decode())[-1])
def crossfade_chain(parts, ov):
    n = int(ov * SR); t = np.linspace(0, np.pi / 2, n)[:, None]; fo, fi = np.cos(t), np.sin(t)      # equal-power
    out = parts[0]
    for p in parts[1:]:
        out = np.concatenate([out[:-n], out[-n:] * fo + p[:n] * fi, p[n:]])
    return out

import time, requests
def server_up():
    try: return requests.get("http://127.0.0.1:8001/health", timeout=3).status_code == 200
    except Exception: return False
def ensure_server():
    if server_up(): return
    print("music server down -> restarting", flush=True)
    subprocess.run("pkill -f start_api_server_macos; pkill -f acestep-api", shell=True); time.sleep(3)
    env = dict(os.environ, ACESTEP_CHECKPOINTS_DIR="/Volumes/SSD-4T-LR/AI/Models/ACE-Step")
    subprocess.Popen(["./start_api_server_macos.sh"], cwd="tools/ACE-Step-1.5", env=env, stdout=open("work/acestep_server.log", "a"), stderr=subprocess.STDOUT)
    for _ in range(120):
        time.sleep(5)
        if server_up(): return
    raise SystemExit("music server would not start")

# 1) pieces
n_pieces = int(np.ceil((T + 20 - a.piece) / (a.piece - a.xfade))) + 1
print("pieces needed:", n_pieces, flush=True)
pieces = []
for i in range(n_pieces):
    f = f"{W}/piece{i:02d}.flac"
    for attempt in range(3):
      if os.path.exists(f): break
      ensure_server()
      try:
        run([sys.executable, "scripts/music_gen.py", "--tag", f"{os.path.relpath(W, 'work/music')}/piece{i:02d}", "--seed", str(1000 + i * 7), "--dur", str(a.piece),
             "--bpm", str(BPMS[i % len(BPMS)]), "--key", KEYS[i % len(KEYS)], "--prompt", PROMPT])
      except subprocess.CalledProcessError: print(f"  piece{i:02d} attempt {attempt+1} failed", flush=True); time.sleep(5)
    assert os.path.exists(f), f"could not generate {f}"
    print("generated", f, flush=True)
    x = decode(f, "lowpass=f=6500,highshelf=f=3000:g=-3")
    # trim ACE-Step's possible abrupt ends with short edge fades so the crossfade is clean
    e = int(1.0 * SR); x[:e] *= np.linspace(0, 1, e)[:, None]; x[-e:] *= np.linspace(1, 0, e)[:, None]
    g = a.music_lufs - lufs(x); x *= 10 ** (g / 20); print(f"  piece{i:02d}: gain {g:+.1f} dB", flush=True)
    pieces.append(x)
music = crossfade_chain(pieces, a.xfade); print("music length s:", len(music) / SR, flush=True)

# 1b) slow leveler: pull loud passages down (up to -8 dB) and lift quiet ones a little (up to +3 dB) over ~20 s, so nothing jumps out over hours
def slow_level(x, lo=-8.0, hi=3.0, win=20):
    mono = x.mean(1); n = len(mono) // SR
    p = np.array([np.mean(mono[i * SR:(i + 1) * SR] ** 2) for i in range(n)]) + 1e-12
    env = 10 * np.log10(np.convolve(np.pad(p, win, mode="edge"), np.ones(2 * win + 1) / (2 * win + 1), "valid"))
    g = np.clip(np.median(env) - env, lo, hi)
    g = np.convolve(np.pad(g, 10, mode="edge"), np.ones(21) / 21, "valid")
    gs = np.interp(np.arange(len(x)) / SR, np.arange(n) + 0.5, g)
    print(f"leveler: gain range {g.min():+.1f}..{g.max():+.1f} dB, envelope std {env.std():.2f} dB", flush=True)
    return x * (10 ** (gs / 20))[:, None]
music = slow_level(music)

# 2) ambience in 124 s chunks (seeded), 4 s equal-power crossfades
chunks = []; nc = int(np.ceil((T + 20) / 120))
for i in range(nc):
    f = f"{W}/amb{i:02d}.wav"
    if not os.path.exists(f): run([sys.executable, "scripts/ambience.py", "--dur", "124", "--seed", str(500 + i), "--nofade", "--out", f])
    chunks.append(decode(f))
amb = crossfade_chain(chunks, 4.0); print("ambience length s:", len(amb) / SR, flush=True)

# 3) mix, fade, level
N = int(T * SR); music, amb = music[:N], amb[:N]
amb *= 10 ** ((a.amb_lufs - lufs(amb)) / 20)
mix = music + amb
fi, fo = int(3 * SR), int(10 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
pk = np.abs(mix).max()
if pk > 0.89: mix *= 0.89 / pk; print(f"peak {pk:.2f} -> scaled to 0.89", flush=True)
print(f"final: {N/SR:.0f}s  integrated {lufs(mix):.1f} LUFS  peak {np.abs(mix).max():.2f}", flush=True)
write_wav(a.out + ".wav", mix)
run(["ffmpeg", "-v", "error", "-y", "-i", a.out + ".wav", "-c:a", "aac", "-b:a", "256k", a.out + ".m4a"])
print("wrote", a.out + ".m4a", flush=True)
