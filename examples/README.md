# Examples

This directory contains runnable examples and regression fixtures for crane runway workflows.

## Important files

- `crane_runway_case_demo.json`: baseline JSON case for validation/execution scripts.
- `run_crane_runway_case_from_json.py`: script-style JSON execution example.
- `end_to_end_crane_runway_demo.py`: end-to-end programmatic workflow demo.
- `cases/README.md`: scenario matrix case set overview.
- `golden/crane_runway_case_demo_golden_summary.json`: golden summary baseline.
- `golden/crane_runway_case_demo_golden_report.md`: golden markdown baseline.
- `golden/crane_runway_case_demo_golden_report.html`: golden HTML baseline.

## Scenario matrix

Scenario matrix JSON files are under `examples/cases/` and are used by matrix tests and CLI validation to cover expected pass/fail variants.

## Golden outputs

Golden regression outputs are under `examples/golden/` and are used to verify deterministic report/summary behavior.

## Warning

All examples are demo/regression cases only, not design recommendations, and require independent engineering verification.
