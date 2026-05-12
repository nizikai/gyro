# Journal

## Current State (2026-05-12)
- Main work: [parallax/gyro-parallax-v4.html](parallax/gyro-parallax-v4.html) WebGL core stabilized for mobile output.
- Vertex UV remains direct clip-to-UV mapping; texture orientation kept aligned for image+depth with one global UNPACK Y-flip before uploads.
- Fragment shader updated to edge-aware depth smoothing and edge-damped displacement to reduce silhouette overlap/tearing at large tilt.
- Pivot behavior now uses `relative = (uPivotDepth - depth) * uDepthInfluence` so: behind pivot moves with tilt, in front moves against tilt, pivot stays locked.
- Displacement is hard-capped to prevent runaway warping under extreme slider values.
- Cover-fit UV still computed from image natural size vs canvas pixel size (post-DPR resize).
- Current control defaults in v4: Strength 0.03 (max 0.08), Pivot Depth 0.5, Smoothing 0.06.

## Verification
- VS Code diagnostics: no errors in [parallax/gyro-parallax-v4.html](parallax/gyro-parallax-v4.html).
