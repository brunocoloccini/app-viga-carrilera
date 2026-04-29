# Crane runway simple-span analysis (V1-021)

## Purpose
This module introduces the first structural analysis layer for crane runway beams: a deterministic simple-span beam solver for a fixed wheel position set.

## Coordinate convention
- Beam axis coordinate is `x` measured from the left support.
- Valid domain is `0 <= x <= span`.

## Internal units
- Length: `mm`
- Force: `N`
- Moment: `Nmm`

## Point-load beam formulas
For wheel forces `P_i` at positions `x_i` on span `L`:

- `R_right = sum(P_i * x_i) / L`
- `R_left = sum(P_i) - R_right`

At a section `x`:

- `V(x) = R_left - sum(P_i for x_i <= x)`
- `M(x) = R_left * x - sum(P_i * (x - x_i) for x_i <= x)`

## Scope for V1-021
- Vertical wheel loads only.
- Lateral and longitudinal components are intentionally ignored in this phase.
- Deterministic sampling includes supports, wheel positions, and epsilon offsets before/after wheel points.

## Out of scope for V1-021
- Moving-load envelopes.
- Influence lines.
- Fatigue checks.
- CIRSOC/AISC/CISC checks.
- Deflection/serviceability checks.
- Lateral-torsional buckling checks.

## Next steps
- Moving load envelope.
- Lateral bending.
- Biaxial stress combination.
- Deflection.
- Fatigue stress-range workflows.
