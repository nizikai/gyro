# Journal

## Latest Milestone
- Simplified to core behavior only: image load + gyro parallax.
- Removed idle-return system, mouse fallback logic, reduced-motion flow, and in-file property-test harness.

## Current Behavior
- App loads source image + depth map, initializes WebGL renderer, and drives tilt from deviceorientation.
- iOS permission prompt remains via PermissionManager.
- UI keeps live sliders (displacement, smoothing, overscan, foreground scale) and debug log overlay.

## Key Tunables
- displacementScale (slider)
- smoothingFactor (slider)
- overscan (slider)
- fgScale (slider)

## Verification
- VS Code diagnostics: no errors in depth/gyro-parallax.html.

## Open Notes
- If desktop support is needed again, reintroduce a mouse controller as optional fallback.
