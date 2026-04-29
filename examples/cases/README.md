# Crane Runway Scenario Matrix Cases

This folder contains a compact scenario matrix of crane runway JSON input cases used for software validation and demo regression coverage.

## Purpose

The matrix extends single-case regression by covering common variants of the same baseline input so we can verify deterministic behavior for:

- cover plate enabled/disabled,
- rail eccentricity enabled/disabled,
- intentional serviceability failure,
- intentional stress-criteria failure.

## Included cases

- `crane_runway_case_with_cover_and_eccentricity.json`
  - Baseline case with cover plate and rail eccentricity enabled.
- `crane_runway_case_without_cover_plate.json`
  - Same baseline, but cover plate disabled.
- `crane_runway_case_without_rail_eccentricity.json`
  - Same baseline, but rail eccentricity disabled (torsional input omitted).
- `crane_runway_case_deflection_fail.json`
  - Same baseline, but with intentionally strict deflection limit to trigger serviceability `FAIL`.
- `crane_runway_case_stress_fail.json`
  - Same baseline, but with intentionally strict stress limit to trigger stress criteria `FAIL`.

## Important notes

- All data here is for software validation/demo purposes only.
- CIRSOC sample profile data is manually curated and requires independent verification.
- These files are **not** design recommendations and are not a substitute for project-specific engineering checks.
