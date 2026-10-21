# Video-Astra: STATE (updated 2026-10-20 ~20:40)

Autonomous; user asleep/away. Heartbeat cron 1e5117ba every 15 min until the 4K film is delivered. RULE 0 (every image/frame vs the sheet incl. body) applies at every step.

## Done
- Bible, story "The Last Lantern", shotlist (40 shots, 171.5 s), 39 keyframes (qc/keyframes_storyboard.jpg), 39 LTX clips (clips/<id>/chosen.mp4, rejects in clips/_rejected).
- Cut v1: edit/cut_v1.mp4 (1080p, silent) + edit/cut_v1_audio.mp4 (with audio). Trims in edit_trims.json (A04 2.5 s, B07 1.3 s). Timeline edit/timeline_v1.json.
- Audio: 4 music cues audio/proc/cue*.wav (all audio_qc pass), 36 MOSS SFX audio/sfx, mix script audio/mix.py → audio/mix/mix_final.wav (-18 LUFS, TP -3): audio_qc 0 harsh, 5 loud-note warnings.
- Sent to user: storyboard, v1 silent preview, v1 audio preview.

## Now
- Stage 8: full review of cut v1 (identity per shot on the cut, joins, look timeline, weak clips: A05 handoff, B07 burst, C10 no collapse, D04 low motion), fix → cut v2.

## Next
- Stage 9: SeedVR2 3B at 3840x1608, batch 9, ~14 s/frame (~17 h). Per-shot, resumable. Then regrade/grain, mux final audio, deliver output/ (3 files) + qc/qc-report.md.

## HANDOFF 2026-10-21 3:20PM (new session)
Done: clip redo pass (A05,B06,B07,B08,B10,C04,C07,C08,C10,D01 chosen; C08 s32 borderline, lantern low). A09 doorway redo running: keyframes/run6.log then clips/run4.log (seeds 34-36, auto-chained). Review A09 take against ledger.
Next: (1) pick A09 take; (2) timeline v3 = v2 minus D03, with new D01 (clips/D01/chosen.mp4, 121 frames) and changed shots; (3) remix audio for v3 (adapt audio/mix_v2.py), audio_qc; (4) edit_cut.py 1080p cut with audio; (5) own review vs ledger/RULE 0b; (6) SEND whole movie (1080p+audio+storyboard) to user and WAIT for approval (4K GATE); (7) after approval re-upscale only changed shots, keep all existing 4K, assemble_4k.py, final QC, output/.
Heartbeat: session-only cron every 30 min (old session job fcbc392b dies with it): recreate in the new session, ends 2026-10-21T14:40Z. Token saving: quiet tool output (tail -n 3), one small contact sheet per shot, scripts for checks.

## 2026-10-21 3:25PM: cut v3 ready, 4K GATE
A09 take s34 kept (s36 turns to camera, body distorts). Cut v3: edit/cut_v3.mp4 + edit/cut_v3_audio.mp4 (149.4 s), timeline edit/timeline_v3.json (v2 minus D03, new D01), audio/mix_v3.py -> audio/mix/mix_final_v3.wav (audio_qc pass, 0 harsh, 5 loud-note warnings). edit_cut.py now takes --skip and --timeline. assemble_4k.py still reads timeline_v2: switch to v3 after approval.
Next: user approves v3 -> re-upscale only changed shots (A05,B06,B07,B08,B10,C04,C07,C08,C10,D01,A09), keep other 4K, assemble_4k.py, final QC, output/.
