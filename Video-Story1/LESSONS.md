# LESSONS — Video-Story1 (book trailer)

What failed, why, and what to do next time. Format follows Project-V lessons. IDs: S = story/pictures, Y = Yun, V = video, A = audio, T = tooling.

| ID | What happened | Why | Do this |
|---|---|---|---|
| S1 | FLUX.2 klein 9B with the book's prompt gave a zip puffer jacket, conical hat and a spiky realistic dragon; Z Image Turbo with the same prompt and seed 733 reproduced the cover (0.21/255 mean difference) | The book was made with Z Image Turbo; models read the same words differently | For "match the existing art exactly" use the model, prompt and seed that made it. Test with the original seed first (RUNLOG 8, 15) |
| S2 | Tiny face-like blobs appeared on rocks, roofs and ground | The style prefix says "expressive kind faces" | Drop that phrase when the picture is not a close-up (`keyframes.py` does) |
| S3 | A drought scene came out lush green | The model paints "rice terraces" green whatever the adjectives | Say "parched pale yellow and brown, cracked dry ochre soil, no green fields anywhere" and reroll (S02r) |
| S4 | Props stick to the wrong person (Hua's map appeared in Mei's hands in 3 of 4 seeds) | Prompt binding is weak with 3+ people | Say who holds it and that the other's hands are empty; still expect to pick the 1 in 4 that is right |
| S5 | A cover crop used as reference had the title text baked into it ("RED THUNDER" in every render) | I copied `cover_front_final.png` (text composed) instead of the art-only file | Always take the art-only cover (`cover_front4.png`); look at the crop before using it |
| Y1 | Strings alone give "a Yun", cuter and smaller, not the cover Yun | Text can't pin a face | Paste the cover head (feathered) into a Yun-free scene, then image-to-image at 0.4–0.55: the head stays the cover design (RUNLOG 19) |
| Y2 | Automatic cut-out (GrabCut) lost antlers and eyes | Thin brown antlers and grey mane look like background | Don't cut out; feather-paste and let image-to-image blend |
| Y3 | Blend strength 0.65 changed Tao's tiger shirt into a round badge and Yun's eye to yellow | High strength rewrites small details | Keep the strength ≤ 0.5 when small print matters; Yun's head survives even at 0.65, small details do not |
| V1 | LTX-2.3 adds a camera push when people are large and close (S06: faces doubled in size by frame 144) | Same cause as Project-V A1/A2 | Never mention the camera; still expect it; measure and choose seeds, or use a still with procedural motion |
| V2 | LTX made floating crossed sticks in the sky (S03) on two seeds | Words like "sticks", "bamboo", "willow" in the motion prompt prime objects | Motion prompt: only the few things that should move, none of the objects you don't want to appear |
| V3 | LTX walked a child out of frame (S13, seed 101) | "Walking/stomping" motion has no boundary | Add "stays in the same place in the picture"; calm prompts freeze expression, so accept stiffer faces |
| V4 | LTX writes 25 fps video for 145 frames (5.8 s) | Draw Things container default | Re-time to 24 fps in the assembler (`setpts=PTS*25/24`) |
| V5 | Memory hit 69 GB used with Qwen loaded beside LTX and everything slowed | 19 GB Qwen + 26 GB video model | `ollama stop <model>` before video renders |
| A1 | Both first ACE-Step pieces failed the softness QC (12–13 events, peaks over 0 dBFS) | Prompt asked for a building, cinematic sound | Prompt "very soft, warm, mellow, no bright or shrill notes, no bells"; low-pass 9 kHz, −4 dB, limiter 0.75; pick the best of 4 seeds (46 s each) |
| A2 | `--speed 1.12` did not shorten the Qwen3-TTS line (longer, in fact) | Sampling variation dominates | Time-compress with ffmpeg `atempo 1.08` |
| A3 | Qwen3-TTS: "Speech tokenizer not loaded" | macOS `._*` junk files on the exFAT model cache | Delete `._*` in the cache (or keep the cache off exFAT) |
| A4 | Only 3 of 21 MOSS clips passed QC outright (all thunder) | Noisy textures (rain, crowd) trip the hiss/harshness limits by nature | Generate 3 seeds, pick the steadiest, low-pass and lower the gain; user's ears decide |
| T1 | Qwen `web_search` returned "No results" for everything | DuckDuckGo bot-blocks | Fallback to GitHub and HuggingFace search APIs added to `qwen_agent.py` |
| T2 | `git push` to the public repo was denied by the permission classifier | Publishing needs the user's explicit permission rule | Ask the user to add a `Bash(git push:*)` rule; do not work around |
| T3 | No `timeout` command on macOS | BSD userland | Use the tool's `timeout` parameter or python `subprocess(timeout=)` |
