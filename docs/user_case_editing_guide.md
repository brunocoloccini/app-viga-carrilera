# User Case Editing Guide (Crane Runway)

This guide explains how to edit a generated project case file for real project inputs while staying within the current beta workflow scope.

Target file example:

- `projects/mi_viga/input_case.json`

## A) Basic workflow

1. Create project workspace and starter case:

```bash
PYTHONPATH=src python scripts/init_crane_runway_project.py --name mi_viga --template ipn-with-cover --validate
```

2. Edit case JSON:

- `projects/mi_viga/input_case.json`

3. Validate edits before execution:

```bash
PYTHONPATH=src python scripts/validate_crane_runway_case.py projects/mi_viga/input_case.json
```

4. Run case and generate report package:

```bash
PYTHONPATH=src python scripts/run_crane_runway_case.py projects/mi_viga/input_case.json --package-output projects/mi_viga/outputs --overwrite-package
```

5. Open report:

- `projects/mi_viga/outputs/report.html`

## B) Fields users commonly edit

```json
{
  "case_id": "mi_viga_rev02",
  "description": "Nave A - runway girder preliminary case",
  "span": {"value": 8, "unit": "m"},
  "base_shape_id": "CIRSOC_IPN_240",
  "section": {
    "section_id": "ipn_240_with_cover_plate",
    "base_component_id": "ipn_240",
    "base_center_y": {"value": 0, "unit": "mm"},
    "base_center_z": {"value": 120, "unit": "mm"},
    "cover_plate": {
      "enabled": true,
      "width": {"value": 180, "unit": "mm"},
      "thickness": {"value": 12, "unit": "mm"},
      "weld_size": {"value": 6, "unit": "mm"}
    }
  },
  "material": {
    "material_id": "S355",
    "Fy": {"value": 355, "unit": "MPa"},
    "Fu": {"value": 510, "unit": "MPa"},
    "E": {"value": 200000, "unit": "MPa"}
  },
  "analysis": {
    "movement_step": {"value": 250, "unit": "mm"},
    "station_step": {"value": 500, "unit": "mm"},
    "E": {"value": 200000, "unit": "MPa"}
  },
  "crane": {
    "crane_id": "grua_nave_a",
    "vertical_impact_factor": 0.25,
    "lateral_force_factor": 0.1,
    "wheels": [
      {"wheel_id": "W1", "position_x": {"value": 0, "unit": "mm"}, "vertical_force": {"value": 120, "unit": "kN"}},
      {"wheel_id": "W2", "position_x": {"value": 3, "unit": "m"}, "vertical_force": {"value": 120, "unit": "kN"}}
    ]
  },
  "criteria_presets": ["stress_0_90Fy"],
  "serviceability_limits": [{"limit_id": "strict_10mm", "type": "absolute", "max": {"value": 10, "unit": "mm"}}],
  "stress_limits": [{"limit_id": "0.90Fy", "type": "fraction_of_Fy", "factor": 0.9}],
  "rail_eccentricity": {
    "enabled": true,
    "vertical_eccentricity_y": {"value": 25, "unit": "mm"},
    "lateral_load_height_z": {"value": 100, "unit": "mm"}
  },
  "warnings": ["Editable starter case only."],
  "metadata": {"project": "mi_viga", "revision": "r02"}
}
```

## C) Common edits

1. Change span to 8 m: set `span` to `{"value": 8, "unit": "m"}`.
2. Change two wheel loads to 120 kN: update `crane.wheels[0].vertical_force` and `crane.wheels[1].vertical_force`.
3. Change wheel spacing to 3 m: set `crane.wheels[1].position_x` to `{"value": 3, "unit": "m"}` (or equivalent delta in your wheel list).
4. Disable cover plate: set `section.cover_plate.enabled` to `false`.
5. Change cover plate to 180 mm x 12 mm: set `section.cover_plate.width` and `section.cover_plate.thickness`.
6. Change base profile from `CIRSOC_IPN_200` to `CIRSOC_IPN_240`: update `base_shape_id`.
7. Change material Fy to 355 MPa: update `material.Fy`.
8. Disable rail eccentricity: set `rail_eccentricity.enabled` to `false`.
9. Add strict deflection limit absolute 10 mm: add an `absolute` entry in `serviceability_limits` with 10 mm max.
10. Use criteria preset `stress_0_90Fy`: include it in `criteria_presets`.

## D) Units

Quantity format is explicit:

```json
{"value": 120, "unit": "kN"}
```

- Units are validated.
- Compatible units are converted internally.
- Invalid units produce user-facing validation errors.

## E) Warnings and limitations

- CIRSOC sample data in this repo is manually curated and incomplete.
- Sample material values require independent verification.
- Rail sample data is fake test data unless real data is explicitly added later.
- Current checks are generic and include no official CIRSOC/CISC/AISC checks.
- No fatigue checks are currently implemented.
- No torsional/warping stress checks are currently implemented.
- No lateral-torsional buckling (LTB) checks are currently implemented.
- Engineering review is required before project decisions.
