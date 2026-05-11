# Journal

## Current State (2026-05-11)
- `parallax/gyro-parallax-v2.html` uses a 4-input compositor (background, transparent foreground, optional foreground mask, depth map).
- Foreground now receives depth-map distortion via a damped shared depth warp term, so both layers respond to depth instead of only background drift.
- Foreground halo cleanup added in fragment shader:
	- contracts mask edge with a 5-tap min filter (center + 4-neighbor erosion)
	- tightens alpha/mask matte thresholds
	- applies white-edge decontamination on low-alpha edge pixels
- Result target: remove visible white stroke around the foreground subject while preserving core detail.

## Defaults / Controls
- displacementScale: 62
- smoothingFactor: 0.06
- overscan: 0.04
- fgScale: 0.05
- fgZoom: 0.015
- foregroundMaskUrl: mask.png (optional; falls back to PNG alpha)

## Known Risks
- Very soft hair/fur edges may need slight matte threshold relaxation on specific assets.
- If foreground and background resolutions diverge heavily, mask erosion step size may need a dedicated foreground-resolution uniform.
- Extreme tilt can still reveal UV clamp/stretch at frame edges; overscan adjustment remains the first mitigation.

## Verification
- No VS Code diagnostics in `parallax/gyro-parallax-v2.html` after halo-fix patch.