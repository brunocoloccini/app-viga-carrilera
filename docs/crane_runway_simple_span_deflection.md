# Crane Runway Simple-Span Deflection (V1-024)

## Purpose
This module computes fixed-position elastic vertical deflection for a simply supported crane runway beam under wheel loads.

## Coordinates and Sign Convention
- Coordinate `x` is measured from the left support to the right support.
- Positive wheel vertical load is downward.
- Positive deflection `v(x)` is downward.

## Internal Units
- Length: `mm`
- Force: `N`
- Modulus: `MPa` (`N/mm2`)
- Inertia: `mm4`
- Deflection: `mm`

## Point-Load Deflection Formula
For a point load `P` at `a` from the left support on span `L` (`b = L - a`):

- For `x <= a`:

`v(x) = P * b * x / (6 * L * E * I) * (L^2 - b^2 - x^2)`

- For `x >= a`:

`v(x) = P * a * (L - x) / (6 * L * E * I) * (L^2 - a^2 - (L - x)^2)`

Total deflection uses superposition across all wheels.

## V1-024 Scope
- Vertical loads only.
- Fixed wheel positions only.
- No moving-load deflection envelope yet.
- No serviceability limit checks yet.

## Future Steps
- Moving-load deflection envelope.
- Serviceability criteria.
- Lateral deflection.
- Combined vertical/lateral checks.
