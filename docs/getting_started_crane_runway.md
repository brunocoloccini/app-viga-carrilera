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

