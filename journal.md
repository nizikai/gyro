# Journal

## Latest Milestone
- Implemented option-3 style split-layer pipeline in `depth/gyro-parallax copy.html`.
- App now preprocesses `input.jpeg` + `depth.png` into two runtime textures: clean background plate and RGBA foreground cutout.

## Current Behavior
- App loads source image + depth map, initializes WebGL renderer, and drives tilt from deviceorientation.
- Preprocess step builds layers using depth threshold/feather mask + iterative inpaint fill for occluded background regions.
- Fragment shader composites `uBackgroundImage` + `uForegroundImage` textures directly, so near object is no longer sampled from the same base image twice.
- Threshold, feather, and fill-radius slider changes trigger debounced layer rebuild and texture refresh in-place.
- iOS permission prompt remains via PermissionManager.
- UI sliders: displacement, smoothing, overscan, foreground scale, foreground threshold, foreground feather, background fill radius.

## Key Tunables
- displacementScale
- smoothingFactor
- overscan
- fgScale
- fgThreshold
- fgFeather
- fillRadius

## Verification
- VS Code diagnostics: no errors in `depth/gyro-parallax copy.html`.
- Browser smoke test: page loads, images load, orientation controller starts, layer rebuild runs at init.
- Runtime slider test: changing foreground threshold updates value and triggers layer texture rebuild.

## Open Notes
- Current clean background is generated heuristically at runtime; difficult scenes may still benefit from an offline artist-made background plate.
- Main file parity (`depth/gyro-parallax.html`) is pending if this implementation direction is accepted.
