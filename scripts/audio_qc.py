"""Find anything unpleasant in audio: screech/whistle, harsh brightness, scratch/static, crackle/glitch bursts, clicks/pops,
clipping/distortion, dropouts, and sudden loud notes. Usable as a CLI (any length: a 30 s piece or the full hour) and as a
module (music_build.py checks every generated piece with piece_ok() and regenerates pieces that fail).

CLI:  python scripts/audio_qc.py <audio> [--out dir] [--excerpts N] [--pack]
      writes <out>/audio_qc.json; --excerpts N = MP3 clips (8 s) of the N worst events; --pack = a listening pack for the user:
      the 6 riskiest moments + 3 random spots, joined, as <out>/listening_pack.mp3 (+ listening_pack.txt with timestamps).

Metrics per 0.25 s frame (mono, 48 kHz) against ABSOLUTE limits (so a bad file can't hide behind its own average):
  hf_ratio    energy 3.5-12 kHz / energy 60 Hz-12 kHz                          harsh / bright / hissy
  hf_tone_db  strongest single peak 2-8 kHz vs the whole frame (dB, lasting >= 0.5 s)  screech / whistle / ringing
  flatness    spectral flatness 2-10 kHz while that band is audible            scratch / static / noise
  hf_burst_db jump of 3.5-12 kHz energy vs the previous frame (while audible)   crackle / glitch / sudden sizzle (normal note onsets: 20-35 dB)
  click       largest sample-to-sample step vs the frame RMS                   clicks / pops
  clip        share of samples at |x| >= 0.98                                  clipping / distortion
  dropout_db  loudness falling off a cliff from a loud frame (not a natural decay)  gaps / glitches
  jump_db     frame vs the previous 3 s median, only among the loudest 5 % of frames  sudden loud notes (warning only)
Calibrated on job 001 (2026-09-23): the user confirmed the flagged moments (16:59, 25:58, 52:41, 53:43) were unpleasant.
"""
import argparse, json, os, subprocess
import numpy as np

SR = 48000; HOP = SR // 4; NFFT = 8192
LIMITS = {"hf_ratio": 0.10, "hf_tone_db": -16.0, "flatness": 0.35, "hf_burst_db": 40.0, "click": 12.0,
          "clip": 0.0005, "dropout_db": 30.0, "jump_db": 12.0}
MIN_FRAMES = {k: 1 for k in LIMITS}; MIN_FRAMES.update(hf_tone_db=2, flatness=2)
HARSH = ["hf_tone_db", "hf_ratio", "flatness", "hf_burst_db", "click", "clip", "dropout_db"]   # jump_db = softer "loud note" warning

def decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)

def analyze(x):
    """x: mono float array at 48 kHz. Returns (summary dict, events sorted worst first)."""
    n = max((len(x) - NFFT) // HOP, 0)
    f = np.fft.rfftfreq(NFFT, 1 / SR); win = np.hanning(NFFT)
    b_all = (f >= 60) & (f <= 12000); b_hf = (f >= 3500) & (f <= 12000); b_ton = (f >= 2000) & (f <= 8000); b_flat = (f >= 2000) & (f <= 10000)
    rows = []; prev_db = []; prev_hf_db = None
    for i in range(n):
        seg = x[i * HOP: i * HOP + NFFT]
        rms = np.sqrt(np.mean(seg ** 2)) + 1e-12; db = 20 * np.log10(rms)
        P = np.abs(np.fft.rfft(seg * win)) ** 2 + 1e-18; tot = P[b_all].sum()
        hf = P[b_hf].sum() / tot
        tone = float(10 * np.log10(P[b_ton].max() / tot)) if db > -50 else -99.0
        pf = P[b_flat]; band_rel = 10 * np.log10(pf.sum() / tot)
        flat = float(np.exp(np.mean(np.log(pf))) / np.mean(pf)) if band_rel > -18 and db > -50 else 0.0
        hf_db = 10 * np.log10(P[b_hf].sum())
        burst = (hf_db - prev_hf_db) if (prev_hf_db is not None and db > -50 and 10 * np.log10(hf + 1e-12) > -30) else 0.0
        prev_hf_db = hf_db
        click = float(np.abs(np.diff(seg)).max() / rms) if db > -55 else 0.0
        clip = float(np.mean(np.abs(seg) >= 0.98))
        base = np.median(prev_db[-12:]) if prev_db else db
        drop = (prev_db[-1] - db) if prev_db and prev_db[-1] > -35 else 0.0
        rows.append((i * HOP / SR, db, hf, tone, flat, burst, click, clip, drop, db - base)); prev_db.append(db)
    names = ["t", "db"] + list(LIMITS)
    R = np.array(rows) if rows else np.zeros((0, len(names)))
    if len(R):
        loud = np.percentile(R[:, 1], 95); R[R[:, 1] < loud, names.index("jump_db")] = 0.0
    events = []
    for key in LIMITS:
        j = names.index(key); idx = np.where(R[:, j] > LIMITS[key])[0] if len(R) else []
        start = None
        for k2, i in enumerate(idx):
            if start is None: start = i
            if k2 == len(idx) - 1 or idx[k2 + 1] != i + 1:
                if i - start + 1 >= MIN_FRAMES[key]:
                    events.append({"metric": key, "start_s": round(float(R[start, 0]), 2), "dur_s": round((i - start + 1) * HOP / SR, 2),
                                   "worst": round(float(R[start:i + 1, j].max()), 4), "limit": LIMITS[key]})
                start = None
    def sev(e):
        over = (e["worst"] - e["limit"]) if e["metric"].endswith("_db") else e["worst"] / e["limit"]
        return over * (1 + e["dur_s"])
    events.sort(key=lambda e: -sev(e))
    harsh = [e for e in events if e["metric"] in HARSH]
    summary = {"duration_s": round(len(x) / SR, 1), "limits": LIMITS,
               "p99": {k: round(float(np.percentile(R[:, names.index(k)], 99)), 4) for k in LIMITS} if len(R) else {},
               "events_by_metric": {k: sum(1 for e in events if e["metric"] == k) for k in LIMITS},
               "harsh_events": len(harsh), "loud_note_warnings": len(events) - len(harsh), "pass": len(harsh) == 0}
    return summary, events

def piece_ok(path):
    """Gate for one generated music piece (used by music_build.py): no harsh events at all."""
    s, ev = analyze(decode(path)); return s["pass"], s, ev

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("audio"); ap.add_argument("--out", default=None)
    ap.add_argument("--excerpts", type=int, default=0); ap.add_argument("--pack", action="store_true")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.audio)[0] + "_qc"; os.makedirs(out, exist_ok=True)
    x = decode(a.audio); s, ev = analyze(x)
    s["file"] = a.audio; s["worst_events"] = ev[:40]
    json.dump(s, open(f"{out}/audio_qc.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in s.items() if k not in ("worst_events", "limits")}, indent=1))
    for key in LIMITS:
        for e in [e for e in ev if e["metric"] == key][:3]:
            m, sec = divmod(e["start_s"], 60); print(f"  {int(m):02d}:{sec:05.2f}  {key:11s} worst {e['worst']} (limit {e['limit']}), {e['dur_s']} s")
    ordered = [e for e in ev if e["metric"] in HARSH] + [e for e in ev if e["metric"] not in HARSH]
    def clip8(st, dst):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(st - 4, 0)), "-t", "8", "-i", a.audio, "-ac", "2", "-ar", "48000",
                        "-c:a", "libmp3lame", "-b:a", "192k", dst], check=True)
    for k, e in enumerate(ordered[:a.excerpts]):
        clip8(e["start_s"], f"{out}/event{k + 1:02d}_{int(e['start_s'] // 60):02d}m{int(e['start_s'] % 60):02d}s_{e['metric']}.mp3")
    if a.pack:   # riskiest 6 (spread out) + 3 random spots, for the user's ears
        picks = []
        for e in ordered:
            if all(abs(e["start_s"] - p) > 30 for p in picks): picks.append(e["start_s"])
            if len(picks) == 6: break
        n_risky = len(picks)
        rng = np.random.default_rng(1); dur = len(x) / SR
        picks += [float(t) for t in rng.uniform(10, max(dur - 10, 11), 3)]
        parts = []
        for k, t in enumerate(picks):
            p = f"{out}/_pack{k}.mp3"; clip8(t, p); parts.append(p)
        lst = f"{out}/_pack.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:a", "libmp3lame", "-b:a", "192k",
                        f"{out}/listening_pack.mp3"], check=True)
        open(f"{out}/listening_pack.txt", "w").write("Listening pack: 8 s clips in this order (the moment is in the middle of each clip)\n" + "".join(
            f"{k + 1}. {int(t // 60):02d}:{t % 60:04.1f}  {'riskiest moments' if k < n_risky else 'random spot'}\n" for k, t in enumerate(picks)))
        for p in parts + [lst]: os.remove(p)
        print("listening pack:", f"{out}/listening_pack.mp3")
