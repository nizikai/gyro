# Journal

## Latest Milestone
- Reverted heavy split-layer preprocessing path in `depth/gyro-parallax copy.html` due overlap persistence and performance cost.
- Implemented lightweight depth-guided background shrink distortion in shader and removed foreground-scale logic entirely.

## Current Behavior
- App loads source image + depth map, initializes WebGL renderer, and drives tilt from deviceorientation.
- Rendering is single-pass again with one source texture + one depth map.
- Shader computes near-mask from depth threshold/feather and applies controlled background UV shrink/distortion around near-depth influence before compositing.
- Foreground scale has been removed from shader, controls, and renderer API.
- Controls now: displacement, smoothing, overscan, background shrink, foreground threshold, foreground feather.
- iOS permission prompt remains via PermissionManager.

## Key Tunables
- displacementScale
- smoothingFactor
- overscan
- bgShrink
- fgThreshold
- fgFeather

## Verification
- VS Code diagnostics: no errors in `depth/gyro-parallax copy.html`.
- Browser smoke test: page loads, images load, orientation controller starts.
- Runtime slider test: background shrink slider updates and applies live.

## Open Notes
- This is a lower-cost heuristic intended to reduce overlap artifact without expensive preprocessing.
- Main file parity (`depth/gyro-parallax.html`) is pending if this implementation direction is accepted.
