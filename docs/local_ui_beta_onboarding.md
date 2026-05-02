# Local UI Beta Onboarding

## A. What this beta is

This beta is a local browser UI for crane runway case setup and generic elastic demand workflow.
It is not official code-compliance software.

## B. First-time setup

1. Clone/open this repository.
2. Install package dependencies (or run commands with `PYTHONPATH=src`).
3. Run:
   - `PYTHONPATH=src python scripts/print_local_ui_beta_info.py`
4. Run:
   - `PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest`

## C. Start the UI

Recommended:
- `PYTHONPATH=src python scripts/launch_crane_runway_ui.py`

Alternatives:
- `bash scripts/start_local_ui_beta.sh`
- `PowerShell scripts/start_local_ui_beta.ps1`

## D. Create demo project

- `PYTHONPATH=src python scripts/create_local_ui_demo_project.py --overwrite --run`

## E. Open demo in UI

1. Open **Project Workspace**.
2. Click **Refresh Project List**.
3. Open project `demo_local_ui_beta`.
4. Click **Validate**.
5. Click **Run Project To Outputs**.
6. Review the generated HTML report.

## F. Run checks

- Run UI Diagnostics.
- Run Demo Workflow.
- Run RC acceptance command: `PYTHONPATH=src python scripts/run_local_ui_rc_check.py --skip-archive`
- Complete manual QA checklist: `docs/local_ui_beta_manual_qa_checklist.md`

## G. Save/share results

- Project Archive Export
- Support Bundle
- Issue Report Helper

## H. Known limitations

See `docs/local_ui_beta_known_issues.md`.

## I. What to send back when reporting problems

- `support_bundle.json`
- issue report text
- screenshot (if available)
- commands run
- browser and operating system
