# Audio (2026-10-17) — APPROVED: sample A (piano, seed 32) + round-1 ambience (`mix_a_piano.mp3`)

All: ACE-Step 1.5 via `../scripts/music_gen.py --dur 40` (pieces end early, so 40 s generated, first 30 s used), then
`lowpass=f=6500,highshelf=f=3000:g=-3,loudnorm=I=-22:TP=-3:LRA=7`, fades 2 s / 3 s. All three pass `audio_qc.py` (0 harsh events).

| Sample | Seed | BPM / key | Prompt |
|---|---|---|---|
| A piano | 32 | 44, F major | Very slow, soft, healing ambient piano. Gentle felt piano playing a calm flowing melody with steady, frequent soft notes and long sustain, a warm airy pad holding underneath the whole time. Peaceful, tender, comforting, a quiet snowy night in a small town. no drums, no percussion, no vocals, no sharp sounds. |
| B piano + strings | 44 | 48, C major | Slow nostalgic lullaby on soft felt piano with a warm, gentle string pad underneath, continuous and smooth, tender and cozy, a snowy evening street with warm shop lights. no drums, no percussion, no vocals, no sharp sounds. |
| C electric piano | 54 | 46, A minor | Slow dreamy ambient music, soft warm electric piano and muted felt piano, smooth continuous chords with a mellow pad, calm and cozy, a quiet winter evening watching snow fall. no drums, no percussion, no vocals, no sharp sounds, no bells. |

Rejected on QC: A seeds 33–37 (silence after the piece ended), B seeds 41–43 (1–3 harsh events), C seed 53 (hf tone + jumps).

**Ambience (MOSS-SoundEffect, `jobs/<id>/amb_jobs.json`):** bed2 (snowy night wind, seed 2) at −30 LUFS + hum1 (store hum, seed 3, band 60–2500 Hz) at −42 + bell3 (distant streetcar bell, seed 7, lowpass 3.5 kHz, light echo) at −38 placed at 12 s; whole mix to −36 LUFS under the music (−22). bed1 (22 dB swing) and bell2 (almost silent) not used. Hum clips are tonal at 100/120 Hz, so the hum stays very low.

## Round 2 (user: "give me diff piano")
| Sample | Seed | BPM / key | Prompt |
|---|---|---|---|
| D jazz ballad piano | 61 | 52, Bb major | Slow, warm solo jazz ballad piano, soft rich chords and a gentle melody, played tenderly with soft touch, intimate late-night cafe feeling, cozy snowy evening. no drums, no bass, no percussion, no vocals, no sharp sounds. |
| E piano + cello | 91 | 50, E minor | Slow minimalist neo-classical piano with a soft, warm cello line underneath, tender and calm, long gentle phrases, a quiet snowy night by a lit shop window. no drums, no percussion, no vocals, no sharp sounds. |
| F muted upright piano | 82 | 50, G major | Soft muted upright piano with felt dampers, warm and intimate, slow and simple, close and quiet like playing late at night so no one wakes up, gentle room ambience, cozy winter night. no drums, no percussion, no vocals, no sharp sounds. |

Rejected: "nostalgic anime-style piano with arpeggios" failed QC on 7 seeds (71–77; level jumps and bright notes), so it was replaced by E; F seed 81 (1 harsh event).

## The hour (built from the approved sample A)
`../scripts/music_build.py --minutes 60 --no_ambience --prompt "<prompt A>" --keys "F major,D minor,C major,A minor,Bb major,G minor" --bpms "44,42,46,40"` (26 × 150 s, 8 s crossfades) →
`../scripts/upcomp.py --max_up 8 --ratio 0.75 --release 1.8` → loudnorm −22 → local 3×lowpass 2.2 kHz at 593.35–594.65 s and 2114.75–2117.25 s = `work/<id>/music_60min_fixed.wav`.
Ambience: `../scripts/rain_bed.py --clips work/snow_bed --ref bed_ref --minutes 61 --min_ok 7 --max_swing 11 --max_tone 32 --centroid_tol 0.40` (b23 removed) →
`../scripts/amb_layers.py --hum work/amb/hum1.wav --shots work/amb/bell1.wav work/amb/bell3.wav` = `work/<id>/amb_61min.wav` (−29.4 LUFS).
Mix: ambience −6.6 dB (→ −36 LUFS) under the music, fades 3 s / 6 s, AAC 256k → −21.8 LUFS, peak −4.5 dBFS, 0 harsh events.
