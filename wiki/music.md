# Music and ambience playbook (local, free, instrumental)

The process is stage 3 (samples, approval) and stage 8 (full hour, softness check, listening pack) of [SPEC.md](SPEC.md); commands in [runbook.md](runbook.md) §3, §8, §M.

Used for the reference run. All local: no cloud, no third-party tracks, no licence questions beyond the model's (ACE-Step 1.5 is MIT-licensed).

## Stack
- **ACE-Step 1.5** (text-to-music) in `tools/ACE-Step-1.5`, API on `127.0.0.1:8001`. Start: `cd tools/ACE-Step-1.5 && ACESTEP_CHECKPOINTS_DIR=/Volumes/SSD-4T-LR/AI/Models/ACE-Step ./start_api_server_macos.sh`. Weights (9.6 GB) live on the SSD; `tools/ACE-Step-1.5/checkpoints` is a symlink to `/Volumes/SSD-4T-LR/AI/Models/ACE-Step` (the `.env` setting alone did NOT redirect downloads).
- `scripts/music_gen.py` — one piece via the API (`--dur`, `--bpm`, `--key`, `--prompt`, `--seed`).
- `scripts/ambience.py` — procedural fire hum + soft wind + gentle crackles (no samples).
- `scripts/music_build.py` — builds the long track: N pieces → filter → **softness check with retakes** → loudness match → equal-power crossfades → slow leveler → ambience mixed under → fades → AAC → final check + listening pack. Resumable; restarts the music server and retries if it crashes. Style comes from `--prompt/--keys/--bpms`.

## Recipe (60 minutes)
```bash
# music server running, then:
(see the runbook §8-§9: music_build.py → listening pack → ffmpeg mux, all from the video folder)
```
Result: 1.1 GB, 3600.000 s, 86,400 video frames (exactly 24 × 3600), music ≈ −22.5 LUFS, ambience ≈ −36 LUFS (14 dB under the music).

## Softness check (`scripts/audio_qc.py`) — added after the first hour had screechy/scratchy moments
- Runs on every generated piece (after the softening filters) and on the finished hour. A piece with **any** harsh event is regenerated with a new seed (up to 4 takes).
- Looks for: sustained high-pitched tone (screech/whistle), harsh brightness, scratch/static (spectral flatness), sudden crackle/glitch bursts, clicks/pops, clipping, dropouts; warns about sudden loud notes.
- `--excerpts N` cuts 8 s clips of the worst moments; `--pack` builds the **listening pack** for the user (6 riskiest moments spread over the hour + 3 random spots, about 72 s, with a timestamp list).
- Claude can't hear: the script finds candidates, the **user's ears confirm**. Limits were calibrated on the first hour; if the user still hears something the check passed (or it flags what the user finds fine), tune `LIMITS` and record it in [lessons.md](lessons.md).

## What we learned
- **Set tempo and key yourself** (`--bpm 44 --key "D minor"`). With the model's built-in planner on, it ignored "slow" in the prompt and picked 91–120 BPM.
- What the user chose (v3b): *"Very slow, soft, gentle ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, a faint distant low flute and a warm airy pad far in the background… 44 BPM"*. A solo shakuhachi flute at 70 BPM was "too harsh and fast".
- **Soften after generating:** low-pass 6.5 kHz + −3 dB high shelf above 3 kHz; match every piece to −22 LUFS with a fixed gain (not dynamic loudnorm).
- **Piece length: 150 s.** A 240 s request crashed the music server during the VAE decode (diffusion was fine). 150 s is stable (~30 s each). Pieces cross-fade 8 s.
- **A slow leveler is needed for long listening:** without it 10-s windows swung from −34.5 to −16.2 dBFS (std 3.8 dB); with it −32.6 to −18.7 (std 2.7 dB). The remaining dips are natural silences in the piano, filled by the ambience.
- Generating short clips is cheap (~10 s for 30 s of audio), so iterate on style with 30 s clips first and only then build the hour.
- Ambience is generated in 124 s chunks with different seeds and 4 s equal-power crossfades, so an hour never repeats.
- Not verified by ear by Claude (it can't listen): no voice-like artifacts, exact instrument realism. The user reviewed the 30 s clips; the full hour is spot-checked by excerpts.
- Two of three "free Japanese music" sites the user cited as a style reference did not load (cert error / suspended account); the third was a frame wrapper. They were used only as a style hint, nothing was downloaded.

## Healing piano with rain (Video-Zen4; from the user's feedback)
**What the user approved:** a "healing song" = very slow, soft piano with a warm airy pad far in the background, D minor, 44 BPM, prompt: *"Very slow, soft, healing ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, a warm airy pad far in the background. Peaceful, calm, tender, comforting, a quiet rainy night by the sea. no drums, no percussion, no vocals, no sharp sounds."* (seed 32 sample; the hour used keys D minor, F major, A minor, C major, G minor and BPM 44, 40, 46, 42).
**Three styles offered, each checked with `audio_qc`:** A piano + pad (chosen), B cello + soft piano, C Rhodes + pad. Harp and nylon-guitar takes failed the check (too bright) even after the low-pass; add "muted, low register, dark rounded tone, no bright sounds" and lower the low-pass to 5.5 kHz with a −5 dB shelf at 2.5 kHz when a style fails.
**Known problem, not yet solved by ear:** "lots of silence" in the prompt makes the piano fall to near-silence every ~5 s (Lessons D12). Ask for a steadier pad and more frequent notes in the prompt, or lift the tails with `scripts/upcomp.py`; check the 1-second envelope of the finished hour, and let the user hear it before the full render.

### Rain (replaces the procedural rain, which the user rejected as "white noise")
- **Model:** MOSS-SoundEffect (`OpenMOSS-Team/MOSS-SoundEffect`, Apache 2.0, 16.7 GB) plus its tokenizer `MOSS-Audio-Tokenizer` (7.1 GB), both in `/Volumes/SSD-4T-LR/AI/Models`. Free, no account. Runs in its own environment `tools/moss-env` (Python 3.12, torch, transformers 5.0.0, soundfile, pillow, opencv). `hf download` stalled on the exFAT SSD (file locks); plain `curl -C -` per file worked.
- **Prompt the user approved (clip r1):** *"Gentle steady rain falling on wet stone streets and tiled roofs at night, soft, soothing and continuous, no thunder, no voices, no music"*, 30 s, mono 24 kHz. Four types were offered (roof/street, eaves and drips, coast with waves, light street rain); the user picked roof/street. The coast clip had a strong tone and about 14 dB of swing: skip "waves" in a rain prompt.
- **Level:** rain −36 LUFS under music −22 LUFS ("subtle", approved) against a "clear" −30 LUFS.
- **Hour:** `scripts/rain_gen.py` (jobs file, model loaded once) makes about 50 clips; `scripts/rain_bed.py` checks each clip (limits set from the approved clip), builds left and right from different random orders with 5 s crossfades, and writes a listening pack. 19 of 49 clips passed. Then `music_build.py --amb_wav <bed.wav> --amb_lufs -36`.
- **Checking:** run `audio_qc` on the music alone, the rain alone and the mix, and judge the mix on clicks, clipping, HF bursts, whistles and dropouts (Lessons D13). Give the user a pack cut from the real mix.

## Snowy-night piano hour (The First Tram and Corner Store, 2026-10-17; approved: sample A + ambience)
**Approved piano (style A):** *"Very slow, soft, healing ambient piano. Gentle felt piano playing a calm flowing melody with steady, frequent soft notes and long sustain, a warm airy pad holding underneath the whole time. Peaceful, tender, comforting, a quiet snowy night in a small town. no drums, no percussion, no vocals, no sharp sounds."**, seed 32, 44 BPM, F major. The hour: `music_build.py --minutes 60 --no_ambience --keys "F major,D minor,C major,A minor,Bb major,G minor" --bpms "44,42,46,40"` (26 pieces of 150 s, ~50 min incl. retakes; most pieces needed 1–3 takes before `audio_qc` passed).
**Other styles tried (all pass `audio_qc` unless noted):** B piano + strings "nostalgic lullaby" (seed 44), C soft electric piano + muted felt piano (seed 54, add "no bells"), D slow jazz-ballad piano (61), E minimalist piano + soft cello (91), F muted upright piano, "late at night so no one wakes up" (82). **Failed:** "nostalgic anime-style piano with flowing arpeggios", 7 seeds, loud note jumps and bright notes; a bell word in a prompt gave a high-frequency tone.
**30 s samples:** ACE-Step pieces asked for 30 s often end at ~23 s and then go silent (that looked like "dips"); generate **40 s and cut 30 s** (fade out 3 s). Sample QC = `audio_qc.py` on the cut MP3 + the share of 1 s windows more than 6 dB under the median (12–25 % is normal for solo piano).
**The finished hour failed the check at first** (2 harsh events, 143 loud-note warnings, 16 % quiet windows): fix = `upcomp.py --max_up 8 --ratio 0.75 --release 1.8` (the older 9 / 0.8 / 1.6 added two dropouts), `loudnorm -22`, and a **local softening** of the 2 harsh spots: crossfade (0.4 s) to a 3× lowpass 2.2 kHz copy over 1.3–2.5 s around each event, then re-run `audio_qc` = 0 harsh events.
**Winter-night ambience (MOSS, `jobs/<id>/amb_jobs.json`, `snow_bed_jobs.json`):** bed = "Quiet snowy winter night in a small town street, soft gentle wind, hushed muffled air, snow falling softly, very calm and peaceful, no voices, no music, no traffic" (18 clips of 30 s, ~19 s each; wind is gusty, so `rain_bed.py` limits are re-calibrated on the approved clip: `--max_swing 11 --max_tone 32 --centroid_tol 0.40 --min_ok 7`; drop clips far quieter than the rest, e.g. −51 dB RMS); hum = "Faint soft electrical hum of a small convenience store heard from outside..." (band 60–2500 Hz, −12.9 dB under the bed); bell = "A single old tram bell ringing twice, very far away down a quiet snowy street at night, soft and distant..." (lowpass 3.5 kHz + light echo, −8 dB, one every 3–7 min). `scripts/amb_layers.py` puts bed + hum + shots together; final mix music −22 LUFS, ambience −36 LUFS (−6.6 dB on the −29.4 LUFS layer), fades 3 s / 6 s → −21.8 LUFS, peak −4.5 dBFS, 0 harsh events.
**Listening pack for the hour:** 12 × 5 s = the 4 biggest note jumps, both softened spots, 3 bells, 3 random moments (`listening_pack.txt` lists their times).

## YouTube notes (from web search on 2026-09-23; verify current policy yourself)
- No YouTube feature loops a short video under a longer audio track: upload one file. 1 h ≈ 1.1 GB (~8 min at 20 Mbps up).
- YouTube's "inauthentic content" (repetitive / mass-produced) rules are enforced per channel and hit ambient/lo-fi channels often; disclose AI-generated content in Studio.
