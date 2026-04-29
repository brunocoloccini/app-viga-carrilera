# Crane Runway Case Schema (V1-037)

This document defines the versioned schema and validation layer for crane runway JSON case files.

## Purpose
- Make the case format explicit and user-facing.
- Provide deterministic, pre-run validation for UI/API integrations.
- Keep this layer independent from structural design-code checks.

## Schema version
- Current schema version: `1.0`.
- Cases should include: `"schema_version": "1.0"`.
- `run_crane_runway_case_dict` and `run_crane_runway_case_json` enforce strict validation.

## Relationship with `case_io.py`
- `load_crane_runway_case_json(path)` reads raw JSON payloads.
- `validate_crane_runway_case_dict(data, strict=...)` performs schema checks.
- `assert_valid_crane_runway_case_dict(...)` raises with aggregated issues.
- Run helpers validate first, then build workflow inputs.

## Quantity object format
Use explicit quantity dictionaries:

```json
{"value": 250, "unit": "mm"}
```

Validation requires:
- object type,
- `value` numeric,
- `unit` non-empty string.

## Required blocks
Top-level required keys:
- `schema_version`, `case_id`, `shape_library_path`, `base_shape_id`,
- `section`, `span`, `analysis`, `crane`.

## Optional blocks
- `description`, `serviceability_limits`, `stress_limits`, `rail_eccentricity`, `warnings`, `metadata`.

## Supported limit types
- Serviceability: `span_over`, `absolute`, `minimum_of_span_over_and_absolute`.
- Stress: `absolute`, `fraction_of_Fy`.

## Disabled behavior notes
- Disabled cover plate (`section.cover_plate.enabled=false`) requires no cover-plate dimensions.
- Disabled rail eccentricity (`rail_eccentricity.enabled=false`) requires no eccentricity quantities.

## Exported schema file
- JSON-schema-like export: `examples/crane_runway_case_schema_v1.json`.
- This is intended for documentation and lightweight tooling integration.

## Validation strategy
- Collect all issues into `CaseSchemaValidationResult`.
- `error` issues make result invalid.
- In non-strict mode, missing `schema_version` is a warning for backward compatibility.

## Current limitations
- The JSON Schema dictionary is an internal aid; no external validator dependency is required.
- No UI layer yet.
- No CIRSOC-specific checks.
- No fatigue checks.
- No torsional/warping stress checks.
- Sample CIRSOC data still requires independent verification before production use.
