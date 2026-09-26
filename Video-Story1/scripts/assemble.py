#!/Users/justin/Code/Project-V/.venv/bin/python
"""Assemble the trailer from jobs/timeline.json. usage: assemble.py [--video-only] [--out output/name.mp4] [--clips-dir work/clips]
Picture: each shot's LTX clip (25 fps frames re-timed to 24 fps), slowed up to 1.2x and last frame held to fit its slot, lanczos to 1920x1080, 0.5 s cross-dissolves,
text cards with fades, end card with a slow push. Audio (if present): narration lines (atempo), work/audio/music.wav (ducked under the voice), work/audio/sfx.json items; loudnorm -14 LUFS."""
import json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent; os.chdir(ROOT)
T = json.load(open("jobs/timeline.json")); a = sys.argv[1:]
vid_only = "--video-only" in a; out = a[a.index("--out") + 1] if "--out" in a else "work/assembled.mp4"
cdir = a[a.index("--clips-dir") + 1] if "--clips-dir" in a else "work/clips"
sel = json.load(open("jobs/clip_choice.json")) if os.path.exists("jobs/clip_choice.json") else {}
d = T["xfade"]; shots = T["shots"]; inputs = []; filt = []; BASE = 145 / 24
for i, s in enumerate(shots):
    clip = sel.get(s["id"], s["clip"]); inputs += ["-i", f"{cdir}/{clip}/clip.mp4"]
    L = s["dur"] + d; f = min(max(L / BASE, 1.0), 1.2)
    filt.append(f"[{i}:v]setpts=PTS*{f * 25 / 24:.5f},fps=24,scale=1920:1080:flags=lanczos,tpad=stop_mode=clone:stop_duration=8,trim=duration={L:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
n = len(shots); e = T["end"]
inputs += ["-loop", "1", "-framerate", "24", "-t", f"{e['dur'] + d:.2f}", "-i", e["img"]]
N = int((e["dur"] + d) * 24)
filt.append(f"[{n}:v]scale=2112:1188,zoompan=z='1+0.04*on/{N}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24,format=yuv420p,fade=t=out:st={e['dur'] + d - 1.2:.2f}:d=1.2[v{n}]")
acc = "v0"; A = shots[0]["dur"] + d
for i in range(1, n + 1):
    off = A - d; filt.append(f"[{acc}][v{i}]xfade=transition=fade:duration={d}:offset={off:.3f}[x{i}]"); acc = f"x{i}"
    A += (shots[i]["dur"] + d if i < n else e["dur"] + d) - d
k = n + 1; cur = acc
for c in T["cards"]:
    inputs += ["-loop", "1", "-framerate", "24", "-t", f"{c['end'] + 1:.2f}", "-i", f"work/cards/{c['png']}.png"]
    filt.append(f"[{k}:v]format=rgba,fade=t=in:st={c['start']}:d=0.5:alpha=1,fade=t=out:st={c['end'] - 0.5}:d=0.5:alpha=1[c{k}]")
    filt.append(f"[{cur}][c{k}]overlay=enable='between(t,{c['start']},{c['end']})':format=auto[o{k}]"); cur = f"o{k}"; k += 1
filt.append(f"[{cur}]trim=duration={T['total']},setpts=PTS-STARTPTS[vout]")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs; maps = ["-map", "[vout]"]
if not vid_only:
    aud = []; ai = k
    for nn in T["narration"]:
        f = sorted(pathlib.Path("work/tts/lines").glob(f"serena_{nn['n']}_*.wav"))[0]; cmd += ["-i", str(f)]
        ms = int(nn["start"] * 1000); aud.append(f"[{ai}:a]atempo={T['narration_atempo']},aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms},apad[n{ai}]"); ai += 1
    voice = "".join(f"[n{j}]" for j in range(k, ai)); aud.append(f"{voice}amix=inputs={len(T['narration'])}:normalize=0:duration=longest,volume=1.0,atrim=duration={T['total']}[voice]")
    mix = ["[voice]"]; 
    if os.path.exists("work/audio/music.wav"):
        cmd += ["-i", "work/audio/music.wav"]; aud.append(f"[{ai}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration={T['total']}[mus0]")
        aud.append("[voice]asplit=2[vo][vsc]"); aud.append("[mus0][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=600[musd]"); mix = ["[vo]", "[musd]"]; ai += 1
    if os.path.exists("work/audio/sfx.json"):
        for it in json.load(open("work/audio/sfx.json")):
            cmd += ["-i", it["file"]]; ms = int(it["start"] * 1000)
            aud.append(f"[{ai}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={it.get('gain', 1.0)},adelay={ms}|{ms}[s{ai}]"); mix.append(f"[s{ai}]"); ai += 1
    aud.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,atrim=duration={T['total']},afade=t=out:st={T["total"]-2.5:.2f}:d=2.5,loudnorm=I=-14:TP=-2:LRA=9[aout]")
    filt += aud; maps += ["-map", "[aout]"]
cmd += ["-filter_complex", ";".join(filt)] + maps + ["-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "24"]
if not vid_only: cmd += ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
cmd += ["-t", str(T["total"]), out]
os.makedirs(os.path.dirname(out) or ".", exist_ok=True); open("work/assemble_cmd.txt", "w").write(" ".join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True); print("rc", r.returncode, (r.stderr or "")[-1500:]); print("wrote", out)
