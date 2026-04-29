# Crane runway moving-load envelope (V1-022)

## Purpose

This module computes a moving-load envelope for a simply supported crane runway beam by translating a `CraneWheelGroup` along the span and re-running simple-span analysis at each position.

## Coordinate convention

- Beam axis coordinate is `x` in mm from left support (`x=0`) to right support (`x=span`).
- Wheel positions are measured in the same coordinate system.

## Offset convention

For each envelope position, the wheel group is translated by an offset `offset_x_internal_mm`:

`x_shifted = x_original + offset`

The envelope returns both offset and shifted wheel group for traceability.

## Allowed offset range

Given original wheel positions:

- `x_min_group = min(x_i)`
- `x_max_group = max(x_i)`

Allowed offsets are:

- `offset_min = -x_min_group`
- `offset_max = span - x_max_group`

This guarantees all considered wheels remain within `[0, span]`.

If `(x_max_group - x_min_group) > span`, analysis raises `WheelGroupLongerThanSpanError`.

## Step-size behavior and endpoint inclusion

- Movement is sampled on a regular grid using `step_internal_mm`.
- Step must be positive.
- Endpoints are always included, even when `offset_max` is not an exact multiple of step.
- Envelope values therefore depend on step size in V1-022.

Step and offset limits are stored in envelope metadata.

## Scope in V1-022

- Vertical loads only.
- Lateral and longitudinal wheel forces are ignored by this envelope layer.
- No exact influence-line optimization is implemented; this is grid-based scanning.

## Future steps

- Exact critical-position search (influence-line-driven).
- Shear envelope along span.
- Moment envelope along span.
- Deflection envelope.
- Fatigue stress-range envelope.
- Lateral-load envelope analysis.
