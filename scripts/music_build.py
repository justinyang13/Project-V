"""Build a long ambient track: N piano pieces (ACE-Step, local) crossfaded + procedural ambience, leveled, encoded, checked.
Run from the video folder:  ../.venv/bin/python ../scripts/music_build.py --minutes 60 --out output/<job>/music_60min
Music style: --prompt/--keys/--bpms (defaults = the soft piano approved on job 001).
Every piece is checked with audio_qc (screech, harshness, scratch, crackle, clicks, clipping, dropouts) AFTER the softening filters;
a piece with any harsh event is regenerated with a new seed (up to --tries), and the least-bad take is kept if all fail.
The finished mix is checked again (<out>_qc/audio_qc.json) and a listening pack is written for the user (<out>_qc/listening_pack.mp3).
Needs the ACE-Step API on :8001 (restarted automatically). Resumable: existing pieces in --work are reused (and re-checked)."""
import argparse, glob, json, os, re, shutil, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); import audio_qc

SR = 48000
ap = argparse.ArgumentParser()
ap.add_argument("--minutes", type=float, default=60); ap.add_argument("--piece", type=float, default=150)
ap.add_argument("--xfade", type=float, default=8); ap.add_argument("--out", required=True)
ap.add_argument("--work", default="work/music/long"); ap.add_argument("--music_lufs", type=float, default=-22); ap.add_argument("--amb_lufs", type=float, default=-36)
ap.add_argument("--prompt", default=("Very slow, soft, gentle ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain "
    "and lots of silence, a faint distant low flute and a warm airy pad far in the background. Peaceful, calm, tender, sleepy, Japanese winter night. "
    "no drums, no percussion, no vocals, no sharp sounds."))
ap.add_argument("--keys", default="D minor,F major,A minor,D minor,C major,G minor"); ap.add_argument("--bpms", default="44,40,46,42")
ap.add_argument("--tries", type=int, default=4, help="takes per piece before keeping the least-bad one")
ap.add_argument("--filters", default="lowpass=f=6500,highshelf=f=3000:g=-3")
a = ap.parse_args()
T = a.minutes * 60; W = a.work; os.makedirs(W, exist_ok=True); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
PROMPT = a.prompt; KEYS = [k.strip() for k in a.keys.split(",")]; BPMS = [int(b) for b in a.bpms.split(",")]

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
    os.makedirs("work", exist_ok=True)
    subprocess.Popen(["./start_api_server_macos.sh"], cwd=os.path.join(ROOT, "tools/ACE-Step-1.5"), env=env, stdout=open("work/acestep_server.log", "a"), stderr=subprocess.STDOUT)
    for _ in range(120):
        time.sleep(5)
        if server_up(): return
    raise SystemExit("music server would not start")

# 1) pieces
n_pieces = int(np.ceil((T + 20 - a.piece) / (a.piece - a.xfade))) + 1
print("pieces needed:", n_pieces, flush=True)
def generate(tag, seed, i):
    for attempt in range(3):                                   # server crash retries
        f = f"work/music/{tag}.flac"
        if os.path.exists(f): return f
        ensure_server()
        try:
            run([sys.executable, os.path.join(HERE, "music_gen.py"), "--tag", tag, "--seed", str(seed), "--dur", str(a.piece),
                 "--bpm", str(BPMS[i % len(BPMS)]), "--key", KEYS[i % len(KEYS)], "--prompt", PROMPT])
        except subprocess.CalledProcessError: print(f"  {tag} attempt {attempt + 1} failed", flush=True); time.sleep(5)
    raise SystemExit(f"could not generate {tag}")
def prepare(f):
    x = decode(f, a.filters)
    e = int(1.0 * SR); x[:e] *= np.linspace(0, 1, e)[:, None]; x[-e:] *= np.linspace(1, 0, e)[:, None]   # clean edges for the crossfade
    g = a.music_lufs - lufs(x); x *= 10 ** (g / 20)
    return x, g

pieces = []; qc_log = []; rel = os.path.relpath(W, "work/music")
for i in range(n_pieces):
    best = None
    for take in range(a.tries):
        tag = f"{rel}/piece{i:02d}" + (f"_take{take}" if take else "")
        f = generate(tag, 1000 + i * 7 + take * 100003, i)
        x, g = prepare(f)
        s, ev = audio_qc.analyze(x.mean(1))
        harsh = s["harsh_events"]
        print(f"  piece{i:02d} take{take}: gain {g:+.1f} dB, harsh events {harsh}" + (" OK" if harsh == 0 else " -> retry"), flush=True)
        if best is None or harsh < best[2]: best = (x, f, harsh, s["events_by_metric"])
        if harsh == 0: break
    qc_log.append({"piece": i, "file": best[1], "harsh_events": best[2], "events_by_metric": best[3], "takes": take + 1})
    if best[2]: print(f"  WARNING piece{i:02d}: kept least-bad take with {best[2]} harsh events", flush=True)
    pieces.append(best[0])
json.dump(qc_log, open(a.out + "_pieces_qc.json", "w"), indent=1)
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
    if not os.path.exists(f): run([sys.executable, os.path.join(HERE, "ambience.py"), "--dur", "124", "--seed", str(500 + i), "--nofade", "--out", f])
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
# 4) final check of the finished mix + listening pack for the user
r = subprocess.run([sys.executable, os.path.join(HERE, "audio_qc.py"), a.out + ".m4a", "--out", a.out + "_qc", "--pack"], capture_output=True, text=True)
q = json.load(open(a.out + "_qc/audio_qc.json"))
print(f"final audio check: harsh events {q['harsh_events']}, loud-note warnings {q['loud_note_warnings']} -> {'PASS' if q['pass'] else 'FAIL'}", flush=True)
print("listening pack:", a.out + "_qc/listening_pack.mp3", flush=True)
