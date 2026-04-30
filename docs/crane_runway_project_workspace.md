# Crane Runway Project Workspace

This workspace initializer helps users create organized local project folders for crane runway JSON cases.

## Purpose

- Keep each project case, notes, and output artifacts together.
- Start from built-in templates and use existing validation/execution tooling.
- Support user/developer workflow only (no UI, no database).

## Folder Structure

By default the initializer creates:

```text
projects/<project_name>/
├── input_case.json
├── README.md
└── outputs/
```

## Create a Project

```bash
PYTHONPATH=src python scripts/init_crane_runway_project.py --name mi_viga --template ipn-with-cover
```

## Validate a Project Case

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py projects/mi_viga/input_case.json
```

## Run and Generate Reports

Generate HTML:

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py projects/mi_viga/input_case.json --html --output projects/mi_viga/outputs/report.html
```

Generate package:

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py projects/mi_viga/input_case.json --package-output projects/mi_viga/outputs --overwrite-package
```

## Options

- `--validate`: validates `input_case.json` after creation.
- `--run`: validates and runs the case, then writes a report package to `outputs/`.
- `--root PATH`: choose a different root folder for project directories (default is `projects`).
- `--overwrite`: allows overwriting known generated files in an existing non-empty project folder.

## Limitations

- No UI.
- No database/project registry.
- No official CIRSOC/CISC/AISC compliance checks.
- Sample data requires independent verification before design use.
