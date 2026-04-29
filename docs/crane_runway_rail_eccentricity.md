# Crane runway rail eccentricity torsional input (V1-031)

## Purpose
This module converts wheel forces plus geometric eccentricities into **signed torsional input moments** along the runway beam.

This is an input-demand model only. It does **not** compute torsional or warping stresses.

## Scope boundary
Included in V1-031:
- Torsional input per wheel and wheel group.
- Vertical eccentricity and lateral load-height contributions.
- Unit-aware eccentricity/height inputs converted to internal mm.

Not included in V1-031:
- Torsional stress calculation.
- Warping stress.
- J/Cw property derivation workflows.
- Rail attachment design.
- CIRSOC/CISC/AISC checks.
- Fatigue checks.
- Lateral-torsional buckling checks.

## Coordinate convention
- `x`: runway beam longitudinal axis.
- `y`: transverse horizontal axis.
- `z`: vertical axis.

## Sign convention
Torsional input moment is signed about the beam longitudinal `x` axis.

For V1-031:

`T = P * e_y + H * h_z`

Where:
- `P`: vertical wheel force (positive downward).
- `e_y`: signed transverse eccentricity from reference axis.
- `H`: signed lateral force.
- `h_z`: signed vertical height from reference point.
- `T`: resulting signed torsional input moment in `Nmm`.

## Typical eccentricity sources
Vertical eccentricity examples:
- Rail centerline offset from beam web centerline.
- Vertical force resultants not passing through the section reference/shear-center axis.

Lateral height examples:
- Lateral wheel force introduced above/below the reference point.
- Rail head elevation offset producing lateral-force torsion couple.
