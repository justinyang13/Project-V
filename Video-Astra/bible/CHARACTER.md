# Astra: character bible (from the sheet)

Source: `input/astra_sheet_preview_1536.webp` (1536x1024 preview, 2026-10-19). **Redo the crops and colour sampling from the 8K sheet when it arrives**; the text below is read from the preview and should still hold.

## Identity (sheet header)
- **Name:** Astra. **Type:** android / AI companion. **Gender:** female. **Height:** 168 cm (5'6"). **Build:** slim, athletic. **Apparent age:** 20s.
- **Tagline:** "Not just a machine. A companion for what's next."
- **Tech notes:** synthetic skin (realistic texture), advanced facial recognition, emotion simulation, multi-language support, self-repair system.
- **Materials:** ceramic composite armor, carbon fibre frame, titanium alloy joints, blue LED light strips, matte and gloss finish.
- **Logo:** stylised "A" chevron in light blue (sheet top-right).

## Face (identity reference = `input/astra_face_ref.webp` close-up, user 2026-10-19)
The user supplied a close-up whose face differs a little from the sheet (sheet faces score only 0.34-0.47 ArcFace vs it). **The close-up is the identity**; the sheet gives hair style, marks, armor and outfits. Close-up specifics: soft oval face, gentle rounded jaw, light freckles across nose and cheeks, natural full lips with a faint closed-lip smile, light grey eyes with dark limbal rings, soft straight brows; the close-up shows a messy updo with blue LED hair clips and no face mark (the film uses the sheet's ponytail and marks).
- East Asian features, soft oval face, small pointed chin, smooth pale porcelain skin with a light natural blush.
- Eyes: **light grey-blue irises** (between the close-up's grey and the sheet's blue), large, slightly almond, with a dark limbal ring; long lower lashes; soft natural brows, light ash-grey.
- Nose small and straight; lips full, natural rosy pink, usually closed or slightly parted.
- **Face marks (signature):** thin glowing light-blue streak marks on **both cheeks** just below the outer corners of the eyes, angled down toward the ears; the one on her **left cheek** (viewer's right) is the brighter chevron/lightning shape (sheet detail panel). Not in the close-up; added by prompt and trained into the LoRA dataset. Story-critical (they fade and return).
- Default expression: calm, warm, faintly curious. Big laughs and wide-open mouths drift the face (sheet's laugh/surprised panels look like a different person), so the film uses neutral, thoughtful, determined, sad, slight smile.

## Hair
- **Silver-white / pale silver with a faint lavender-grey cast**, long, straight, fine strands.
- **High ponytail** at the crown, tied with a **black band plus a small black-and-blue tech clip**. Long side-swept bangs and loose face-framing strands on both sides that fall past the jaw.
- Never blonde, never pure white, never short, never loose without the ponytail (unless a shot asks for it on purpose).

## Tech details
- **Ear implants:** both ears, round black device inside the ear/behind it, with a **glowing blue ring**; thin blue circuit lines run back from it.
- **Neck/nape:** black collar armor with a round **blue glowing port** at the nape and blue line accents along the spine.
- **Hands (armor):** articulated white-and-black plated fingers, blue line accents.

## Outfit A: Default Armor (film default)
- Sleek bodysuit armor: **gloss/ceramic white plates** over a **charcoal/black flexible underlayer**, with **thin glowing blue LED lines** following the plate edges.
- High black collar to the jaw; white shoulder-chest plates; bare-looking pale arms at the upper arm in the sheet's half-body view, then white forearm gauntlets with black joints; segmented black abdomen; white thigh plates; black knees; **white boots** with black soles and blue accents; spine of blue-lit vertebra plates on the back.
- Silhouette: smooth and form-fitting; no capes, no helmets, no weapons on the sheet.

## Other outfits on the sheet (allowed only if the story calls for them)
Casual (white crop top, olive cargo pants, grey jacket) · Sport (black sports bra, leggings) · Dress (cream sleeveless dress) · Winter (black puffer jacket, black pants, boots) · Hiking (teal jacket, dark pants, boots) · Beach (light blue swimwear + white cover-up) · Business (black suit, white shirt, heels). The face, hair, ponytail, face mark and ear implants stay in every outfit.

## Palette (from the sheet swatches; resample hex from the 8K sheet)
- White `#F4F5F7` (armor plates) · light grey `#C9CCD1` · charcoal `#2A2D31` (underlayer) · deep blue `#1E3A8A` (brand/LED base) · LED glow light cyan-blue `#5CC8FF`.

## LOCK list (in every prompt)
`astra`, silver-white hair in a high ponytail with long side bangs, light grey-blue eyes, light freckles, thin glowing blue streak marks below the outer corners of both eyes, round blue-glowing ear implants, (outfit block for the shot; default: white ceramic and black armor bodysuit with thin glowing blue lines, high black collar, white boots).

## NEVER list (reject on sight)
Blonde/yellow/brown/pure-white hair; hair down without ponytail; brown/green/red eyes; missing face marks (except shots where they are dark by story); missing ear implants; armor in other colours (red, gold, silver-chrome); helmet; cape; extra mechanical parts on the face; visible seams across the face; heavy makeup; aged or childlike face; a second Astra in frame; text or labels in the image.

## Personality (for performance in the story)
Composed, observant, gentle; protective rather than aggressive; learning what feeling means. In action she is precise and economical: no wasted motion. Moments of stillness and of looking carry her inner life.
