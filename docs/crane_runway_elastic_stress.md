# Crane Runway Elastic Vertical Bending Stress (V1-027)

## Purpose
This module computes **elastic normal stress** in crane runway beams from vertical bending moments and gross section properties.

It is intentionally a **calculation layer only**: it does not perform design-code checks or resistance verification.

## Governing relationship
For elastic bending about the local y-axis:

- Top-fiber compression magnitude: `sigma_top_compression = |M| / S_y_top`
- Bottom-fiber tension magnitude: `sigma_bottom_tension = |M| / S_y_bottom`

Where:
- `M` is vertical bending moment,
- `S_y_top` and `S_y_bottom` are gross elastic section moduli.

## Internal units
- Moment: `N·mm`
- Section modulus: `mm^3`
- Stress: `MPa = N/mm^2`

## Sign convention
The analyzer follows the common simple-span convention:
- **Positive sagging moment**:
  - top fiber is in compression,
  - bottom fiber is in tension.

Signed stresses preserve this:
- `sigma_top_MPa` is typically negative for positive sagging moments,
- `sigma_bottom_MPa` is typically positive for positive sagging moments.

Stress magnitudes are also reported separately as positive values:
- `sigma_top_compression_MPa`,
- `sigma_bottom_tension_MPa`.

## Scope boundaries
Included in V1-027:
- vertical bending stress from gross elastic properties,
- stress from fixed-position max moment,
- stress from moving-load max-moment envelopes,
- station-based stress envelopes from moment envelope curves.

Explicitly excluded in V1-027:
- lateral bending,
- biaxial stress interaction,
- torsion,
- fatigue stress range checks,
- CIRSOC/CISC/AISC resistance checks,
- allowable stress checks,
- lateral torsional buckling (LTB) checks.
