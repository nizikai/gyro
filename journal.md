# Journal

## Current State (2026-05-12)
- Main work: [parallax/gyro-parallax-v4.html](parallax/gyro-parallax-v4.html) updated for calibration and stability under extreme tilt.
- Shader now uses 9-tap weighted depth blur with adjustable radius (`uDepthBlur`) to reduce hard-edge tearing.
- Added depth inversion toggle (`uDepthInvert`) for opposite depth encodings.
- Added depth debug overlay toggle (`uShowDepth`) rendering a 50% grayscale depth mix over final image.
- Added depth-aware rotation in degrees (`uRotateDeg`) so motion is not translation-only.
- Pivot behavior remains physically aligned: behind pivot with tilt, in front against tilt, pivot locked.
- Displacement and relative depth are clamped to limit overlap artifacts.
- Current control defaults in v4: Strength 0.025 (max 0.06), Pivot Depth 0.75, Smoothing 0.06, Depth Influence 1.2 (max 2.0), Depth Blur 0.008.

## Verification
- VS Code diagnostics: no errors in [parallax/gyro-parallax-v4.html](parallax/gyro-parallax-v4.html).
