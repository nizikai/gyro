# Journal

## Latest Milestone
- Stabilized gyro idle-return behavior in depth/gyro-parallax.html.
- Fixed renderer displacement initialization bug that could produce a gray/blank frame on first render.

## Current Behavior
- Renderer now initializes and validates active displacement scale before shader upload.
- Idle return no longer fights incoming micro gyro jitter.
- Returning to center now snaps state cleanly, so next tilt starts from centered state.
- UI slider updates now use renderer methods and explicit redraw requests.

## Key Tunables
- IDLE_DELAY: 1000 ms
- IDLE_THRESHOLD: 0.01
- WAKE_THRESHOLD: 0.03
- RETURN_SCALE: 1
- RETURN_DURATION: 900 ms

## Verification
- VS Code diagnostics reports no errors in depth/gyro-parallax.html.

## Open Notes
- Runtime feel on physical devices should be validated for threshold tuning per hardware sensor noise.
