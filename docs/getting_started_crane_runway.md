# Getting Started: Crane Runway Case Workflow

This guide shows the baseline internal-beta command path for validating and running a crane runway JSON case.

## A) Validate a case

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/crane_runway_case_demo.json
```

## B) Run a case

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json
```

## C) Generate markdown

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --markdown
```

## D) Generate HTML

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --html --output out/report.html
```

## E) Generate package

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --package-output out/demo --overwrite-package
```

## F) Run scenario matrix

```bash
PYTHONPATH=src python scripts/run_crane_runway_case_matrix.py
```

## G) Run matrix HTML

```bash
PYTHONPATH=src python scripts/run_crane_runway_case_matrix.py --html --output out/matrix.html
```


## H) Create your first project

```bash
PYTHONPATH=src python scripts/init_crane_runway_project.py --name mi_viga --template ipn-with-cover
```

This creates `projects/mi_viga/input_case.json`, `projects/mi_viga/README.md`, and `projects/mi_viga/outputs/`.

## Notes

- Sample data is for demonstration/regression and requires independent verification.
- Current checks are generic and are not official CIRSOC/CISC/AISC code compliance checks.

## I) Edit generated project cases

After you initialize a project, use the dedicated user editing guide for practical JSON edits and examples:

- [User Case Editing Guide](user_case_editing_guide.md)
- `examples/editing_guide/`



## Use the local web UI

Recommended first command:

```bash
PYTHONPATH=src python scripts/launch_crane_runway_ui.py
```

Fallback server command:

```bash
PYTHONPATH=src python scripts/serve_crane_runway_ui.py --host 127.0.0.1 --port 8765
```

Then open `http://127.0.0.1:8765` if your browser does not open automatically.

Suggested quick flow:

1. Confirm the header and beta warning in the page.
2. Select a built-in template and click **Load Template**.
3. (Optional) Edit the JSON in **JSON Editor**.
4. For multi-wheel edits (more than two wheels), use **Wheel Table Editor** instead of manual `crane.wheels` JSON edits.
4a. Use **Field Help / Glossary** while editing inputs to review quick term definitions without leaving the page.
5. Click **Format JSON** to normalize the payload formatting.
6. Click **Validate** and review the **Validation** panel:
   - VALID/INVALID state.
   - tabular messages (`Severity`, `Path`, `Message`, `Hint`) when available.
   - **Find Path** per row (best-effort jump in editor).
   - **Copy Error List** for plain-text validation issues.
7. Click **Refresh Case Outline** to view key fields and quick completeness checks (`N/A` for missing fields).
8. Click **Run** and review:
   - **Result Cards** (max demands + PASS/FAIL/N/A criteria),
   - **Result Interpretation** panel (plain-language explanation using existing summary values only),
   - **Summary** panel (key fields table),
   - **HTML Report** iframe preview,
   - **Raw Response** panel for full JSON.
8. Use **Open report in new tab** when available.
9. Use **Clear Output** and **Clear JSON** as needed for a clean reset.
10. Use **Download / Copy** actions for local exports:
   - download/copy case JSON,
   - download/copy summary JSON,
   - download HTML report,
   - copy validation response,
   - copy raw response.
11. Local autosave keeps JSON editor/session state in this browser (`localStorage`) and restores it on refresh; use **Clear Saved Session** to remove local autosaved data.
12. Use **Package Export** for browser-side artifact packaging:
   - download `metadata.json`, `case.json`, `summary.json`, `validation_response.json`, `run_response.json`, `report.html`,
   - or click **Download All Package Files** to export all currently available files.
   - unavailable artifacts are skipped and reported in the status bar.
13. Use **Scenario Comparison** to compare alternatives in-browser:
   - enter **Scenario Name** and click **Save Current Scenario** for each variant,
   - click **Run All Scenarios** to generate a comparison table from summary outputs,
   - use **Download Comparison JSON** or **Copy Comparison JSON** for downstream review.

- You can import generated `projects/<name>/input_case.json` into the local UI using **Import JSON File**.

Important: this is a local beta tool. Results require engineering review.

- For end-to-end UI testing, follow `docs/local_ui_beta_manual_qa_checklist.md`.


### Local UI Common Inputs quick workflow (V1-066)

1. Load Template.
2. Load Form From JSON.
3. Edit Common Inputs.
4. Optionally use **Profile / Material Selector** to choose base profile and material preset/value inputs before validation.
5. Click **Validate Common Inputs** and resolve any Common Inputs Errors.
6. Apply Form To JSON.
7. Click **Refresh Visual Preview** (or use the auto-refresh after template/import/apply) to inspect Beam/Section/Preview Summary schematic data.
6. Validate.
7. Run.
8. Download outputs.


### Recommended first local UI flow (V1-074)

1. Open the local UI.
2. Click **Check Backend Health**.
3. Click **Run Demo Workflow**.
4. Inspect **Results**, **Result Interpretation**, and **HTML Report**.
5. Then click **Refresh Case Quality** and review setup warnings.
6. Edit your own case and rerun Validate/Run.

- Start in **Show Beginner View** and use **UI Navigation** to jump directly to key sections.

## Recommended local UI startup flow (beta)
1. Start server.
2. Open UI.
3. Run UI Diagnostics.
4. Run Demo Workflow.
5. Use Common Inputs / Wheel Table / Presets.
6. Validate and Run.
7. Export results.

## Recommended Local UI Project Workflow

1. Launch UI.
2. Create project.
3. Configure inputs.
4. Save JSON to project.
5. Validate.
6. Run project to outputs.
7. Review `report.html` in `projects/<name>/outputs`.


## Project Run History workflow (V1-081)
1. Create/open project.
2. Save `input_case.json`.
3. Run **Run Project As History Snapshot**.
4. Refresh and review run history.
5. Load a previous run summary/report.

## Project Run Comparison workflow (V1-082)
1. Create or open a local project in **Project Workspace**.
2. Run the project as a history snapshot multiple times.
3. In **Project Run Comparison**, click **Refresh Runs For Comparison**.
4. Choose one **Baseline Run**.
5. Select one or more **Comparison Runs**.
6. Click **Compare Selected Runs** to render rows, deltas, and PASS/FAIL indicators.
7. Click **Download Run Comparison JSON** to save `project_run_comparison.json`.


- Developer RC acceptance check: `PYTHONPATH=src python scripts/run_local_ui_rc_check.py --skip-archive`.

## Project archive backup workflow (V1-083)
1. Create/open project.
2. Save/run project.
3. Refresh archive manifest.
4. Download project archive.
5. Store archive outside repo if desired.

## If something goes wrong
- Use **Issue Report Helper** to copy issue report text.
- Use **Support Bundle** to download support_bundle.json for debugging.

## Recommended beta path
Use launcher + Run Demo Workflow + Local UI RC Status as the primary path. See `docs/local_ui_beta_feature_map.md` and `docs/local_ui_beta_known_issues.md`.

## Local UI beta quick-start recommendation

1. `PYTHONPATH=src python scripts/print_local_ui_beta_info.py`
2. `PYTHONPATH=src python scripts/create_local_ui_demo_project.py --overwrite --run`
3. `PYTHONPATH=src python scripts/launch_crane_runway_ui.py`
4. Open Project Workspace.

## Local UI first-time flow
1. Read **Welcome to the Local UI Beta**.
2. Run **Guided Demo** steps before editing production cases.
3. Use **Documentation Portal** when unsure.

## Local UI first-use flow (V1-089)

1. Launch UI.
2. Start on **Home** tab.
3. Click **Load Demo** or **Start Guided Demo**.
4. Go to **Inputs** to configure common fields.
5. Go to **Wheels** to edit wheel loads.
6. Go to **Preview** to inspect setup.
7. Go to **Validate & Run**.
8. Go to **Results**.
9. Use **Export** or **Project** tabs as needed.
\n\n## V1-090 Form-first workflow update\nUI now supports a form-first workflow (Project → Beam & Section → Material → Crane Wheels → Criteria → Rail / Eccentricity → Preview → Validate → Run → Results → Export). Advanced JSON remains available in the Advanced tab.\n

## Recommended first path (V1-093)
1. Launch UI.
2. Home tab.
3. Beginner Dashboard.
4. Start Case Wizard.
5. Complete wizard steps.
6. Validate & Run.
7. Review Results.
8. Export outputs.
9. Use Advanced JSON only if needed.
