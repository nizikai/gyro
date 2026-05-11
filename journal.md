# Journal

## Current State (2026-05-11)
- `parallax/gyro-parallax-v2.html` remains a 3-layer compositor (background + transparent foreground + depth map).
- Fragment shader now uses one shared depth warp for both layers to prevent foreground/background drift.
- Foreground motion now adds a subtle depth-driven lead plus light perspective scaling to mimic iPhone wallpaper behavior.
- Foreground blending now includes depth-assisted alpha weighting for clearer near-subject presence.

## Defaults / Controls
- `displacementScale`: 50
- `smoothingFactor`: 0.06
- `overscan`: 0.02
- `fgScale`: 0.08

## Known Risks
- Visual quality depends on asset alignment: foreground cutout and depth map edges must match.
- Some depth maps may need polarity inversion if near/far motion feels reversed.

## Verification
- No VS Code diagnostics in `parallax/gyro-parallax-v2.html`.