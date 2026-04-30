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
   - listed validation messages (severity/path/message/hint when present).
6. Click **Run** and review:
   - **Summary** panel (key fields table),
   - **HTML Report** iframe preview,
   - **Raw Response** panel for full JSON.
7. Use **Open report in new tab** when available.
8. Use **Clear Output** and **Clear JSON** as needed for a clean reset.
9. Use **Download / Copy** actions for local exports:
   - download/copy case JSON,
   - download/copy summary JSON,
   - download HTML report,
   - copy validation response,
   - copy raw response.

Important: this is a local beta tool. Results require engineering review.
