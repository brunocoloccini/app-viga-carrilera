# Crane Runway Demand Summary (V1-032)

## Purpose

`CraneRunwayDemandSummary` provides a compact reporting object that aggregates key crane runway analysis outputs into one structured result.

## Analysis Result vs. Summary Object

- Analysis result objects (moving envelope, deflection envelope, lateral analysis, stress analysis) each represent one analysis domain.
- The demand summary is a higher-level aggregation/reporting layer that references those existing results and exposes key maxima and pass/fail statuses.

V1-032 intentionally does **not** introduce new structural formulas.

## Aggregated Values

The summary can aggregate:

- Vertical moving-envelope maxima (moment and absolute shear).
- Moving deflection envelope maximum.
- Lateral analysis maximum moment.
- Biaxial stress maximum absolute stress.
- Maximum absolute torsional input from `WheelTorsionalLoadGroup`.
- Optional serviceability and stress-utilization check lists.

## Pass/Fail Aggregation

- `serviceability_passed()`:
  - `True` if at least one serviceability result exists and all pass.
  - `False` if any serviceability check fails.
  - `None` if no serviceability checks exist.
- `stress_criteria_passed()` uses the same logic for stress utilization checks.
- `overall_passed()`:
  - `False` if any available check set fails.
  - `True` if at least one check set exists and all available checks pass.
  - `None` if no pass/fail checks exist.

## `to_dict()` Output Scope

`to_dict()` is intentionally limited to JSON-serializable key values:

- IDs and span.
- Key maxima.
- Aggregated pass/fail flags.
- Warnings and metadata.

V1-032 does not fully serialize all nested analysis/result objects.

## Current Limitations

- No normative code checks (no CIRSOC/CISC/AISC checks in this layer).
- No full report formatting/rendering.
- No torsional stress or warping stress computation.
- No fatigue checks.
- No lateral-torsional buckling (LTB) checks.
- No UI layer.
