# Journal

## Current State (2026-05-11)
- `parallax/gyro-parallax-v2.html` is a 4-input compositor pipeline (background + transparent foreground + optional foreground mask + depth map).
- Fragment shader now increases background tilt response significantly, adds subtle background perspective warp, and keeps foreground drift damped for stronger separation.
- Foreground rendering now supports a dedicated black/white mask matte to reduce transparent silhouette overlap artifacts.
- Foreground has a dedicated zoom control (`fgZoom`) with default 0.015 (~1.5%) for a slight closer look.

## Defaults / Controls
- `displacementScale`: 62
- `smoothingFactor`: 0.06
- `overscan`: 0.04
- `fgScale`: 0.05
- `fgZoom`: 0.015
- `foregroundMaskUrl`: `foreground-mask.png` (optional; falls back to PNG alpha)

## Known Risks
- Visual quality still depends on alignment between foreground cutout, depth map, and optional mask.
- If the mask has hard edges, very fine hair/soft edges may need threshold tuning in shader matte smoothstep.
- High tilt angles can still clamp UVs near edges; increase overscan if edge smearing appears.
- Some depth maps may need polarity inversion if near/far motion feels reversed.

## Verification
- No VS Code diagnostics in `parallax/gyro-parallax-v2.html`.