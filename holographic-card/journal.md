# Project Journal

## State
- Direction remains Oryzo-inspired with a story split: realistic bench editing mode and premium card showcase mode.
- Preview uses two WebGL layers:
- Card realism layer attached to the card.
- Stage layer behind it (desk, pegboard, cutting mat, paper scraps, dynamic lights/shadows).
- Pen and coaster props were removed.
- Text design editing now includes typography and placement controls:
- Primary font selector (name/title), company font selector.
- Text alignment selector (left/center/right).
- Per-line X/Y offset sliders (line1/line2/line3) to split and position each text line independently.
- Reset button for typography/layout defaults.
- Direct drag editing on card in editor mode: each text line is draggable and updates its matching sliders.
- Drag/click safeguards prevent text-line interaction from accidentally toggling showcase mode.
- Stage now has dual rigs with timed interpolation:
- Editor rig: higher camera angle, workbench lighting balance.
- Showcase rig: hero camera push, stronger key/rim feeling, deeper card separation.
- Tap transition now includes:
- Delayed stage cinematic move,
- One-shot highlight sweep over card,
- Stage post treatment ramp (sat/brightness/blur/scale),
- Smooth return path back to bench mode.

## Validation
- No syntax errors in holographic-card-editor.html.
- Browser verification passed: stage canvas mounts, showcase transform/filter engage on tap, sweep triggers once, and return to editor restores controls/state.
- Browser verification passed: new typography controls render, per-line drag updates offsets, and text-line clicks no longer trigger mode switch.

## Handoff
- Highest-impact next step is swapping procedural desk/board/mat textures with scanned PBR sets and tuning rig intensities to lock final realism.
