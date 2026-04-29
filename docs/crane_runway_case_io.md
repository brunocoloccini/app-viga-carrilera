# Crane runway case JSON I/O (V1-036)

This layer adds JSON case-file orchestration for crane runway calculations.

- Purpose: store a complete crane runway calculation case in JSON and run it through `CraneRunwayCalculationWorkflow`.
- It is input/output and orchestration only.

## Schema overview
- Top-level required fields: `case_id`, `shape_library_path`, `base_shape_id`, `span`, `analysis`, `crane`.
- Quantities use explicit objects: `{ "value": <number>, "unit": "..." }`.

## Section construction
- The base section component is loaded from `shape_library_path` + `base_shape_id`.
- The section can include an optional enabled top cover plate.
- Cover plate placement uses `LineToLineJoin` from plate bottom edge to base top edge.

## Crane and criteria input
- Crane wheels are required and must be non-empty.
- Serviceability limits support `span_over` (mapped to `DeflectionLimit.span_over`).
- Stress limits support `fraction_of_Fy` and `absolute`.

## Rail eccentricity input
- `rail_eccentricity.enabled=false` disables torsional-input generation.
- If enabled, `RailEccentricityModel` is built from explicit quantities.

## Execution functions
- `load_crane_runway_case_json(path)`
- `dump_crane_runway_case_json(data, path)`
- `build_workflow_input_from_case_dict(data)`
- `run_crane_runway_case_dict(data)`
- `run_crane_runway_case_json(path)`

## Example
Run:

```bash
PYTHONPATH=src python examples/run_crane_runway_case_from_json.py
```

## Current limitations
- No UI yet.
- No PDF/DOCX export.
- No CIRSOC-specific checks.
- No fatigue checks.
- No torsional/warping stress checks.
- Sample CIRSOC data must be independently verified before production use.
