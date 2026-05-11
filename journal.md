# Journal

## Current State (2026-05-11)
- `parallax/gyro-parallax-v2.html` is a 3-layer compositor (background + transparent foreground + depth map).
- Fragment shader now intentionally separates layer motion: far-depth background drift is stronger, foreground drift is damped, and only a reduced shared depth warp is applied to foreground.
- Foreground keeps light depth-driven lead and perspective scale for near-subject dimensionality without dominating global motion.

## Defaults / Controls
- `displacementScale`: 58
- `smoothingFactor`: 0.06
- `overscan`: 0.03
- `fgScale`: 0.06

## Known Risks
- Visual quality depends on asset alignment: foreground alpha edges and depth transitions must match.
- High tilt angles can still clamp UVs near edges; increase overscan if edge smearing appears.
- Some depth maps may need polarity inversion if near/far motion feels reversed.

## Verification
- No VS Code diagnostics in `parallax/gyro-parallax-v2.html`.