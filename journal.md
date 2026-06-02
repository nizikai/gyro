# Journal

## Current State (2026-05-31)
- `gold/gold-diagonal.html` is a standalone black/gold tape-resist artwork page, isolated from shared/parallax runtime code.
- The page uses raw WebGL for static diagonal gold-line geometry and metallic lighting; CSS only adds a subtle masked sheen assist.
- Gold line geometry stays static. Pointer movement now changes reflected light visibly:
  - Shader includes a pointer-driven `reflectionSweep` that brightens the gold pixels themselves.
  - CSS overlay is reduced so the hover reads as material reflection, not a flat translucent band.
  - Pointer handling uses `pointerover` + `pointermove` on the artwork container; pointer leave/out/cancel resets to calm lighting.
- `<link rel="icon" href="data:,">` prevents browser `/favicon.ico` 404 noise.

## Verification
- JS syntax check passed via extracted `<script>` and `new Function(...)`.
- Local HTTP checks returned only `GET /gold/gold-diagonal.html` `200`; no favicon 404.
- Headless Chrome screenshots captured for idle and active hover states.
- Chrome DevTools actual mouse input dispatch confirmed hover activation from `--sheen-opacity: 0` to `0.14`, with a visible reflection band in the active render.
