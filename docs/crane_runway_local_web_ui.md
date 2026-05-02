
# Crane Runway Local Web UI (V1-063)

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
  - Help / Workflow
  - Case Outline
  - Validation (status + message table + path helper)
  - Result Cards
  - Summary
  - HTML Report
  - Raw Response

## Buttons

- **Load Template**: loads selected template into JSON editor.
- **Validate**: sends current JSON to `/api/validate`.
- **Copy Error List**: copies a plain-text list of validation messages from the latest validation payload.
- **Run**: sends current JSON to `/api/run` with summary + HTML output formats.
- **Clear Output**: clears validation/summary/report/raw outputs.
- **Format JSON**: pretty-prints JSON editor content (2 spaces).
- **Clear JSON**: empties JSON editor content.
- **Open report in new tab**: appears when an HTML report exists.
- **Refresh Case Outline**: parses editor JSON and renders a quick key-field outline.

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

## Package Export panel (browser-side package builder)

The **Package Export** panel provides one-click browser downloads for calculation artifacts after Validate/Run:

- `case.json`
- `summary.json`
- `validation_response.json`
- `run_response.json`
- `report.html`
- `metadata.json`

Buttons:

- **Download Package Metadata**
- **Download Case JSON**
- **Download Validation Response**
- **Download Run Response**
- **Download Summary JSON**
- **Download Report HTML**
- **Download All Package Files**

Behavior:

- Individual buttons download one artifact if available and show a clear status message if unavailable.
- **Download All Package Files** downloads every currently available artifact and skips unavailable files.
- `metadata.json` is generated client-side with timestamp, available/unavailable lists, and review/limitations notes.

Important:
- Downloads are browser-side only.
- Files are not saved automatically to this repo.
- There is no server-side file persistence.
- No ZIP bundle is generated yet; save files manually into your project folder if needed.


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
- view validation messages as a table (`Severity`, `Path`, `Message`, `Hint`) with row-level **Find Path** helper;
- copy validation message list via **Copy Error List**;
- use **Find Path** as a best-effort key search in the JSON editor;
- refresh **Case Outline** to inspect key input fields (`schema_version`, `case_id`, `section.section_id`, `material.Fy`, etc.) with `N/A` for missing fields;
- view **Result Cards** for max demand values and PASS/FAIL/N/A check flags;
- view rendered summary table for key result fields;
- preview HTML report in-page and open it in a new tab;
- inspect full raw JSON response.

## Cannot do

- save/manage projects or files;
- authentication;
- database storage;
- file management;
- PDF/DOCX export;
- ZIP package export;
- project file management from UI;
- official CIRSOC/CISC/AISC checks;
- fatigue checks;
- torsion/warping/LTB checks.

## Current limitations

- **Find Path** is best-effort text matching on the path tail segment (not full AST navigation).
- **Case Outline** is client-side only and requires valid JSON text.
- **Result Cards** are display helpers only; they do not alter summary JSON or calculations.

## Security

Local-only development UI. It binds to `127.0.0.1` by default; do not expose publicly.

## Autosave and session restore (browser localStorage)

The local UI now autosaves editor session state in the browser using `localStorage` only.

Saved items:
- `craneRunway.caseJson`: current JSON editor text.
- `craneRunway.selectedTemplate`: current template selector value.
- `craneRunway.lastSavedAt`: ISO timestamp for latest autosave.

Behavior:
- JSON edits trigger autosave with a short debounce.
- Template changes and template/import/clear-json actions also refresh autosave state.
- On page load, if autosaved JSON exists, it is restored into the editor and status shows **Restored autosaved JSON.**
- Restore does **not** auto-run Validate or Run; users still click those actions manually.
- **Clear Saved Session** removes all autosave keys and resets autosave status to **No saved session**.

Autosave status text near the editor shows one of:
- `Autosave: Saved locally at <timestamp>`
- `Autosave: No saved session`
- `Autosave: Autosave unavailable`

Privacy note shown in UI:
- `Autosave is stored only in this browser using localStorage.`

Limitations:
- Autosave does not write files into this repository.
- Autosave does not save to any server.
- Clearing browser storage removes autosaved data.
- For durable storage, still use Download/Copy/Package Export actions.

## Common Inputs panel (V1-066)

A beginner-friendly **Common Inputs** panel is available above the JSON editor to edit frequent fields without manual JSON navigation.

Supported fields:
- General: Case ID, Description.
- Section: Base Shape ID, Cover Plate Enabled, Cover Plate Width/Thickness/Weld Size.
- Material: Material ID, Fy, Fu, E.
- Analysis: Span, Movement Step, Station Step.
- Crane: Crane ID, Vertical Impact Factor, Lateral Force Factor, Wheel 1 Load, Wheel 2 Load, Wheel Spacing.
- Rail eccentricity: Enabled, Vertical Eccentricity Y, Lateral Load Height Z.
- Criteria: Deflection Preset, Stress Preset.

Panel actions:
- **Load Form From JSON**: parses editor JSON and fills matching form fields; invalid JSON shows `Cannot load form: invalid JSON.`
- **Apply Form To JSON**: writes non-empty form values to JSON and pretty-prints with 2-space indentation; invalid JSON shows `Cannot apply form: invalid JSON.`
- **Reset Form**: clears panel inputs and shows `Common inputs reset.`

Notes shown in UI:
- `Common Inputs edits the JSON below. Review generated JSON before running.`
- `Advanced fields remain editable directly in JSON.`

Default units used in this version:
- Span: `m`
- Cover plate width/thickness/weld size: `mm`
- Fy/Fu/E: `MPa`
- Wheel loads: `kN`
- Movement/station step: `mm`
- Rail eccentricities: `mm`

Wheel behavior:
- Wheel 1 load -> `crane.wheels[0].vertical_force`
- Wheel 2 load -> `crane.wheels[1].vertical_force`
- Wheel spacing sets wheel 2 position relative to wheel 1 (`position_x` in `m`).
- If fewer than two wheels exist, simple `W1`/`W2` entries are created, preserving existing wheel IDs when present.

Limitations:
- The form is a convenience layer only.
- Generated JSON must still be reviewed by the user.
- Advanced/non-common fields still require direct JSON editing.
- No official CIRSOC/CISC/AISC checks.
- No fatigue, torsion/warping stress, or LTB checks.


## Visual Preview panel (V1-067)

The local UI now includes a **Visual Preview** panel with a **Refresh Visual Preview** action.

What it renders (browser-side only):
- **Beam Preview**: simple schematic of span, supports, and wheel markers/labels (`wheel_id`, vertical force, `position_x`).
- **Section Preview**: placeholder base shape rectangle labeled by `base_shape_id`, optional top cover plate marker when enabled, material label (`material_id`, `Fy`), and rail eccentricity enabled/disabled label.
- **Preview Summary**: key-case table with `case_id`, `base_shape_id`, `span`, wheel count, cover plate enabled, `material_id`, rail eccentricity enabled, and criteria presets.

Status behavior:
- Success: `Visual preview refreshed.`
- Invalid JSON: `Cannot refresh visual preview: invalid JSON.`

Important limitations:
- `Preview is schematic only and not to scale.`
- This preview does **not** run validation or calculations.
- No structural formulas or demand/check logic are executed by preview refresh.

Refresh integration:
- Visual preview refresh is called after **Load Template**, **Import JSON File**, and **Apply Form To JSON** complete.


## Result Interpretation panel (V1-068)

A new **Result Interpretation** panel appears near Summary/Result Cards after **Run**.

What it does:
- Interprets existing `summary` values only (no new formulas/check engines).
- Explains PASS/FAIL/N/A for overall, serviceability, and stress criteria.
- Adds beginner-oriented context for high deflection/stress demand relative to configured checks.
- Reports whether torsional input exists from `max_torsional_input_Nmm`.
- Reports whether run warnings are present.

Status meanings:
- **PASS**: relevant configured generic criterion passed in `summary`.
- **FAIL**: relevant configured generic criterion failed in `summary`.
- **N/A**: summary value missing/null, so no interpretation available for that line.

Important scope notes:
- Interpretation is explanatory only and uses run response summary values already produced by backend execution.
- It is **not** an official CIRSOC/CISC/AISC code-compliance verdict.

Copy support:
- **Copy Interpretation** copies plain-text interpretation lines to clipboard.
- If interpretation has not been generated yet, UI shows: `No interpretation available. Run a case first.`

Limitations (unchanged):
- no official code checks;
- no fatigue checks;
- no torsional/warping stress checks;
- no LTB checks;
- engineering review required.

## Scenario Comparison panel (V1-069)

The local UI includes a **Scenario Comparison** panel for browser-side comparison of alternatives.

Storage model:
- Uses `localStorage` key: `craneRunway.scenarios`.
- Stores an array with:
  - `scenario_id` (user-provided name),
  - `case_json` (JSON text for the case),
  - `saved_at` (ISO timestamp).
- Storage is browser-local only (no server-side database).

Controls:
- **Scenario Name**
- **Save Current Scenario**
- **Refresh Scenario List**
- **Run All Scenarios**
- **Clear All Scenarios**
- **Download Comparison JSON**
- **Copy Comparison JSON**
- Row actions: **Load Scenario**, **Delete Scenario**

Behavior:
- Save validates `scenario_id` and current JSON.
- Empty scenario name -> `Scenario name is required.`
- Invalid JSON on save -> `Cannot save scenario: invalid JSON.`
- Existing `scenario_id` is not overwritten in this version -> `Scenario already exists.`
- Load action restores selected scenario JSON into editor.
- Delete removes one scenario; clear removes all scenarios.

Run-all comparison:
- **Run All Scenarios** executes each saved case with `/api/run` using `output_formats: ["summary"]`.
- Status messages include:
  - `Running saved scenarios...`
  - `Scenario comparison complete.`
- If no scenarios exist:
  - `No saved scenarios available.`

Comparison table fields:
- `Scenario`
- `case_id`
- `base_shape_id`
- `cover_plate_enabled`
- `span`
- `max_vertical_moment_Nmm`
- `max_vertical_shear_abs_N`
- `max_vertical_deflection_mm`
- `max_biaxial_stress_MPa`
- `serviceability_passed`
- `stress_criteria_passed`
- `overall_passed`

Export/copy comparison:
- Uses last run-all results.
- **Download Comparison JSON** -> `scenario_comparison.json`.
- **Copy Comparison JSON** copies current comparison payload.
- If no results are available:
  - `No comparison results available. Run scenarios first.`

Limitations:
- Browser local only.
- No server-side scenario database.
- No official design-code comparison.
- Engineering review required.


## Beta UI manual QA (V1-070)

Before relying on the local beta UI for engineering workflows, run the manual checklist:

- [Local UI Beta Manual QA Checklist](local_ui_beta_manual_qa_checklist.md)

Also run the beta health check script and confirm it passes for your branch/environment.



## V1-071 Common Inputs validation and unit selectors

The **Common Inputs** panel now includes:
- **Validate Common Inputs** button (form-only check, no JSON mutation).
- **Common Inputs Errors** area:
  - shows `No common input errors.` when clear,
  - shows a Field/Message table when invalid.
- Apply flow safety: **Apply Form To JSON** runs client-side validation first and aborts JSON updates when errors exist, showing `Common inputs contain errors.`

Validation rules include:
- `Case ID` must not contain spaces (if provided).
- Positive numeric checks for section/material/analysis wheel fields (if provided).
- Non-negative checks for vertical impact and lateral force factors (if provided).
- Signed numeric acceptance for rail eccentricity Y/Z (if provided).

Unit selector pack:
- Span: `m`, `mm`, `ft`
- Cover plate width/thickness/weld: `mm`, `cm`, `in`
- Movement/station step: `mm`, `cm`, `in`
- Rail eccentricity Y/Z: `mm`, `cm`, `in`
- Wheel loads: `kN`, `N`, `kip`
- Fy/Fu/E: `MPa`, `ksi`, `psi`

Behavior:
- Apply writes selected units into quantity objects.
- Load selects unit when unit is supported.
- Unsupported existing units do not fail the load; value remains and default selector remains selected.

Limitations:
- Client-side helper validation only.
- JSON schema validation remains authoritative.
- Engineering review is still required.


## Wheel Table Editor (V1-072)

A new **Wheel Table Editor** panel provides beginner-friendly editing of `data.crane.wheels` without manual JSON typing.

Actions:
- **Load Wheels From JSON**: parse current JSON and populate rows; invalid JSON -> `Cannot load wheels: invalid JSON.`; no wheels -> `No wheels found in JSON.`
- **Apply Wheels To JSON**: validates rows, writes `crane.wheels`, pretty-prints JSON, triggers autosave/preview/outline refresh, status `Wheel table applied to JSON.`
- **Add Wheel**: adds a row with default `wheel_id` (`W1`, `W2`, ...), blank position and vertical force.
- **Clear Wheel Table**: removes all rows and sets `Wheel table cleared.`

Columns:
- Wheel ID
- Position X
- Position Unit (`m`, `mm`, `ft`)
- Vertical Force
- Force Unit (`kN`, `N`, `kip`)
- Remove

Validation rules:
- Wheel ID required and unique.
- Position required and numeric.
- Vertical force required and positive.
- Unit selectors must be selected.

Wheel Table Errors panel defaults to `No wheel table errors.` and renders required validation messages such as `Wheel ID is required.`, `Wheel IDs must be unique.`, `Wheel position must be numeric.`, and `Wheel vertical force must be positive.`

Mapping used when applying:

```json
{
  "wheel_id": "W1",
  "position_x": {"value": 0, "unit": "m"},
  "vertical_force": {"value": 80, "unit": "kN"}
}
```

Limitation in V1-072:
- The simple table editor focuses on `wheel_id`, `position_x`, and `vertical_force`.
- Extra per-wheel fields may be dropped when applying from the table.
- Advanced users can still edit raw JSON directly for unsupported/extra fields.


## Profile / Material Selector (V1-073)

The local UI includes a **Profile / Material Selector** convenience panel to edit base shape and material fields without hand-editing raw JSON.

Supported sample profile IDs:
- `CIRSOC_IPN_180`
- `CIRSOC_IPN_200`
- `CIRSOC_IPN_240`
- `CIRSOC_IPN_300`
- `CIRSOC_IPB_200`

Material presets:
- `F24` -> `material_id=F24`, `Fy=235 MPa`, `Fu=370 MPa`, `E=200000 MPa`
- `F36` -> `material_id=F36`, `Fy=355 MPa`, `Fu=470 MPa`, `E=200000 MPa`
- `Custom` -> leaves manual values unless currently empty

Actions:
- **Load Profile/Material From JSON**: loads `base_shape_id` (`root` or `section.base_shape_id`) and `material` fields from the current JSON editor payload.
- **Apply Profile/Material To JSON**: writes selected base shape and material values into schema-compatible paths, then pretty-prints JSON, autosaves (if available), and refreshes UI helpers.
- **Reset Profile/Material**: resets selector values to defaults.

Validation rules:
- Base shape is required.
- Material ID is required unless preset is `Custom` and all material fields are blank.
- `Fy`, `Fu`, and `E` must be positive when provided.

Warnings:
- Profile sample data is manually curated and incomplete. Verify before design use.
- Material presets are sample helpers and must be independently verified.
- No official CIRSOC/CISC/AISC compliance checks are performed.
- Engineering review is required before design use.

## Guided Workflow and beta readiness (V1-074)

New usability helpers in the local UI:
- **Guided Workflow** panel with 7 steps:
  1. Load Template or Import JSON
  2. Configure Inputs
  3. Refresh Preview
  4. Validate
  5. Run
  6. Review Results
  7. Export / Compare
- Step statuses are client-side only: **Pending**, **Done**, **Needs attention**.
- **Run Demo Workflow** runs an end-to-end path using `ipn-with-cover` (template load, preview refresh, validate, run, result rendering).
- Demo status text reports `Demo workflow complete.` or `Demo workflow failed.`

### Beta Readiness panel

- Includes local checks with PASS/FAIL/N/A:
  - UI JavaScript loaded
  - Backend health
  - JSON loaded
  - Validation status
  - Run status
  - Autosave available
- Includes **Check Backend Health** button that calls `/api/health` and reports:
  - `Backend health: OK.`
  - `Backend health: FAIL.`

### Troubleshooting panel

Visible guidance:
- If buttons do not respond, refresh the page.
- If the server is unreachable, start `scripts/serve_crane_runway_ui.py`.
- If JSON validation fails, review the Validation panel.
- If results show FAIL, review configured criteria and engineering assumptions.
- This local UI is a beta tool and requires engineering review.

### Important limitations

- Guided workflow and beta readiness are **beta helpers only**.
- They do **not** prove engineering correctness.
- No official CIRSOC/CISC/AISC checks are performed.
- No fatigue checks.
- No torsional/warping stress checks.
- No LTB checks.
- Engineering review is required.


## Field Help / Glossary pack (V1-075)

- Added **Field Help / Glossary** panel with short non-normative definitions for key inputs, outputs, and warnings.
- Added **Toggle Help** to show/hide the glossary panel in-page.
- Added **Search glossary** client-side filtering with `No glossary matches.` fallback text.
- Added inline helper text under major panels and lightweight native tooltips (`title`) for common inputs and wheel-table fields.

Important educational scope:
- Help text is educational and non-normative.
- It does not replace engineering judgment.
- It is not official CIRSOC/CISC/AISC guidance.
- No fatigue/torsion/warping/LTB checks are introduced by this UI help pack.
- Sample profile/material data still requires independent verification.

## Case Quality Warnings pack (V1-076)

- Added **Case Quality Warnings** panel with browser-side setup guidance.
- Added **Refresh Case Quality** action intended for use before Validate/Run.
- Severity levels used in the warnings table: **Info**, **Warning**, **Caution**.
- Table columns: **Severity**, **Area**, **Message**, **Suggested Action**.
- Added checks for missing metadata, material, wheels, duplicate wheel IDs, missing criteria, sample CIRSOC profile IDs, rail eccentricity setup, and cover plate setup.
- Added copy/export actions:
  - **Copy Case Quality Warnings** (plain text list)
  - **Download Case Quality Warnings JSON** (`case_quality_warnings.json`)

Limitations:
- Setup guidance only.
- Not engineering design checks.
- Not official CIRSOC/CISC/AISC compliance checks.
- No fatigue checks.
- No torsional/warping stress checks.
- No LTB checks.
- Engineering review is required before relying on results.

## V1-077 UI navigation and panel layout
- Added **UI Navigation** quick-jump panel and workflow focus buttons (Beginner/Advanced, Expand/Collapse all, Reset).
- Major panels now support Collapse/Expand toggles.
- Panel layout state persists in browser localStorage key `craneRunway.panelState` and restores on reload.
- Limitation: browser-local layout only; no server-side user preferences or authentication.
- Beta UI remains a helper and still requires engineering review.

## V1-078 Local UI Diagnostics hardening

- Added **Local UI Diagnostics** panel with **Run UI Diagnostics** button.
- Diagnostics run lightweight endpoint checks for `/api/health`, `/api/templates`, `/api/template/ipn-with-cover`, `/api/validate`, and `/api/run`.
- Diagnostics indicate UI/server connectivity only and do not prove engineering correctness.
- Use the beta health check, manual QA checklist, and engineering review before relying on outputs.


## One-command launcher

Recommended quick start:

```bash
PYTHONPATH=src python scripts/launch_crane_runway_ui.py
```

Useful options:

- `--no-open`
- `--host`
- `--port`
- `--check-only`
- `--skip-preflight`
- `--run-smoke-after-start`

The launcher runs preflight checks first, then starts the local-only server and prints the URL. Use `Ctrl+C` to stop the server.
