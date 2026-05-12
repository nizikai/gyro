# Journal

## Current State (2026-05-12)
- Main work: [parallax/gyro-parallax-v4.html](parallax/gyro-parallax-v4.html) WebGL core rewritten (shader + texture pipeline) while keeping existing HTML layout, controls UI, and gyro/mouse input flow.
- Vertex UV uses direct clip-to-UV mapping: `vUv = vec2(aPosition.x * 0.5 + 0.5, aPosition.y * 0.5 + 0.5)`.
- Texture orientation is unified for both image/depth via one global `gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)` before uploads.
- Texture unit mapping is stable: image on unit 0, depth map on unit 1.
- Fragment shader now uses 5-tap depth averaging, pivot-relative displacement clamp, displacement cap, and soft edge fallback with opaque output alpha.
- Cover-fit UV uses image natural dimensions vs canvas pixel dimensions (`canvas.width/height` after DPR resize) and is recalculated on resize.
- Current control defaults in v4: Strength 0.03 (max 0.08), Pivot Depth 0.5, Smoothing 0.06.

## Verification
- VS Code diagnostics: no errors in [parallax/gyro-parallax-v4.html](parallax/gyro-parallax-v4.html).
