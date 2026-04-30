
# Crane Runway Local Web UI (V1-061)

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

## Download / Copy actions (local browser only)

The **Download / Copy** toolbar adds local browser export helpers:

- **Download JSON Case**: validates editor JSON, pretty-prints with 2-space indentation, and downloads `crane_runway_case.json`.
- **Copy JSON Case**: copies current JSON editor text to clipboard.
- **Download Summary JSON**: downloads latest run summary as `summary.json`.
- **Copy Summary JSON**: copies latest run summary JSON.
- **Download HTML Report**: downloads latest run HTML report as `report.html`.
- **Copy Validation Response**: copies latest validation response JSON.
- **Copy Raw Response**: copies current raw response panel JSON text.

Notes:
- These are client-side browser actions only.
- The UI does not save files into this repository.
- There is no server-side persistence for downloaded/copied artifacts.


## Importing a local JSON case file

Use **Import JSON File** in the UI to load an existing `.json` case from your machine directly into the JSON editor.

- Import uses the browser `FileReader` API and is **client-side only**.
- The selected file is **not uploaded** to the server.
- The selected file is **not saved** on the server.
- If **Validate after import** is checked, the UI automatically runs **Validate** after loading.
- If unchecked (default), the UI only loads the file.
- After import, you can continue with **Validate**, **Run**, and local **Download / Copy** actions.

Limitations:
- No project file management in the UI yet.
- No automatic save back to the original local file.
- Use browser **Download JSON Case** to save edited JSON.

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
- project file management from UI;
- official CIRSOC/CISC/AISC checks;
- fatigue checks;
- torsion/warping/LTB checks.

## Security

Local-only development UI. It binds to `127.0.0.1` by default; do not expose publicly.
