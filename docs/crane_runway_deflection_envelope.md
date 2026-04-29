# Crane runway moving-load deflection envelope (V1-025)

## Purpose
This module computes the **vertical deflection envelope** for a simple-span crane runway beam under a moving wheel group.

It reports:
- maximum downward deflection over all analyzed load positions,
- the beam x-station where that maximum occurs,
- the moving-load offset that produces that critical response,
- and station-by-station max/min deflection envelope values.

## Fixed-position vs moving-load deflection
- Fixed-position deflection (`SimpleSpanRunwayBeamDeflectionAnalyzer`) evaluates one static wheel configuration.
- Moving-load deflection envelope (`SimpleSpanMovingDeflectionEnvelopeAnalyzer`) shifts the same wheel group through all allowed offsets and aggregates extremes.

## Coordinate/station convention
- Beam axis `x` is measured along span from left support.
- Stations are in internal mm.
- Station list is either explicit (`stations=[...]`) or generated from `station_step`.

## Moving offset convention
Given original wheel positions:
- `x_min_group = min(wheel_x)`
- `x_max_group = max(wheel_x)`

Allowed offsets are:
- `offset_min = -x_min_group`
- `offset_max = span - x_max_group`

So the translated wheel group remains within `[0, span]`.

## Step behavior and endpoint inclusion
- Movement is grid-based using `movement_step`.
- Station sampling is grid-based using `station_step` (or explicit stations).
- Endpoints are always included:
  - final moving offset includes `offset_max`,
  - final station includes `span`,
  even when step does not divide interval exactly.

## Sign convention
- Positive vertical wheel load is downward.
- Positive deflection is downward.
- With vertical downward loads only, expected deflections are nonnegative.

## Scope in V1-025
Included:
- Vertical deflection envelope for moving wheel groups.

Not included yet:
- serviceability limit checks,
- CIRSOC/CISC/AISC limit checks,
- exact optimization of critical position (current method is step/grid scan),
- lateral deflection,
- torsional effects,
- combined vertical/lateral serviceability,
- report generation.

## Future steps
- Add serviceability criteria workflows.
- Add exact/local optimization for critical deflection position.
- Add lateral moving-load deflection envelope.
- Add combined vertical+lateral serviceability checks.
- Add structured report output.
