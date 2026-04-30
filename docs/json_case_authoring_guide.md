# JSON Case Authoring Guide

Use this guide to author crane runway input files compatible with the current internal-beta schema and CLI flow.

## Core fields

- `schema_version`: versioned schema selector (required).
- `case_id`: stable case identifier string for traceability.
- `shape_library_path`: path to shape library JSON source.
- `base_shape_id`: shape ID selected from the library.
- `section`: section assembly inputs (for example, optional cover plate geometry/units).
- `material`: material definition or material reference used for stress criteria derivation.
- `analysis`: span, discretization, and workflow analysis options.
- `crane`: wheel loads, spacing, dynamic/lateral inputs, and related crane parameters.
- `serviceability_limits` and `stress_limits`: explicit criteria limits can be set per case.
- `criteria_presets`: optional preset selection to populate generic criteria defaults.
- `rail_eccentricity`: optional rail/load eccentricity inputs for torsional demand contribution.
- `warnings`: optional list for author-provided cautionary notes.
- `metadata`: optional non-calculation context (project, author, revision, tags).

## Quantity object format

Use explicit value/unit objects for dimensional inputs:

```json
{"value": 80, "unit": "kN"}
```

Units are validated on read/validation. Missing units or incompatible units produce user-facing validation/execution errors.

## Compact example

```json
{
  "schema_version": "v1",
  "case_id": "demo_internal_beta",
  "shape_library_path": "data/shape_libraries/cirsoc_profiles_sample.json",
  "base_shape_id": "IPN_200",
  "section": {
    "cover_plate": {
      "enabled": true,
      "width": {"value": 180, "unit": "mm"},
      "thickness": {"value": 12, "unit": "mm"}
    }
  },
  "material": {
    "grade_id": "F24"
  },
  "analysis": {
    "span": {"value": 12, "unit": "m"},
    "station_step": {"value": 100, "unit": "mm"}
  },
  "crane": {
    "wheel_load": {"value": 80, "unit": "kN"}
  },
  "criteria_presets": ["GENERIC_STEEL_FY_240"],
  "serviceability_limits": {
    "vertical_deflection_ratio": 600
  },
  "stress_limits": {
    "allowable_bending_stress": {"value": 160, "unit": "MPa"}
  },
  "rail_eccentricity": {
    "vertical_load_eccentricity": {"value": 20, "unit": "mm"}
  },
  "warnings": ["Demo input only"],
  "metadata": {
    "project": "internal_beta",
    "revision": "r1"
  }
}
```


## Starting from built-in templates

You can generate starter files with `scripts/create_crane_runway_case_template.py`.
The built-in IDs are `ipn-with-cover`, `ipn-without-cover`, and `ipn-no-rail-eccentricity`.
Generated files include `schema_version: "1.0"` and are strict-schema valid.

## Practical editing guide and examples

For step-by-step editing of generated workspace files, see:

- `docs/user_case_editing_guide.md`
- `examples/editing_guide/`

Use these alongside this authoring guide when adapting built-in templates to project-specific values.
