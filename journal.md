# Journal

## Latest Milestone
- Implemented layered depth compositing in `depth/gyro-parallax copy.html` to reduce double-foreground ghosting from single-image warp.
- Added depth-mask controls and runtime hole-fill sampling to approximate background recovery behind near objects.

## Current Behavior
- App loads source image + depth map, initializes WebGL renderer, and drives tilt from deviceorientation.
- Fragment shader now separates foreground/background contribution using depth threshold + feather and composites them after a background-only weighted sample pass.
- Background pass uses local ring sampling (`fillRadius`) to replace near-depth pixels with nearby far-depth pixels when possible.
- iOS permission prompt remains via PermissionManager.
- UI keeps live sliders and now includes: foreground threshold, foreground feather, background fill radius.

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
- Browser smoke test: page loads, images load, orientation controller starts, new sliders render.

## Open Notes
- Runtime hole-fill is heuristic; best quality still requires an offline clean background plate + explicit foreground cutout.
- Main file parity (`depth/gyro-parallax.html`) is pending if this implementation direction is accepted.
