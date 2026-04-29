# Crane Runway Matrix HTML Reporting (V1-045)

## Purpose
V1-045 adds a lightweight static HTML index report that summarizes all crane runway scenario matrix cases in one table.

## Relationship to scenario matrix
The matrix report is intended to aggregate the case files in `examples/cases/*.json` and provide a quick status/index view across all scenarios.

## Values shown
Each row includes:
- case identification (`case_id`, optional case path)
- max vertical moment (kN·m)
- max vertical shear (kN)
- max vertical deflection (mm)
- max biaxial stress (MPa)
- max torsional input (kN·m)
- status flags for serviceability, stress criteria, and overall checks
- warnings list

## Status aggregation
Status fields map as:
- `True` -> `PASS`
- `False` -> `FAIL`
- `None` -> `N/A`

## CLI usage
Text mode (existing behavior):

```bash
python scripts/run_crane_runway_case_matrix.py
```

HTML to stdout:

```bash
python scripts/run_crane_runway_case_matrix.py --html
```

HTML to file:

```bash
python scripts/run_crane_runway_case_matrix.py --html --output examples/golden/crane_runway_scenario_matrix.html
```

## Limitations
- Static summary/index only.
- Does not embed per-case detailed reports.
- No PDF/DOCX export.
- No UI.
- No CIRSOC-specific checks.
- No fatigue checks.
- No torsion/warping stress checks.
- No LTB checks.
