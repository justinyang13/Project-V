#!/Users/justin/Code/Project-V/.venv/bin/python
"""Captions from the narration timing (book words only): output/Video-Story1_captions.srt"""
import json, pathlib, subprocess, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.load(open(ROOT / "jobs/timeline.json")); L = json.load(open(ROOT / "jobs/narration.json"))
def ts(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"
rows = []; i = 1
for n in T["narration"]:
    f = sorted((ROOT / "work/tts/lines").glob(f"serena_{n['n']}_*.wav"))[0]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]).decode()) / T["narration_atempo"]
    words = L[n["n"]].split(); chunks = [" ".join(words[k:k + 12]) for k in range(0, len(words), 12)]
    tot = sum(len(c) for c in chunks); t = n["start"]
    for c in chunks:
        d = dur * len(c) / tot; rows.append(f"{i}\n{ts(t)} --> {ts(t + d)}\n{textwrap.fill(c, 42)}\n"); t += d; i += 1
(ROOT / "output").mkdir(exist_ok=True); (ROOT / "output/Video-Story1_captions.srt").write_text("\n".join(rows)); print(len(rows), "captions")
