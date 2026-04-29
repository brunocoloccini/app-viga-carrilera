# Crane runway lateral analysis (V1-028)

This module adds a first generic lateral wheel-load analysis layer for simple-span runway beams and elastic lateral bending stress.

## Scope and purpose

- Analyze wheel lateral forces along beam span `x` from left support to right support.
- Compute lateral reactions, shear, and bending moment from point lateral loads.
- Compute elastic lateral bending stress from weak-axis section moduli:
  - `S_z_left_mm3`
  - `S_z_right_mm3`

## Coordinate and sign convention

- `x=0` at left support; `x=L` at right support.
- Wheel positions are measured from the left support.
- Lateral force uses `WheelLoad.lateral_force_internal_N` only.
- Vertical and longitudinal wheel forces are ignored in this analysis.

## Simple-span formulas

For lateral point loads `H_i` at positions `x_i`:

- `R_right = sum(H_i * x_i) / L`
- `R_left = sum(H_i) - R_right`

At any section `x`:

- `V_lat(x) = R_left - sum(H_i for x_i <= x)`
- `M_lat(x) = R_left * x - sum(H_i * (x - x_i) for x_i <= x)`

Internal units are:

- Length: `mm`
- Force: `N`
- Moment: `Nmm`

## Lateral elastic stress

Stress is computed using weak-axis moduli:

- `sigma_left = M_lat / S_z_left`
- `sigma_right = M_lat / S_z_right` (signed convention may invert side sign internally)

Reported results include:

- signed stress values
- absolute compression/tension magnitudes per side
- maximum absolute lateral stress

## Difference from vertical bending stress

- Vertical bending stress uses `S_y_top_mm3` and `S_y_bottom_mm3`.
- Lateral bending stress uses `S_z_left_mm3` and `S_z_right_mm3`.
- This feature does not combine vertical and lateral stress yet.

## Current limitations

- No biaxial interaction.
- No rail eccentricity.
- No torsion.
- No lateral-torsional buckling.
- No CIRSOC/CISC/AISC code checks.
- No fatigue checks.
