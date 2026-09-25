# Music (approved by the user, 2026-09-24): sample A, piano + pad
- Prompt: "Very slow, soft, healing ambient piano. Sparse felt piano notes, warm and muted, played very softly with long sustain and lots of silence, a warm airy pad far in the background. Peaceful, calm, tender, comforting, a quiet rainy night by the sea. no drums, no percussion, no vocals, no sharp sounds."
- Sample: seed 32, BPM 44, key D minor (30 s, audio_qc pass, about -22 LUFS). Sample filters: lowpass 6500, highshelf 3000 -3 dB.
- For the hour: `--keys "D minor,F major,A minor,C major,G minor" --bpms "44,40,46,42"` (runbook 8).
- Rejected on the softness check (too bright): harp (F major), nylon guitar (A minor). B (cello + piano, seed 62) and C (Rhodes, seed 84) passed but were not chosen.
- Ambience: rain, from a new model (MOSS-SoundEffect) instead of the procedural `ambience.py` rain.
- Rain chosen by the user (2026-09-24): **r1**, prompt "Gentle steady rain falling on wet stone streets and tiled roofs at night, soft, soothing and continuous, no thunder, no voices, no music" (MOSS-SoundEffect, seed 11 for the sample; mono 24 kHz; tools/moss-env + scripts/rain_gen.py). Rain level (clear -30 LUFS vs subtle -36 LUFS, music -22) still to be chosen.
- Rain level approved by the user (2026-09-24): **subtle**, rain -36 LUFS under music -22 LUFS (14 dB under). Approval 3 complete.
