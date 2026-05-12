/**
 * Bug Condition Exploration Property-Based Test
 *
 * Property 1: Bug Condition — Sign-Locked Displacement and Flat-Translate Foreground
 *
 * This test encodes the Expected Behavior from the design (Property 1: pivoted,
 * depth-aware displacement for both BG and FG). It is expected to FAIL on the
 * unfixed `parallax/gyro-parallax-v4.html` — failure confirms the bug exists.
 *
 * Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';

// ─── Extract of the UNFIXED shader displacement math ───
// Mirrors FRAG_SRC in gyro-parallax-v4.html:
//   depthInfluence = 1.0 - depth
//   displacement = -uTilt * uStrength * depthInfluence
//
// This is the CURRENT (buggy) formula. It does NOT use a focus-depth pivot.
function unfixedDisplacement(depth, tilt, strength) {
  const depthInfluence = 1.0 - depth;
  return {
    x: -tilt.x * strength * depthInfluence,
    y: -tilt.y * strength * depthInfluence,
  };
}

// ─── Extract of the UNFIXED foreground displacement ───
// Mirrors loop() in gyro-parallax-v4.html:
//   fg.style.transform = translate(current.x * -fgStrength, current.y * -fgStrength)
//
// Every FG pixel gets the same displacement vector regardless of depth.
function unfixedFgDisplacement(tilt, fgStrength) {
  return {
    x: tilt.x * -fgStrength,
    y: tilt.y * -fgStrength,
  };
}

// ─── Helper: sign function matching GLSL sign() ───
function sign(v) {
  if (v > 0) return 1;
  if (v < 0) return -1;
  return 0;
}

// ─── Bug condition check from design ───
// isBugCondition: length(tilt) > 0.0 AND (fgUsesFlatTranslate OR bgDisplacementSignFixed)
// On unfixed code, both sub-conditions are always true when tilt is non-zero.
function isBugCondition(tilt) {
  return Math.sqrt(tilt.x * tilt.x + tilt.y * tilt.y) > 0.0;
}

describe('Bug Condition Exploration - Property 1', () => {
  /**
   * Sign-flip assertion:
   * For arbitrary non-zero tilt, arbitrary focusDepth ∈ [0, 1], and any d1 < focusDepth < d2,
   * sign(displacement(d1).x) != sign(displacement(d2).x) and same for .y.
   *
   * FAILS on unfixed code because (1.0 - depth) is always ≥ 0 so the sign is constant.
   *
   * **Validates: Requirements 1.2**
   */
  it('Sign-flip: displacement should have opposite signs across the focus depth pivot', () => {
    // Scoped concrete case first
    const tilt = { x: 0.5, y: 0.0 };
    const focusDepth = 0.5;
    const d1 = 0.1; // behind focus (far)
    const d2 = 0.9; // in front of focus (near)
    const strength = 0.03;

    const disp1 = unfixedDisplacement(d1, tilt, strength);
    const disp2 = unfixedDisplacement(d2, tilt, strength);

    // The post-fix expected behavior: sign should flip across the pivot
    // On unfixed code, both displacements point in the same direction
    expect(sign(disp1.x)).not.toBe(sign(disp2.x));
  });

  it('Sign-flip property (PBT): displacement sign must flip across focus depth for any non-zero tilt', () => {
    fc.assert(
      fc.property(
        // Generator: non-zero tilt, focusDepth in (0,1), d1 < focusDepth < d2
        fc.record({
          tiltX: fc.oneof(
            fc.double({ min: 0.01, max: 1.0, noNaN: true }),
            fc.double({ min: -1.0, max: -0.01, noNaN: true })
          ),
          tiltY: fc.double({ min: -1.0, max: 1.0, noNaN: true }),
          focusDepth: fc.double({ min: 0.1, max: 0.9, noNaN: true }),
          strength: fc.double({ min: 0.01, max: 0.08, noNaN: true }),
        }).chain((params) =>
          fc.record({
            ...Object.fromEntries(Object.entries(params).map(([k, v]) => [k, fc.constant(v)])),
            d1: fc.double({ min: 0.0, max: params.focusDepth - 0.01, noNaN: true }),
            d2: fc.double({ min: params.focusDepth + 0.01, max: 1.0, noNaN: true }),
          })
        ),
        (params) => {
          const tilt = { x: params.tiltX, y: params.tiltY };
          const disp1 = unfixedDisplacement(params.d1, tilt, params.strength);
          const disp2 = unfixedDisplacement(params.d2, tilt, params.strength);

          // Post-fix expected behavior: sign must flip for the x component
          // (tiltX is guaranteed non-zero by generator)
          expect(sign(disp1.x)).not.toBe(sign(disp2.x));
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Locked-pivot assertion:
   * For any tilt and any focusDepth, displacement(focusDepth, tilt) == (0, 0).
   *
   * FAILS on unfixed code because the formula is zero only at d = 1.0,
   * not at an arbitrary focus depth.
   *
   * **Validates: Requirements 1.3, 2.3**
   */
  it('Locked-pivot: displacement at focus depth should be zero', () => {
    // Scoped concrete case
    const tilt = { x: 0.5, y: 0.0 };
    const focusDepth = 0.5;
    const strength = 0.03;

    const disp = unfixedDisplacement(focusDepth, tilt, strength);

    // Post-fix expected behavior: displacement at focusDepth should be (0, 0)
    // On unfixed code: -0.5 * 0.03 * (1 - 0.5) = -0.0075, NOT zero
    expect(disp.x).toBeCloseTo(0, 5);
    expect(disp.y).toBeCloseTo(0, 5);
  });

  it('Locked-pivot property (PBT): displacement at focus depth must be zero for any tilt', () => {
    fc.assert(
      fc.property(
        fc.record({
          tiltX: fc.double({ min: -1.0, max: 1.0, noNaN: true }),
          tiltY: fc.double({ min: -1.0, max: 1.0, noNaN: true }),
          focusDepth: fc.double({ min: 0.0, max: 1.0, noNaN: true }),
          strength: fc.double({ min: 0.01, max: 0.08, noNaN: true }),
        }),
        (params) => {
          const tilt = { x: params.tiltX, y: params.tiltY };
          const disp = unfixedDisplacement(params.focusDepth, tilt, params.strength);

          // Post-fix expected behavior: zero displacement at the pivot
          expect(disp.x).toBeCloseTo(0, 5);
          expect(disp.y).toBeCloseTo(0, 5);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * FG depth-awareness assertion:
   * Given an FG depth source with variance > 0 and any non-zero tilt,
   * the set of per-pixel displacement vectors across FG pixels contains
   * more than one distinct value.
   *
   * FAILS on unfixed code because fg.style.transform = translate(current.x * -fgStrength,
   * current.y * -fgStrength) moves every FG pixel by the same vector.
   *
   * **Validates: Requirements 1.1, 2.1**
   */
  it('FG depth-awareness: foreground pixels at different depths should have different displacements', () => {
    // Scoped concrete case
    const tilt = { x: 0.3, y: 0.2 };
    const fgStrength = 8;

    // Simulate FG depth source with variance: two pixels at different depths
    const fgDepths = [0.2, 0.4, 0.6, 0.8];

    // On unfixed code, every FG pixel gets the same displacement
    const fgDisplacements = fgDepths.map(() => unfixedFgDisplacement(tilt, fgStrength));

    // Post-fix expected behavior: different depths → different displacements
    // Check that there's more than one distinct displacement vector
    const uniqueDisplacements = new Set(
      fgDisplacements.map((d) => `${d.x.toFixed(10)},${d.y.toFixed(10)}`)
    );

    expect(uniqueDisplacements.size).toBeGreaterThan(1);
  });

  it('FG depth-awareness property (PBT): FG pixels with different depths must have different displacements', () => {
    fc.assert(
      fc.property(
        fc.record({
          tiltX: fc.oneof(
            fc.double({ min: 0.05, max: 1.0, noNaN: true }),
            fc.double({ min: -1.0, max: -0.05, noNaN: true })
          ),
          tiltY: fc.double({ min: -1.0, max: 1.0, noNaN: true }),
          fgStrength: fc.double({ min: 1, max: 25, noNaN: true }),
          // Generate at least 2 distinct FG depth values with variance > 0
          fgDepth1: fc.double({ min: 0.0, max: 0.4, noNaN: true }),
          fgDepth2: fc.double({ min: 0.6, max: 1.0, noNaN: true }),
        }),
        (params) => {
          const tilt = { x: params.tiltX, y: params.tiltY };

          // On unfixed code, the FG displacement is the same for all pixels
          const disp1 = unfixedFgDisplacement(tilt, params.fgStrength);
          const disp2 = unfixedFgDisplacement(tilt, params.fgStrength);

          // Post-fix expected behavior: different depths → different displacements
          // This checks that the displacement vectors are NOT all the same
          const areIdentical =
            Math.abs(disp1.x - disp2.x) < 1e-10 && Math.abs(disp1.y - disp2.y) < 1e-10;

          expect(areIdentical).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });
});
