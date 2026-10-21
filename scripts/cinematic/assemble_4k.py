#!/usr/bin/env python3
"""Assemble the 4K master from upscale/<id>_4k.mp4 on a 3840x2160 canvas (2.39 scope bars), per-shot grade + grain in ffmpeg,
per-shot HEVC 10-bit intermediates (crf 12), title card at 4K, concat (stream copy), mux audio. Resumable; skips shots not upscaled yet.
Usage (python3): assemble_4k.py --film <dir> --audio <wav> --out <mp4> [--final]  (--final: also title + concat + mux)"""
import argparse, json, os, subprocess, sys
a = argparse.ArgumentParser(); a.add_argument("--film", required=True); a.add_argument("--audio", required=True); a.add_argument("--out", required=True)
a.add_argument("--final", action="store_true"); o = a.parse_args(); F = os.path.abspath(o.film)
TL = json.load(open(f"{F}/edit/timeline_v2.json"))["timeline"]; S = {s["id"]: s for s in json.load(open(f"{F}/story/SHOTLIST.json"))["shots"]}
W, H, FPS = 3840, 2160, 25; BAR = (H - 1608) // 2; D = f"{F}/edit/graded"; os.makedirs(D, exist_ok=True)
SAT = {"L1": 1.05, "L2": 1.0, "L3": 1.08, "L4": 1.06}
def vf(loc):
    return (f"eq=saturation={SAT.get(loc,1.0)}:contrast=1.03,curves=m='0/0 0.20/0.17 0.5/0.5 0.80/0.84 1/1',"
            f"noise=alls=3:allf=t,pad={W}:{H}:0:{BAR}:black")
codec = ["-c:v", "libx265", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1", "-x265-params", "log-level=error", "-r", str(FPS), "-an"]
parts = []
for i in TL:
    if i == "T01": continue
    src = f"{F}/upscale/{i}_4k.mp4"; out = f"{D}/{i}.mp4"; parts.append(out)
    if os.path.exists(out): continue
    if not os.path.exists(src): print(i, "not upscaled yet", flush=True); continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf(S[i]["location"]), *codec, out], check=True); print(i, "graded", flush=True)
if o.final:
    from PIL import Image, ImageDraw, ImageFont
    tc = f"{D}/T01.mp4"
    if not os.path.exists(tc):
        font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", int(H * 0.09), index=5); txt = "A S T R A"
        img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img); bb = d.textbbox((0, 0), txt, font=font)
        d.text(((W - (bb[2] - bb[0])) // 2, (H - (bb[3] - bb[1])) // 2 - int(H * 0.02)), txt, fill=(170, 210, 255), font=font)
        import numpy as np
        card = np.array(img).astype(np.float32); n = int(TL["T01"][1] - TL["T01"][0]) * FPS
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *codec, tc], stdin=subprocess.PIPE)
        for k in range(n):
            t = k / max(1, n - 1); amp = min(1, t / 0.25) * min(1, (1 - t) / 0.3); p.stdin.write((card * amp).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
    parts.append(tc)
    missing = [p for p in parts if not os.path.exists(p)]
    if missing: sys.exit(f"missing parts: {missing}")
    # order = timeline order
    order = [f"{D}/{i}.mp4" for i in TL]
    open(f"{D}/list.txt", "w").write("".join(f"file '{p}'\n" for p in order))
    tmp = f"{D}/video_only.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{D}/list.txt", "-c", "copy", "-tag:v", "hvc1", tmp], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", o.audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", os.path.abspath(o.out)], check=True)
    print("final", o.out)
