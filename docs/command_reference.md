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


## init_crane_runway_project.py

```bash
PYTHONPATH=src python scripts/init_crane_runway_project.py --name <project_name> --template <template_id>
PYTHONPATH=src python scripts/init_crane_runway_project.py --name <project_name> --template <template_id> --validate
PYTHONPATH=src python scripts/init_crane_runway_project.py --name <project_name> --template <template_id> --run
PYTHONPATH=src python scripts/init_crane_runway_project.py --name <project_name> --template <template_id> --root <path>
PYTHONPATH=src python scripts/init_crane_runway_project.py --name <project_name> --template <template_id> --overwrite
```

- `--name`: required project name (letters/numbers/dash/underscore only).
- `--template`: required built-in template id.
- `--root`: optional workspace root (default `projects`).
- `--overwrite`: allow replacing known generated files in existing non-empty project folder.
- `--validate`: validate generated `input_case.json`.
- `--run`: implies validate and writes report package to `outputs/`.

Exit codes: `0` success, `1` user/runtime error (for example unknown template, invalid project name, or non-empty target without `--overwrite`), `2` CLI argument error.

## Editing guide example commands

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/editing_guide/ipn_with_cover_editing_example.json
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/editing_guide/ipn_without_cover_editing_example.json
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/editing_guide/ipn_with_cover_editing_example.json --package-output out/editing_with_cover --overwrite-package
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/editing_guide/ipn_without_cover_editing_example.json --package-output out/editing_without_cover --overwrite-package
```


## serve_crane_runway_ui.py

Start local crane runway browser UI.

```bash
PYTHONPATH=src python scripts/serve_crane_runway_ui.py [--host 127.0.0.1] [--port 8765] [--open]
```

- `PYTHONPATH=src python scripts/check_local_ui_smoke.py --url http://127.0.0.1:8765`


## Local UI launcher

```bash
PYTHONPATH=src python scripts/launch_crane_runway_ui.py
```

Options:

- `--host` (default `127.0.0.1`)
- `--port` (default `8765`)
- `--no-open`
- `--skip-preflight`
- `--check-only`
- `--run-smoke-after-start`
- `--timeout`

## Local UI Project Workflow

Use the Local UI **Project Workspace** panel to create/open/save/run project cases under `projects/`.

- Local UI project workspaces include **Project Run History** actions for timestamped snapshots and run artifact review.
