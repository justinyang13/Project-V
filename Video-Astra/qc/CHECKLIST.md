# Astra identity checklist (every image, every clip, every step)

Automatic (`scripts/cinematic/identity_qa.py`, ComfyUI venv): face ArcFace ≥ 0.55 vs close-up + canon (faces ≥ 80 px), body ratio ≥ 9.0 on standing full-body (sheet 8.9-10.4), suit white+dark ≥ 0.45 and LED glow present (unless the story turns them off), hair bright and low saturation.

Visual (Claude writes a verdict per image in the stage's `*_qc.json`; any "no" = reject):
1. **Face:** same young East Asian woman as the close-up (soft oval face, eye shape, small nose, full lips, smooth skin); not older, not Western, no heavy freckles, calm expression.
2. **Eyes:** light grey-blue.
3. **Hair:** silver-white (not blonde, grey-brown or pure white), high ponytail with black band, long side bangs and face-framing strands.
4. **Marks:** thin glowing blue streaks under the outer eye corners on both cheeks (dark only where the story says so).
5. **Ear implant:** round black device with a blue ring.
6. **Suit:** sheet design: glossy white plates over charcoal-black underlayer, thin blue LED lines on plate edges, high black collar, black hex-ring knees, white boots; no other colours, no capes/helmets/extra parts.
7. **Body:** tall slim athletic adult, ~8 heads tall, long legs, small head, narrow waist (sheet full-body).
8. **Anatomy:** two arms, two legs, five fingers per hand, no merged limbs.
9. **Props/continuity:** the shot's props and damage state (S0-S4) as in the shot list.

## Scene / story / object checks (RULE 0b: every keyframe, clip and the cut)
10. **Props:** each prop from the shot card is present, in the correct hand/side/count/size; flame inside the lantern glass only; blade/energy as specified (straight, from the right place).
11. **No intruders:** no extra people, hooded strangers, animals or objects that are not in the shot card.
12. **Action:** first/middle/last frame show exactly the action on the card (start state → end state).
13. **Continuity:** state S0-S4 (ash, crack, LEDs), lantern flame level, light direction and time of day are right for this point in the story; location matches WORLD.md.
14. **Story flow:** the shot advances the story and is readable without words; the previous shot explains how she got here; fantasy elements obey their rules (ash dissolves, light is a thin blue thread).
15. **Ledger (RULE 0c):** every major item (lantern, blade, ash creatures, maker, ring/brazier, bridge, Astra's state) is exactly where/how `story/ledger.json` says for THIS shot; changes of state happen only in the shot the ledger names.
