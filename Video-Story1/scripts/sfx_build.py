#!/Users/justin/Code/Project-V/.venv/bin/python
"""Process the chosen MOSS clips (low-pass, gain, fades, trim, 48 kHz stereo) and write work/audio/sfx.json for assemble.py.
Chosen from the QC table in RUNLOG: thunder_1 (only clip passing), rain_3, cheer_2, bamboo_1, pool_1, bell_1, roomtone_1."""
import json, os, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; os.chdir(ROOT); os.makedirs("work/audio/sfx", exist_ok=True)
# name, source, start(s), dur(s), gain(dB), lowpass(Hz), fade_in, fade_out
P = [("roomtone", "roomtone_1", 0.0, 10.1, 3, 6000, 0.5, 3.0),
     ("bell", "bell_1", 33.5, 10.0, 8, 7000, 0.3, 1.5),
     ("bamboo_a", "bamboo_1", 34.0, 14.1, -8, 7500, 1.5, 1.5),
     ("pool_a", "pool_1", 48.0, 14.0, -20, 7500, 1.5, 1.5),
     ("pool_b", "pool_1", 61.5, 7.0, -20, 7500, 1.0, 3.0),
     ("thunder", "thunder_1", 64.8, 12.0, -3, 4500, 0.5, 4.0),
     ("cheer", "cheer_2", 71.5, 12.0, -3, 7000, 1.0, 3.5),
     ("rain", "rain_3", 74.0, 14.0, -6, 8000, 2.0, 0.0)]
out = []
for name, src, start, dur, gain, lp, fi, fo in P:
    f = f"work/audio/sfx/{name}.wav"; af = f"atrim=duration={dur},lowpass=f={lp},afade=t=in:d={fi}" + (f",afade=t=out:st={dur - fo}:d={fo}" if fo else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"work/audio/sfx_raw/{src}.wav", "-af", af, "-ar", "48000", "-ac", "2", f], check=True)
    out.append({"file": f, "start": start, "gain": round(10 ** (gain / 20), 3), "name": name})
json.dump(out, open("work/audio/sfx.json", "w"), indent=1); print(len(out), "sfx")
