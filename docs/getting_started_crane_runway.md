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

Run:
- `PYTHONPATH=src python scripts/serve_crane_runway_ui.py`
- `PYTHONPATH=src python scripts/serve_crane_runway_ui.py --open`

Then open `http://127.0.0.1:8765`.

Suggested quick flow:

1. Confirm the header and beta warning in the page.
2. Select a built-in template and click **Load Template**.
3. (Optional) Edit the JSON in **JSON Editor**.
4. Click **Format JSON** to normalize the payload formatting.
5. Click **Validate** and review the **Validation** panel:
   - VALID/INVALID state.
   - tabular messages (`Severity`, `Path`, `Message`, `Hint`) when available.
   - **Find Path** per row (best-effort jump in editor).
   - **Copy Error List** for plain-text validation issues.
6. Click **Refresh Case Outline** to view key fields and quick completeness checks (`N/A` for missing fields).
7. Click **Run** and review:
   - **Result Cards** (max demands + PASS/FAIL/N/A criteria),
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

- You can import generated `projects/<name>/input_case.json` into the local UI using **Import JSON File**.

Important: this is a local beta tool. Results require engineering review.


### Local UI Common Inputs quick workflow (V1-066)

1. Load Template.
2. Load Form From JSON.
3. Edit Common Inputs.
4. Apply Form To JSON.
5. Click **Refresh Visual Preview** (or use the auto-refresh after template/import/apply) to inspect Beam/Section/Preview Summary schematic data.
6. Validate.
7. Run.
8. Download outputs.
