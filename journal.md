# Journal

## Current State (2026-05-12)
- [parallax/gyro-parallax-v2.1.html](parallax/gyro-parallax-v2.1.html) was rewritten as a raw WebGL two-pass parallax renderer.
- Pass 1 (background): per-pixel UV displacement in fragment shader using depth map + tilt.
- Pass 2 (foreground): fixed max displacement (depth=1 behavior) plus a subtle opposite-tilt shadow.

## Input + Motion
- Gyroscope input uses DeviceOrientationEvent: gamma for X tilt, beta for Y tilt.
- beta/gamma are clamped to plus/minus 45 degrees and normalized to minus 1.0 to plus 1.0.
- Tilt smoothing uses frame lerp factor 0.08.
- Mouse and touch fallback are active when gyroscope is unavailable, denied, or not producing signal.

## Rendering + Scaling
- Fullscreen WebGL canvas with DPR-aware resize.
- Base sampling uses zoomScale 1.12 to avoid edge exposure under displacement.
- Main displacement strength is 0.048.
- Foreground displacement strength is 0.06.

## UX + Runtime
- Added motion status text and error overlay.
- Added permission prompt UI for mobile contexts where requestPermission is required.

## Verification
- VS Code diagnostics: no errors in [parallax/gyro-parallax-v2.1.html](parallax/gyro-parallax-v2.1.html).
- Browser smoke check: page loads and reports ready state.
