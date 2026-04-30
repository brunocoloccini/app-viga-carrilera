# Crane Runway Report Package Export

## Purpose
`CraneRunwayReportPackageWriter` exports a deterministic folder of artifacts for a crane runway JSON case execution.

## Package files
- `input_case.json`
- `validation_report.json`
- `summary.json`
- `report.txt`
- `report.md`
- `report.html`
- `metadata.json`
- `manifest.json`

## Determinism / reproducibility
JSON files are serialized with sorted keys and fixed indentation (`indent=2`, `sort_keys=True`) for stable outputs across repeated runs of the same case.

## Overwrite behavior
- If destination does not exist: it is created.
- If destination exists and is empty: files are written.
- If destination exists and is non-empty:
  - default: fail with package error;
  - with overwrite enabled: package files are overwritten; unrelated files may remain untouched.

## CLI usage
```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --package-output out/demo
PYTHONPATH=src python scripts/run_crane_runway_case.py examples/crane_runway_case_demo.json --markdown --package-output out/demo --overwrite-package
```

## Limitations
- No PDF export.
- No DOCX export.
- No UI export.
- Package output is **not** an independent engineering verification.
- No CIRSOC-specific design-code checks in this layer.
- No fatigue checks.
- No torsion/warping stress checks.
- No LTB checks.
