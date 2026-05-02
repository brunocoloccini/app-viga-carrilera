# Local UI Frontend Contract
Purpose: keep Local UI wiring stable with a machine-readable contract and self-test.
- Endpoint: `/assets/frontend_contract.json`.
- UI panel: **Frontend Self-Test** (Support tab) with run/copy/download actions.
- CLI checker: `PYTHONPATH=src python scripts/check_local_ui_frontend_contract.py`.
- Node syntax check: runs `node --check` when available; can skip via `--no-node`.
Checks include tabs, panels, actions, JS functions, storage keys, API paths, and CSS design-system tokens.
Does **not** check browser rendering correctness, engineering correctness, or official code compliance.

## Commands
- `PYTHONPATH=src python scripts/check_local_ui_frontend_contract.py`
- `PYTHONPATH=src python scripts/check_local_ui_frontend_contract.py --json`
- `PYTHONPATH=src python scripts/check_local_ui_frontend_contract.py --output out/frontend_contract_report.json`

- V1-093 adds Beginner Dashboard, Case Wizard, Case Readiness, Wizard Change Summary and wizard actions/functions/storage key craneRunway.caseWizardState.
\n## V1-094 Update\n- Local UI visual workflow builder, simplified landing flow, and user-facing polish pack.\n- First-time users should stay in Simple Mode and follow Visual Workflow Map; Advanced JSON is optional.\n- Added Top action bar, What should I do now?, and Status Legend.\n
