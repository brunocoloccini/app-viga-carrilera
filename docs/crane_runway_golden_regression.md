# Crane Runway Golden Regression (V1-038)

## Purpose
Golden regression tests snapshot expected outputs for the demo crane runway JSON case and detect accidental changes in:
- calculation outputs;
- sign conventions and offsets;
- unit conversions/presentation;
- summary flags and warnings;
- markdown report formatting.

This is a **regression baseline**, not an independent engineering verification.

## Golden Files
- `examples/golden/crane_runway_case_demo_golden_summary.json`
- `examples/golden/crane_runway_case_demo_golden_report.md`

They are generated from:
- `run_crane_runway_case_json("examples/crane_runway_case_demo.json")`

## What the Regression Test Compares
`tests/test_crane_runway_golden_regression.py` checks:

1. Golden files exist.
2. Summary numeric values (with tolerance) for key fields:
   - `span_internal_mm`
   - `max_vertical_moment_Nmm`
   - `max_vertical_shear_abs_N`
   - `max_vertical_deflection_mm`
   - `max_lateral_moment_Nmm`
   - `max_biaxial_stress_MPa`
   - `max_torsional_input_Nmm`
3. Summary identifiers and status flags (exact match):
   - `summary_id`, `section_id`, `load_model_id`
   - `serviceability_passed`, `stress_criteria_passed`, `overall_passed`
4. Warnings list exact match.
5. Markdown report match after deterministic normalization:
   - newline normalization;
   - trailing whitespace trim.
6. Golden metadata fields exist and match expected values:
   - `schema_version`
   - `source_case_path`
   - `metadata.generated_by`

## Tolerances
Numeric comparisons use `math.isclose(..., rel_tol=1e-6, abs_tol=1e-6)`.
Strings/booleans/IDs/flags are exact.

## Intentional Golden Update Workflow
Use:

```bash
PYTHONPATH=src python scripts/update_crane_runway_golden_outputs.py
```

Then run tests:

```bash
pytest -q
```

Only update golden files after intentional calculation/reporting changes are reviewed.

## Validation Scope and Limitations
- Not a design-code verification.
- Not a substitute for independent hand checks.
- Not fatigue verification.
- Not torsional/warping stress validation.
- Not lateral-torsional buckling (LTB) validation.
