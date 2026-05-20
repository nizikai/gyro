# Journal

## Current State (2026-05-18)
- File: `holographic-card/holographic-card-editor.html`.
- Holographic overlay feature has been removed end-to-end:
  - Deleted `HolographicLayer` class and all runtime lifecycle wiring.
  - Removed holographic include toggle (`check-holo`).
  - Removed holographic intensity slider (`slider-holo`).
  - Removed helper/state/preset bindings (`getHoloEl`, `includes.holo`, `holoOpacity`).
- Active visual stack now relies on:
  - Base card lighting (`.card::after` smooth sheen).
  - Specular layer (`.specular-layer`) with controllable intensity.
  - Optional realism layer (`RealismLayer`) in `mesh-gradient` or `foil-physical` mode.
  - Optional grain and sticker detail layers.
- Text cutout mask remains dynamic and synced to live text + include toggles.
- Grain remains static (no time animation).
- Three.js is pinned to `three@0.149.0` with jsDelivr fallback; favicon 404 suppression remains in place.

## Verification
- VS Code diagnostics: no errors in `holographic-card/holographic-card-editor.html`.
