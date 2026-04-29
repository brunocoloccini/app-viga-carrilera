# Crane Runway Case Validation CLI

## Purpose

`validate_crane_runway_case.py` is a lightweight developer-facing CLI-style script for validating crane runway JSON case files and printing user-facing validation messages.

It is intended for local checks, CI helpers, and future UI/API pre-validation pipelines.

## Usage

From repository root:

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/crane_runway_case_demo.json
```

Multiple files:

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py examples/crane_runway_case_demo.json path/to/other_case.json
```

## Strict vs non-strict mode

- Default mode is **strict** (`strict=True`).
- Use `--non-strict` to run compatibility-oriented validation (`strict=False`).

Example:

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py --non-strict path/to/case.json
```

## Text output

For each file, deterministic text output is printed.

Valid file:

```text
VALID: examples/crane_runway_case_demo.json
```

Invalid file:

```text
INVALID: path/to/file.json
ERROR $.schema_version: Missing required field 'schema_version'.
Hint: Add "schema_version": "1.0" at the top level.
```

When validating multiple files, the script prints a blank line between file reports.

## JSON output

Use `--json` for machine-readable output:

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py --json examples/crane_runway_case_demo.json
```

Output shape:

```json
[
  {
    "path": "examples/crane_runway_case_demo.json",
    "valid": true,
    "messages": []
  }
]
```

Each `messages` entry follows `UserFacingValidationReport.to_dict()` serialization.

## Exit codes

- `0`: all files valid.
- `1`: at least one file invalid, unreadable, or malformed JSON.
- `2`: no input paths provided (argument/usage error).

## Intended future use

This script is intentionally simple so it can be reused by:

- UI upload pre-validation flows;
- API request pre-validation;
- CI pipelines validating case fixture sets.

## Limitations

This validator:

- validates schema/case structure only;
- does **not** run the engineering calculation workflow;
- does **not** perform CIRSOC-specific checks;
- does **not** replace engineering review.
