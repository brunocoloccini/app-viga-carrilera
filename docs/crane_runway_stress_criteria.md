# Crane runway elastic stress criteria (generic)

## Purpose
This module provides a **generic stress utilization checking layer** for elastic stress results.
It compares computed stress demand values against user-defined allowable stress limits.

It does **not** perform design-code resistance checks.

## Scope split: stress calculation vs. code verification
- Stress calculators (vertical/lateral/biaxial) compute elastic stress demand.
- Stress criteria convert limits to a common stress unit and evaluate utilization/pass-fail.
- Code-specific checks (CIRSOC/AISC/CISC/etc.) are intentionally outside this layer.

## Supported limit types
`StressLimit` supports:
- `absolute`: allowable stress given directly (MPa, ksi, etc., converted internally to MPa).
- `fraction_of_Fy`: allowable = `factor * Fy`.

Examples:
- 165 MPa (absolute)
- 24 ksi (absolute)
- 0.66 Fy
- 0.90 Fy

## Demand sources
`ElasticStressCriteriaChecker` supports:
- vertical bending (`vertical_bending`): uses `max_abs_stress_MPa`
- lateral bending (`lateral_bending`): uses `max_abs_lateral_stress_MPa`
- biaxial elastic (`biaxial_elastic`): uses `max_abs_stress_MPa`

For biaxial checks, the critical point id is preserved.

## Utilization and pass/fail
For each check:
- utilization ratio = `abs(demand_stress_MPa) / allowable_stress_MPa`
- pass if `abs(demand_stress_MPa) <= allowable_stress_MPa`

## Limitations
This layer intentionally excludes:
- CIRSOC-specific provisions
- CISC/AISC-specific provisions
- resistance factors
- ASD/LRFD mapping
- fatigue checks
- lateral-torsional buckling (LTB)
- torsion checks
- local stress effects
