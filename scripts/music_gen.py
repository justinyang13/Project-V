"""Generate instrumental music with the local ACE-Step API (server: tools/ACE-Step-1.5/start_api_server_macos.sh, port 8001).
python scripts/music_gen.py --tag flute_a --seed 11 --dur 30 [--prompt "..."]  -> work/music/<tag>.flac"""
import argparse, json, os, time, requests
ap = argparse.ArgumentParser()
ap.add_argument("--tag", required=True); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--dur", type=float, default=30)
ap.add_argument("--prompt", default=("Slow ambient meditation music, solo shakuhachi bamboo flute with soft breathy tone, "
    "warm sustained notes and gentle pauses, faint soft synth pad underneath, very quiet, calm, peaceful, snowy winter night in a Japanese tea room, "
    "no drums, no percussion, no vocals, minimal, spacious reverb, 60 bpm"))
ap.add_argument("--steps", type=int, default=8); ap.add_argument("--bpm", type=int, default=48)
ap.add_argument("--key", default="D minor"); ap.add_argument("--sig", default="4")
a = ap.parse_args()
U = "http://127.0.0.1:8001"
body = {"prompt": a.prompt, "lyrics": "[Instrumental]", "instrumental": True, "audio_duration": a.dur, "thinking": True,
        "seed": a.seed, "bpm": a.bpm, "key_scale": a.key, "time_signature": a.sig, "use_cot_caption": False, "use_cot_language": False, "use_cot_metas": False, "use_random_seed": False, "inference_steps": a.steps, "batch_size": 1, "audio_format": "flac"}
r = requests.post(f"{U}/release_task", json=body, timeout=60); r.raise_for_status()
j = r.json(); tid = (j.get("data") or j)["task_id"]; print("task", tid, flush=True)
t0 = time.time()
while True:
    q = requests.post(f"{U}/query_result", json={"task_id_list": [tid]}, timeout=60).json()
    d = (q.get("data") or q)[0]
    if d["status"] == 1: break
    if d["status"] == 2: raise SystemExit("FAILED: " + json.dumps(d)[:800])
    time.sleep(3)
res = json.loads(d["result"])[0]
out = f"work/music/{a.tag}.flac"; os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "wb").write(requests.get(U + res["file"], timeout=120).content)
print(f"done in {time.time()-t0:.0f}s -> {out}\nmetas: {res.get('metas')}")
