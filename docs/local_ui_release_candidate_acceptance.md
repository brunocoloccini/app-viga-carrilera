# Local UI release-candidate acceptance

## Purpose
The RC acceptance check runs a realistic automated end-to-end verification for the local UI beta server and workflow stack before manual QA or handoff.

## When to run
- After local UI feature merges.
- Before beta handoff.
- Before manual QA sessions.

## Command
```bash
PYTHONPATH=src python scripts/run_local_ui_rc_check.py
```

## Key options
- `--port`
- `--project-name`
- `--template`
- `--skip-archive`
- `--keep-server`
- `--verbose`

## What it checks
- Server start and health readiness.
- Core endpoints (`/`, `/api/health`, template endpoints).
- Template validate and run.
- Project workspace create/open/save/run.
- Project run history snapshot/list/load.
- Project archive manifest and ZIP export.
- Inline JavaScript function presence and `node --check` syntax (when Node is available).

## Limitations
- Not browser automation.
- Not an engineering correctness proof.
- Not an official CIRSOC/CISC/AISC compliance check.
- No fatigue/torsion/warping/LTB checks.
- Engineering review remains required.

See `docs/local_ui_beta_rc_release_notes.md` and `docs/local_ui_beta_feature_map.md` for RC scope and feature mapping.
