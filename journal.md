# Journal

## Current State (2026-05-18)
- Input modes are split by device class.
- Mobile uses gyro only, desktop uses mouse hover only.
- Desktop hover stutter at card corners was reduced by tracking mouse on the non-rotating wrapper and applying light desktop-only tilt smoothing in the rAF loop.

## Files Updated
- holographic-card/holographic-card.html
- holographic-card/holographic-card-editor.html

## Verification
- VS Code diagnostics: no errors in updated files.
- Added standard mask property alongside -webkit-mask in both card files for compatibility.
