# Crane Runway Case Execution CLI

## Purpose
`scripts/run_crane_runway_case.py` is a lightweight developer/user tooling script that executes a crane runway JSON case and prints calculation reports.

It is complementary to the validation-only CLI (`scripts/validate_crane_runway_case.py`):
- validation CLI: validates schema and reports issues;
- execution CLI: validates as part of execution, then runs the full case workflow and prints report outputs.

## Usage
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json
```

The script accepts exactly one case path positional argument.

## Output modes
Default mode is `--text`.

### Text
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py --text examples/crane_runway_case_demo.json
```

### Markdown
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py --markdown examples/crane_runway_case_demo.json
```

### Both
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py --both examples/crane_runway_case_demo.json
```
Prints text report, a separator (`---`), then markdown report.

### HTML
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py --html examples/crane_runway_case_demo.json
```

### Summary JSON
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py --summary-json examples/crane_runway_case_demo.json
```
Prints `summary.to_dict()` as formatted JSON.

Modes are mutually exclusive.

## Optional output file
Use `--output PATH` to write selected output mode content to a file instead of stdout:

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py --html --output tmp/report.html examples/crane_runway_case_demo.json
```

On success, stdout prints:

```text
WROTE: tmp/report.html
```

## Exit codes
- `0`: successful execution.
- `1`: validation/execution/read/write error.
- `2`: argument/usage error (argparse).

## Validation and error behavior
- Normal validation/execution errors are printed as user-facing formatted messages via `CraneRunwayCaseErrorFormatter`.
- Invalid schema cases are shown as validation-style errors (for example, missing `schema_version`), without Python traceback output.

## Relationship to validation CLI
- Use `scripts/validate_crane_runway_case.py` when you want schema/compatibility checks only.
- Use `scripts/run_crane_runway_case.py` when you want to actually run the case and print reports.

## Limitations
This script intentionally does **not** add:
- PDF/DOCX export;
- UI features;
- CIRSOC-specific checks;
- fatigue checks;
- torsional/warping stress checks;
- substitution for engineering review.
