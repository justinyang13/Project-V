"""Procedural, endlessly variable ambience: soft fire (low warm roar + sparse gentle crackles), soft wind, and soft rain (--rain). No samples, no licences.
python scripts/ambience.py --dur 30 --seed 1 --out work/music/amb_30.wav [--fire 1.0 --wind 1.0 --crackle 1.0 --rain 0.0]  (rain scene: --rain 1.0 --fire 0.25 --wind 0.3 --crackle 0.3)
Levels are relative; final level is set in the mix step. Stereo, 48 kHz, 16-bit WAV. Same seed = same output."""
import argparse, wave
import numpy as np

SR = 48000
ap = argparse.ArgumentParser()
ap.add_argument("--dur", type=float, default=30); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--fire", type=float, default=1.0); ap.add_argument("--wind", type=float, default=1.0)
ap.add_argument("--crackle", type=float, default=1.0); ap.add_argument("--rain", type=float, default=0.0); ap.add_argument("--rain_style", default="window", choices=["window", "patter", "roof", "drizzle"]); ap.add_argument("--nofade", action="store_true"); ap.add_argument("--out", required=True)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
N = int(a.dur * SR)

def bandpass(x, lo, hi):                       # FFT band-pass, fine for offline use
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(float)
    k = max(int(len(m) * 0.0004), 2); m = np.convolve(m, np.ones(k) / k, "same")   # soften band edges
    return np.fft.irfft(X * m, len(x))

def slow_lfo(rate_hz, depth, n):               # smooth random modulation around 1.0
    pts = max(int(a.dur * rate_hz), 2) + 2
    y = np.interp(np.linspace(0, pts - 1, n), np.arange(pts), rng.standard_normal(pts))
    return 1 + depth * y / (np.abs(y).max() + 1e-9)

def channel():
    # warm fire "roar": band-limited noise 90-700 Hz, slowly breathing
    roar = bandpass(rng.standard_normal(N), 90, 700) * slow_lfo(0.15, 0.35, N)
    roar /= np.abs(roar).max() + 1e-9
    # soft wind: 150-900 Hz noise with slow gusts
    wind = bandpass(rng.standard_normal(N), 150, 900) * np.clip(slow_lfo(0.06, 0.8, N), 0.1, None)
    wind /= np.abs(wind).max() + 1e-9
    # gentle crackles: sparse, small, rounded (lowpassed to 3.5 kHz), no loud pops
    crk = np.zeros(N)
    t = 0.0
    while t < a.dur:
        t += rng.exponential(0.45)                                   # ~2 crackles per second on average
        i = int(t * SR)
        L = int(rng.uniform(0.004, 0.02) * SR)
        if i + L >= N: break
        env = np.exp(-np.linspace(0, rng.uniform(5, 9), L))
        crk[i:i + L] += rng.standard_normal(L) * env * min(rng.pareto(3.0) + 0.3, 1.6) * rng.uniform(0.3, 1.0)
    crk = bandpass(crk, 300, 3500); crk /= np.abs(crk).max() + 1e-9
    # rain = many individual drop impacts (not filtered noise, which just sounds like white noise): four layers, weights per --rain_style
    def drops(rate, f_lo, f_hi, tau_lo, tau_hi, amp_lo, amp_hi, chirp=0.0):
        y = np.zeros(N); t = 0.0
        while True:
            t += rng.exponential(1.0 / rate); i = int(t * SR)
            if i >= N - 10: break
            tau = rng.uniform(tau_lo, tau_hi); Ld = min(int(tau * 6 * SR), N - i)
            tt = np.arange(Ld) / SR; f0 = np.exp(rng.uniform(np.log(f_lo), np.log(f_hi)))
            ph = 2 * np.pi * (f0 * tt - chirp * f0 * (1 - np.exp(-tt / tau)) * tau)   # chirp>0: pitch falls (a "plip")
            ph1, ph2 = rng.uniform(0, 6.28, 2); wave_ = (np.sin(ph) + 0.6 * np.sin(1.41 * ph + ph1) + 0.4 * np.sin(2.13 * ph + ph2)) / 2   # inharmonic partials: a tick, not a whistle
            y[i:i + Ld] += wave_ * np.exp(-tt / tau) * amp_lo * (amp_hi / amp_lo) ** rng.random() * rng.choice([-1, 1])
        return y
    fine = drops(500, 1800, 4500, 0.0006, 0.002, 0.05, 0.25) * slow_lfo(0.05, 0.2, N)    # dense fine patter
    glass = drops(28, 1100, 3000, 0.004, 0.014, 0.2, 0.9)                                  # ticks on the window pane
    drip = drops(1.6, 250, 900, 0.02, 0.05, 0.4, 1.0, chirp=0.35)                         # occasional soft "plip" drips
    bed = bandpass(rng.standard_normal(N), 180, 1100) * np.clip(slow_lfo(0.04, 0.3, N), 0.4, None)   # distant wash / roof
    bed /= np.abs(bed).max() + 1e-9
    W = {"window": (0.6, 1.0, 0.6, 0.25), "patter": (1.0, 0.25, 0.3, 0.45), "roof": (0.7, 0.15, 0.7, 1.0), "drizzle": (0.35, 0.5, 0.8, 0.12)}[a.rain_style]
    def nrm(x): return x / (np.abs(x).max() + 1e-9)
    rn = W[0] * nrm(fine) + W[1] * nrm(glass) + W[2] * nrm(drip) + W[3] * bed
    rn = bandpass(rn, 120, 5500); rn = nrm(rn); dr = np.zeros(N)
    return roar, wind, crk, rn, dr

L, R = channel(), channel()
def mix(c): return a.fire * 0.6 * c[0] + a.wind * 0.35 * c[1] + a.crackle * 0.5 * c[2] + a.rain * c[3]
y = np.stack([mix(L), mix(R)], 1)
fade = int(2 * SR); env = np.ones(N); env[:fade] = np.linspace(0, 1, fade); env[-fade:] = np.linspace(1, 0, fade)
y = y * (np.ones_like(env) if a.nofade else env)[:, None]; y = y / (np.abs(y).max() + 1e-9) * 0.9
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype("<i2").tobytes())
print("wrote", a.out, f"{a.dur}s")
