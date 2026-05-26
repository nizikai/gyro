# Journal

## Current State (2026-05-26)
- Active work: `parallax/gyro-parallax-v7.html`.
- v7 renders the parallax scene as split Three.js geometry instead of two continuous planes:
  - `foreground.png` alpha is sampled into a client-side mask.
  - Full background underlay renders first in normal mode so foreground lift/parallax cannot reveal black holes.
  - Normal mode uses a full alpha-discard foreground visual mesh for smoother silhouette rendering.
  - Foreground mesh includes only masked cells.
  - Foreground depth relief has an `FG Shape` control that blurs/remaps depth and tapers relief near the alpha silhouette.
  - Background mesh excludes the foreground mask plus the configured gap radius.
  - Background-fill mesh paints the removed gap ring with `background.png`.
  - Rim mesh overlays the ring with additive blue/warm edge light.
- Controls now include `FG Shape`, `Gap`, and `Rim Light`; wireframe mode hides fill/rim helpers and shows the shaped split topology.
- Mobile CSS keeps the expanded controls panel inside narrow viewports.
- `gyro-parallax-v6.html` is intentionally untouched.

## Verification
- Module script parse check: passed.
- Local server: `python3 -m http.server 5503` from `parallax/`.
- Headless Chrome + SwiftShader WebGL screenshots:
  - Desktop normal render shows object/background separation with background-filled gap and rim light.
  - Repro state `FG Depth=0`, `FG Lift=0.6`, `Rim Light=0` shows the exposed cutout covered by `background.png`.
  - Repro state `FG Depth=0.8`, `FG Lift=0.6`, `FG Shape=0.68`, `Rim Light=0` shows softer foreground shape and less harsh silhouette teeth.
  - Wireframe render shows no continuous wire lines crossing the cutout.
  - Mobile-width render shows scene and controls fit onscreen.
- Console inspection showed no app/shader exceptions; only expected headless SwiftShader/readback warnings and favicon 404.
