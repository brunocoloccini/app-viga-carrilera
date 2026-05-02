# Local UI Internal Beta RC

## Scope included
- local UI
- project workspace
- templates
- validation/run
- reports
- project outputs/history/archive
- support bundle
- diagnostics/RC acceptance

## Scope excluded
- official code checks
- fatigue
- torsional/warping stress
- LTB
- PDF/DOCX
- authentication
- database
- public deployment
- verified production shape/material database

## How to start
`PYTHONPATH=src python scripts/launch_crane_runway_ui.py`

## Required pre-handoff commands
- `PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest`
- `PYTHONPATH=src python scripts/run_local_ui_rc_check.py --skip-archive`

## Manual QA
`docs/local_ui_beta_manual_qa_checklist.md`

## Support
`docs/local_ui_support_bundle.md`

## Known limitations
`docs/local_ui_beta_known_issues.md`
