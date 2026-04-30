# Command Reference

## Testing

```bash
pytest -q
```

## Validation CLI

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py <case.json>
PYTHONPATH=src python scripts/validate_crane_runway_case.py <case.json> --json
PYTHONPATH=src python scripts/validate_crane_runway_case.py <case.json> --non-strict
```

## Execution CLI

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py <case.json>
PYTHONPATH=src python scripts/run_crane_runway_case.py <case.json> --markdown
PYTHONPATH=src python scripts/run_crane_runway_case.py <case.json> --html
PYTHONPATH=src python scripts/run_crane_runway_case.py <case.json> --summary-json
PYTHONPATH=src python scripts/run_crane_runway_case.py <case.json> --package-output out/demo --overwrite-package
```

## Scenario matrix

```bash
PYTHONPATH=src python scripts/run_crane_runway_case_matrix.py
PYTHONPATH=src python scripts/run_crane_runway_case_matrix.py --html --output out/matrix.html
```

## Golden update

```bash
PYTHONPATH=src python scripts/update_crane_runway_golden_outputs.py
```

## Beta health check

```bash
PYTHONPATH=src python scripts/run_beta_health_check.py
PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest
PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest --quiet
```



## create_crane_runway_case_template.py

- `--list`: list built-in template IDs.
- `--template TEMPLATE_ID --output PATH`: write a JSON case file from a template.
- `--overwrite`: allow replacing an existing file.

Exit codes: `0` success, `1` template/runtime error (including unknown template), `2` CLI argument error.
