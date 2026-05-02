# section_core Internal Beta

`section_core` is a UI-independent Python engineering core focused on crane runway beam workflow modeling, analysis, and reporting.

## Internal beta purpose

This internal beta packages the current crane runway workflow so the team can validate case authoring, deterministic outputs, CLI/API boundaries, and regression behavior before broader release.

## Beta scope (current)

The engine currently includes:

- units, geometry, section components, and gross section properties;
- shape library support with manually curated sample CIRSOC shapes;
- materials and sample rail registries;
- crane runway load generation, vertical/lateral analysis, deflection, elastic stress, and generic criteria checks;
- JSON case schema, case I/O, validation/execution scripts;
- markdown/HTML reporting plus report-package export;
- scenario matrix and golden regression workflows;
- API service boundary for validation/execution.

## What it can do today

- Build/assemble sections and compute gross elastic properties.
- Run crane runway demand workflows from JSON inputs.
- Validate JSON case files with strict/non-strict schema modes.
- Produce text/markdown/HTML summaries and report packages.
- Execute scenario matrix and golden-regression flows for deterministic verification.

## What it cannot do yet

- Official CIRSOC/CISC/AISC compliance checks.
- Fatigue, torsional/warping stress, or LTB checks.
- Rail local wheel-patch/local stress checks.
- Weld strength checks.
- Full design-code load-combination engines.
- UI or PDF/DOCX report generation.

## Quick start

```bash
# Run test suite
pytest -q

# Validate a JSON case
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/crane_runway_case_demo.json

# Run a JSON case
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json

# Generate Markdown or HTML
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --markdown
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --html --output out/report.html

# Generate report package
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --package-output out/demo --overwrite-package

# Run scenario matrix
PYTHONPATH=src python scripts/run_crane_runway_case_matrix.py
```

## Key documentation

- [Getting started: crane runway workflow](docs/getting_started_crane_runway.md)
- [JSON case authoring guide](docs/json_case_authoring_guide.md)
- [Command reference](docs/command_reference.md)
- [Known limitations](docs/known_limitations.md)
- [Internal beta release checklist](docs/beta_release_checklist.md)

## Important warnings

- Sample data in this repository must be independently verified before any engineering use.
- Current criteria checks are generic software checks only and are **not** official CIRSOC/CISC/AISC compliance checks.

## Local UI internal beta
- Getting started: `docs/getting_started_crane_runway.md`
- Local UI guide: `docs/crane_runway_local_web_ui.md`
- Feature map: `docs/local_ui_beta_feature_map.md`
- RC release notes: `docs/local_ui_beta_rc_release_notes.md`
- Known issues: `docs/local_ui_beta_known_issues.md`
- Manual QA checklist: `docs/local_ui_beta_manual_qa_checklist.md`
