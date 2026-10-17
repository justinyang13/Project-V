"""Layer an hour of ambience: a stereo bed (rain_bed.py output) + a faint looped hum + occasional distant one-shots (e.g. a tram bell).
python ../scripts/amb_layers.py --bed work/<id>/snow_bed_61min.wav --hum work/amb/hum1.wav --shots work/amb/bell1.wav work/amb/bell3.wav --out work/<id>/amb_61min.wav
Levels are relative to the bed's loudness (approved sample, The First Tram and Corner Store: hum -12 dB, bell -8 dB under the bed).
Hum: band 60-2500 Hz, looped with 3 s equal-power crossfades. Shots: lowpass 3.5 kHz + light echo, one every --gap s (random), alternating clips, panned a little.
Writes a 48 kHz stereo wav at the bed's level; music_build.py / the final mix sets the overall loudness (-36 LUFS under the music)."""
import argparse, re, subprocess
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--bed", required=True); ap.add_argument("--hum"); ap.add_argument("--shots", nargs="*", default=[]); ap.add_argument("--out", required=True)
ap.add_argument("--hum_db", type=float, default=-12); ap.add_argument("--shot_db", type=float, default=-8); ap.add_argument("--gap", type=float, nargs=2, default=[180, 420])
ap.add_argument("--seed", type=int, default=5)
a = ap.parse_args(); SR = 48000; rng = np.random.default_rng(a.seed)
def dec(f, af="anull", ch=2):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-af", af, "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"], check=True, capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, ch).astype(np.float64)
def lufs(x):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "ebur128", "-f", "null", "-"], input=x.astype(np.float32).tobytes(), capture_output=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr.decode())[-1])
bed = dec(a.bed); N = len(bed); Lb = lufs(bed[: SR * 300]); out = bed.copy()
print(f"bed {N / SR / 60:.1f} min, {Lb:.1f} LUFS")
if a.hum:
    h = dec(a.hum, "highpass=f=60,lowpass=f=2500", 1)[:, 0]; h = h[int(1.5 * SR):-int(1.5 * SR)]; xf = 3 * SR
    t = np.linspace(0, np.pi / 2, xf); seg = []; cur = h.copy()
    while sum(len(s) for s in seg) + len(cur) < N + xf:
        seg.append(cur[:-xf]); nxt = h.copy(); nxt[:xf] = cur[-xf:] * np.cos(t) + h[:xf] * np.sin(t); cur = nxt
    seg.append(cur); hum = np.concatenate(seg)[:N]
    hs = np.stack([hum, hum], 1); g = 10 ** ((Lb + a.hum_db - lufs(hs[: SR * 120])) / 20); out += hs * g
    print(f"hum looped, gain {20 * np.log10(g):.1f} dB")
if a.shots:
    clips = [dec(f, "lowpass=f=3500,aecho=0.6:0.5:180|420:0.25|0.12", 1)[:, 0] for f in a.shots]
    tpos = rng.uniform(20, a.gap[0]); k = 0; placed = []
    while tpos < N / SR - 15:
        c = clips[k % len(clips)]; pan = rng.uniform(-0.35, 0.35); st = int(tpos * SR); n = min(len(c), N - st)
        cs = np.stack([c * (1 - pan) ** 0.5, c * (1 + pan) ** 0.5], 1)[:n]
        g = 10 ** ((Lb + a.shot_db - lufs(np.stack([c, c], 1))) / 20) * rng.uniform(0.7, 1.0)
        out[st:st + n] += cs * g; placed.append(round(tpos / 60, 1)); k += 1; tpos += rng.uniform(*a.gap)
    print(f"{len(placed)} shots at minutes {placed}")
pk = np.abs(out).max(); out *= min(1.0, 0.9 / pk)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", a.out], input=out.astype(np.float32).tobytes(), check=True)
print("wrote", a.out, f"{lufs(out[: SR * 300]):.1f} LUFS (first 5 min)")
