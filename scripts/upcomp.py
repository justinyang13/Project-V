"""Upward compressor for sparse piano: lifts the quiet tails between notes so the music no longer 'goes quiet' every few seconds, without raising loud notes.
python ../scripts/upcomp.py in.wav out.wav [--target -22] [--max_up 9] [--release 1.6] [--attack 0.06] [--ratio 0.8]
Level = RMS in 100 ms blocks (both channels). gain_dB = ratio * (target - level) clipped to [-3, +max_up]; the gain follows quickly DOWN (attack, a new note arrives) and slowly UP (release, the tail decays),
so a decaying note is held near the target instead of fading into silence. Blocks below --floor dBFS (true silence / noise floor) are not boosted, so hiss and pauses are not amplified.
A look-ahead of one block is used so a note onset is never boosted for a moment. Output is limited to a peak of 0.89."""
import argparse, subprocess
import numpy as np
SR = 48000
def read(f):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], check=True, capture_output=True); return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).astype(np.float64)
def write(f, x): subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", f], input=x.astype(np.float32).tobytes(), check=True)
def upcomp(x, target=-22.0, max_up=9.0, release=1.6, attack=0.06, ratio=0.8, floor=-62.0, block=0.1):
    B = int(block * SR); n = len(x) // B; lev = np.array([10 * np.log10(np.mean(x[i * B:(i + 1) * B] ** 2) + 1e-12) for i in range(n)])
    want = np.clip(ratio * (target - lev), -3.0, max_up); want[lev < floor] = 0.0
    g = np.zeros(n); cur = 0.0; ka = 1 - np.exp(-block / attack); kr = 1 - np.exp(-block / release)
    for i in range(n):
        nxt = want[min(i + 1, n - 1)]; w = min(want[i], nxt)                    # look-ahead: take the lower of this and the next block
        cur += (ka if w < cur else kr) * (w - cur); g[i] = cur
    gs = np.interp(np.arange(len(x)) / SR, (np.arange(n) + 0.5) * block, g)
    y = x * (10 ** (gs / 20))[:, None]; pk = np.abs(y).max()
    return (y * 0.89 / pk if pk > 0.89 else y), g
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out")
    for k, d in (("target", -22.0), ("max_up", 9.0), ("release", 1.6), ("attack", 0.06), ("ratio", 0.8), ("floor", -62.0)): ap.add_argument("--" + k, type=float, default=d)
    a = ap.parse_args(); y, g = upcomp(read(a.inp), a.target, a.max_up, a.release, a.attack, a.ratio, a.floor); write(a.out, y); print(f"gain range {g.min():+.1f}..{g.max():+.1f} dB, mean {g.mean():+.1f}")
