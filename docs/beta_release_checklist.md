# Internal Beta Release Checklist

## Scope included in internal beta

- Section Builder primitives.
- Shape libraries.
- Materials.
- Rails sample registry.
- Crane runway load modeling.
- Vertical and lateral analysis.
- Deflection workflows.
- Elastic stress workflows.
- Generic criteria checks.
- JSON case schema and case execution.
- Markdown/HTML/report-package outputs.
- CLI validation/execution scripts.
- API service boundary.

## Not included in this beta

- Official CIRSOC/CISC/AISC compliance checks.
- Fatigue checks.
- Torsion/warping stress checks.
- LTB checks.
- Rail local checks.
- Weld strength checks.
- UI.
- PDF/DOCX output.

## Pre-release verification

- `PYTHONPATH=src python scripts/run_beta_health_check.py` passes.
- `PYTHONPATH=src python scripts/run_local_ui_rc_check.py --skip-archive` passes before manual QA.
- `pytest -q` passes.
- Scenario matrix CLI runs successfully.
- Golden regression tests pass.
- `README.md` reviewed and updated.
- `docs/known_limitations.md` reviewed and current.

## Release notes template

- **Version:**
- **Date:**
- **Test count:**
- **Notable changes:**
- **Known limitations:**

- [ ] Support bundle guide reviewed and shared (`docs/local_ui_support_bundle.md`).
- [ ] Beta handoff package prepared (`docs/local_ui_beta_handoff.md`).
