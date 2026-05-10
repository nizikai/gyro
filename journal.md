# Journal

## Latest Milestone
- Implemented deterministic idle-return timing: 1s inactivity detection + 1s smooth return animation.

## Current Behavior
- Renderer supports explicit tilt animations via animateTiltTo(), separate from smoothing lerp.
- After 1000 ms of no significant gyro movement, effect animates tilt to center over 1000 ms.
- Idle-return can be interrupted by meaningful new tilt (wake threshold), and input cancels return animation cleanly.
- Displacement still eases during idle return and restores when movement resumes.

## Key Tunables
- IDLE_DELAY: 1000 ms
- IDLE_THRESHOLD: 0.01
- WAKE_THRESHOLD: 0.03
- RETURN_DURATION: 1000 ms
- RETURN_SCALE: 1

## Verification
- VS Code diagnostics: no errors in depth/gyro-parallax.html.

## Open Notes
- Validate on physical devices and tune IDLE_THRESHOLD/WAKE_THRESHOLD per sensor noise profile.
