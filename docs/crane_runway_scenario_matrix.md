# Crane Runway Scenario Matrix Regression

## Purpose

This scenario matrix adds multi-case regression coverage for crane runway JSON inputs by validating several common variants derived from the same baseline case.

It is focused on software behavior stability and deterministic pass/fail outcomes, not on adding new structural mechanics.

## Cases included

- `with_cover_and_eccentricity`
  - Baseline complete case with cover plate enabled and rail eccentricity enabled.
- `without_cover_plate`
  - Verifies base library shape workflow runs without cover plate assembly.
- `without_rail_eccentricity`
  - Verifies torsional input path is optional and summary/report handle missing torsion as `N/A`.
- `deflection_fail`
  - Uses intentionally strict absolute deflection limit to exercise serviceability failure handling.
- `stress_fail`
  - Uses intentionally strict absolute stress limit to exercise stress-criteria failure handling.

## What this validates

- Strict schema validation (`schema_version: "1.0"`) for all matrix files.
- End-to-end JSON case execution for each scenario.
- Core demand summary signals remain present and positive where expected.
- Deterministic boolean statuses per case:
  - `serviceability_passed`
  - `stress_criteria_passed`
  - `overall_passed`
  - torsional input present/absent
- Report generation includes expected summary headers and explicit `FAIL` text for intentional failure cases.

## Relation to golden regression

This matrix complements (does not replace) the single-case golden baseline introduced in V1-038:

- V1-038: exact numeric/report snapshot for one demo case.
- V1-039: behavior matrix coverage across multiple scenario variants.

## Limitations

- Not an independent engineering validation package.
- Not a design-code compliance implementation.
- CIRSOC sample profile data remains manually curated and must be independently verified for real projects.
- No fatigue checks.
- No torsional/warping stress checks.
- No lateral-torsional buckling (LTB) checks.
