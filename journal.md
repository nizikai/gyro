# Journal

## Latest Milestone
- Converted `parallax/gyro-parallax-v2.html` into a true 3-layer compositor.
- Rendering now uses separate textures for background image, transparent foreground PNG, and depth map.

## Current Behavior
- `ParallaxEffect` now requires `backgroundImageUrl`, `foregroundImageUrl`, and `depthMapUrl`.
- Fragment shader warps background and foreground with different depth-based offsets, then alpha-composites foreground over background.
- Renderer exposes setter APIs for displacement, smoothing, overscan, and foreground scale.
- Slider bindings now call renderer setters instead of mutating internal renderer fields directly.
- iOS permission flow and deviceorientation control remain unchanged.

## Default Asset Names
- `background.png`
- `foreground.png`
- `depth.png`

## Verification
- VS Code diagnostics: no errors in `parallax/gyro-parallax-v2.html`.

## Open Notes
- Motion tuning is controlled by `displacementScale` and `fgScale` in the 3-layer shader.
- `parallax/gyro-parallax.html` remains untouched as the original 2-image version.
