
# Crane Runway Local Web UI (V1-060)

Local browser UI for crane runway beta workflows. It is a developer convenience wrapper around the existing API service.

## Run

- `PYTHONPATH=src python scripts/serve_crane_runway_ui.py`
- `PYTHONPATH=src python scripts/serve_crane_runway_ui.py --open`

Default URL: `http://127.0.0.1:8765`

## UI overview

- **Header and warning**: "Crane Runway Local UI" with a local beta warning: "Local beta tool. Results require engineering review."
- **Template selector**: pick a built-in template and load it into the editor.
- **JSON editor**: direct case JSON editing/pasting.
- **Status bar**: clear state transitions for load/validate/run actions and network errors.
- **Output panels**:
  - Validation
  - Summary
  - HTML Report
  - Raw Response

## Buttons

- **Load Template**: loads selected template into JSON editor.
- **Validate**: sends current JSON to `/api/validate`.
- **Run**: sends current JSON to `/api/run` with summary + HTML output formats.
- **Clear Output**: clears validation/summary/report/raw outputs.
- **Format JSON**: pretty-prints JSON editor content (2 spaces).
- **Clear JSON**: empties JSON editor content.
- **Open report in new tab**: appears when an HTML report exists.

## Can do

- load built-in templates;
- edit/paste JSON case payloads;
- validate cases;
- run cases;
- view rendered validation status/messages;
- view rendered summary table for key result fields;
- preview HTML report in-page and open it in a new tab;
- inspect full raw JSON response.

## Cannot do

- save/manage projects or files;
- authentication;
- database storage;
- file management;
- PDF/DOCX export;
- official CIRSOC/CISC/AISC checks;
- fatigue checks;
- torsion/warping/LTB checks.

## Security

Local-only development UI. It binds to `127.0.0.1` by default; do not expose publicly.
