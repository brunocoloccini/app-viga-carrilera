# Local UI Beta Manual QA Checklist

Use this checklist to run a consistent manual smoke test for the crane runway local beta UI before relying on it for engineering workflows.

## A) Start the UI

Command:

```bash
PYTHONPATH=src python scripts/serve_crane_runway_ui.py --host 0.0.0.0 --port 8765
```

Expected:
- Server starts without errors.
- UI opens via forwarded port, or at `http://127.0.0.1:8765`.

## B) Template workflow

1. Load template `ipn-with-cover`.
2. Confirm JSON editor is populated.
3. Confirm Visual Preview updates.
4. Click **Validate**.
5. Confirm **Validation** panel shows `VALID` or messages.
6. Click **Run**.
7. Confirm **Result Cards**, **Result Interpretation**, **Summary**, **HTML Report**, and **Raw Response** update.

## C) Common Inputs workflow

1. Click **Load Form From JSON**.
2. Change span.
3. Change wheel loads.
4. Toggle cover plate.
5. Click **Apply Form To JSON**.
6. Confirm JSON changes.
7. Refresh **Visual Preview**.
8. **Validate** and **Run**.

9. Enter invalid span (for example `0`), click **Validate Common Inputs**, and confirm `Span must be positive.` appears in **Common Inputs Errors**.
10. Fix span to positive value and click **Validate Common Inputs** again; confirm `Common inputs are valid.`
11. Click **Apply Form To JSON** and confirm JSON updates only after valid form state.

## D) Import JSON workflow

1. Create a project with `init_crane_runway_project.py`.
2. Import `projects/<name>/input_case.json` using **Import JSON File**.
3. Confirm imported JSON appears in editor.
4. **Validate**.
5. **Run**.

## E) Export workflow

1. Run a case.
2. Download JSON Case.
3. Download Summary JSON.
4. Download HTML Report.
5. Download All Package Files.
6. Copy Summary JSON.
7. Copy Interpretation.

## F) Scenario comparison workflow

1. Save current scenario as `base`.
2. Modify Common Inputs.
3. Save as `variant`.
4. Run All Scenarios.
5. Confirm comparison table renders.
6. Download Comparison JSON.

## G) Autosave workflow

1. Edit JSON.
2. Refresh page.
3. Confirm autosaved JSON is restored.
4. Click **Clear Saved Session**.
5. Refresh again.
6. Confirm saved session is cleared.

## H) Expected limitations

- Local browser UI only.
- No server-side save.
- No PDF/DOCX export.
- No official CIRSOC/CISC/AISC checks.
- No fatigue checks.
- No torsional/warping stress checks.
- No LTB checks.
- Engineering review required.

## I) Manual QA signoff template

- Date:
- Tester:
- Commit:
- Browser:
- Operating system:
- Result (PASS/FAIL):
- Notes:
