
# Crane Runway Local Web UI (V1-059)

Local browser UI for crane runway beta workflows. It is a developer convenience wrapper around the existing API service.

## Run

- `PYTHONPATH=src python scripts/serve_crane_runway_ui.py`
- `PYTHONPATH=src python scripts/serve_crane_runway_ui.py --open`

Default URL: `http://127.0.0.1:8765`

## Can do

- load built-in templates;
- edit/paste JSON case payloads;
- validate cases;
- run cases;
- view summary JSON and HTML report preview.

## Cannot do

- save/manage projects or files;
- authentication;
- database storage;
- PDF/DOCX export;
- official CIRSOC/CISC/AISC checks;
- fatigue checks;
- torsion/warping/LTB checks.

## Security

Local-only development UI. It binds to `127.0.0.1` by default; do not expose publicly.
