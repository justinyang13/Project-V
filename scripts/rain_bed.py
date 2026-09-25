"""Build an hour-long stereo rain bed from many short MOSS-SoundEffect clips (scripts/rain_gen.py). Checks every clip, then crossfades random sequences.
python ../scripts/rain_bed.py --clips work/rain_bed --ref bed_ref --minutes 61 --out work/Video-Zen4/rain_bed_61min.wav
Clip checks, calibrated on the rain the user approved (its own numbers: swing 5.7 dB, event +11.7 dB, tone x16, centroid 3546 Hz; a first, stricter set of limits rejected even that clip):
loudness swing within the clip <= 8 dB (0.5 s windows), no sudden event (any 0.1 s window > 14.7 dB above the clip median), no whistle/tone (spectrum peak <= 30x its neighbourhood),
spectral centroid within 35 % of the approved reference clip. Rejects are listed.
Assembly: every accepted clip is level-matched, its first/last 1.5 s trimmed, and left and right are built from DIFFERENT random orders (never the same clip twice in a row)
joined with 5 s equal-power crossfades, so the two ears are decorrelated (stereo width) and nothing repeats audibly. Also writes <out>_pack.mp3: 8 random 10 s excerpts for listening.
Level: the bed is left at about -30 dB RMS; music_build.py sets the final loudness (--amb_lufs)."""
import argparse, glob, json, os, subprocess
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--clips", required=True); ap.add_argument("--ref", default=None); ap.add_argument("--minutes", type=float, default=61); ap.add_argument("--out", required=True)
ap.add_argument("--max_swing", type=float, default=8.0); ap.add_argument("--max_event", type=float, default=14.7); ap.add_argument("--max_tone", type=float, default=30.0); ap.add_argument("--centroid_tol", type=float, default=0.35)
ap.add_argument("--xfade", type=float, default=5.0); ap.add_argument("--seed", type=int, default=3); ap.add_argument("--min_ok", type=int, default=16)
a = ap.parse_args(); SR = 48000; rng = np.random.default_rng(a.seed)
def load(f):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], check=True, capture_output=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)
def metrics(x):
    y = x[int(1.5 * SR):-int(1.5 * SR)]; w = int(0.5 * SR); n = len(y) // w
    rms = np.array([np.sqrt(np.mean(y[i * w:(i + 1) * w] ** 2)) + 1e-9 for i in range(n)]); db = 20 * np.log10(rms)
    w2 = int(0.1 * SR); n2 = len(y) // w2; r2 = 20 * np.log10(np.array([np.sqrt(np.mean(y[i * w2:(i + 1) * w2] ** 2)) + 1e-9 for i in range(n2)]))
    X = np.abs(np.fft.rfft(y * np.hanning(len(y)))); fr = np.fft.rfftfreq(len(y), 1 / SR); sm = np.convolve(X, np.ones(200) / 200, "same")
    return dict(swing=float(np.percentile(db, 95) - np.percentile(db, 5)), event=float(r2.max() - np.median(r2)), tone=float((X / np.maximum(sm, 1e-12))[(fr > 80) & (fr < 11000)].max()),
                centroid=float((fr * X).sum() / X.sum()), rms_db=float(20 * np.log10(np.sqrt(np.mean(y ** 2)))))
files = sorted(glob.glob(a.clips + "/*.wav")); clips = {os.path.basename(f)[:-4]: load(f) for f in files}
ref_c = metrics(clips[a.ref])["centroid"] if a.ref else None
ok, rep = {}, []
for k, x in clips.items():
    m = metrics(x); why = []
    if m["swing"] > a.max_swing: why.append(f"swing {m['swing']:.1f} dB")
    if m["event"] > a.max_event: why.append(f"event +{m['event']:.1f} dB")
    if m["tone"] > a.max_tone: why.append(f"tone x{m['tone']:.0f}")
    if ref_c and abs(m["centroid"] / ref_c - 1) > a.centroid_tol: why.append(f"centroid {m['centroid']:.0f} Hz vs ref {ref_c:.0f}")
    rep.append((k, m, why));
    if not why: ok[k] = x
print(f"{len(ok)} of {len(clips)} clips accepted")
for k, m, why in rep: print(f"  {k:10s} swing {m['swing']:4.1f}  event {m['event']:4.1f}  tone {m['tone']:5.1f}  centroid {m['centroid']:5.0f}  rms {m['rms_db']:6.1f}  " + ("OK" if not why else "REJECT: " + ", ".join(why)))
if len(ok) < a.min_ok: raise SystemExit(f"only {len(ok)} clips passed (need {a.min_ok}); generate more with rain_gen.py")
names = sorted(ok); tr = int(1.5 * SR); target = 10 ** (-30 / 20)
prep = {}
for k in names:
    y = ok[k][tr:-tr].copy(); y *= target / np.sqrt(np.mean(y ** 2)); prep[k] = y
n = int(a.xfade * SR); t = np.linspace(0, np.pi / 2, n); fo, fi = np.cos(t), np.sin(t)
def channel(total):
    out = None; last = None; used = 0
    while out is None or len(out) < total:
        k = names[int(rng.integers(0, len(names)))]
        if k == last: continue
        y = prep[k]; off = int(rng.integers(0, 3 * SR)); y = y[off:]                     # random start so the seams never line up
        out = y.copy() if out is None else np.concatenate([out[:-n], out[-n:] * fo + y[:n] * fi, y[n:]])
        last = k
    return out[:total]
total = int((a.minutes * 60 + 30) * SR); L = channel(total); R = channel(total)
bed = np.stack([L, R], 1); print(f"bed: {len(bed) / SR:.0f} s, rms L {20*np.log10(np.sqrt(np.mean(L**2))):.1f} dB R {20*np.log10(np.sqrt(np.mean(R**2))):.1f} dB, L/R correlation {np.corrcoef(L[::50], R[::50])[0,1]:.3f}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", a.out], input=bed.astype(np.float32).tobytes(), check=True)
# listening pack: 8 random 10 s excerpts, 0.6 s apart
starts = sorted(rng.uniform(30, a.minutes * 60 - 30, 8)); seg = np.concatenate([np.concatenate([bed[int(s * SR):int((s + 10) * SR)], np.zeros((int(0.6 * SR), 2))]) for s in starts]) * 10 ** (12 / 20)
seg = np.clip(seg, -0.95, 0.95); pack = a.out.replace(".wav", "_pack.mp3")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-b:a", "192k", pack], input=seg.astype(np.float32).tobytes(), check=True)
open(a.out.replace(".wav", "_pack.txt"), "w").write("\n".join(f"{i + 1}: {int(s // 60)}:{int(s % 60):02d}" for i, s in enumerate(starts)) + "\n")
json.dump([{"clip": k, **m, "reject": why} for k, m, why in rep], open(a.out.replace(".wav", "_clips.json"), "w"), indent=1)
print("wrote", a.out, "and", pack)
