# Editing Guide Examples

These files are editable starting points for project cases.

- They are not design recommendations.
- They are for workflow practice and integration validation.

## Validate an example

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/editing_guide/ipn_with_cover_editing_example.json
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/editing_guide/ipn_without_cover_editing_example.json
```

## Run an example

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/editing_guide/ipn_with_cover_editing_example.json --package-output out/editing_with_cover --overwrite-package
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/editing_guide/ipn_without_cover_editing_example.json --package-output out/editing_without_cover --overwrite-package
```
