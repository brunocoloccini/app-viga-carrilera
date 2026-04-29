# Crane Runway Case JSON: Material Block and Criteria Preset References (V1-048)

## Purpose
V1-048 extends crane runway case JSON with optional `material` and `criteria_presets` blocks for case I/O integration only.

## `material` block
- Optional top-level object.
- Fields:
  - `material_id` (required non-empty string)
  - `Fy` (required quantity: `value` + `unit`)
  - `Fu` (optional quantity)
  - `E` (optional quantity)
  - `source` (optional string)
  - `metadata` (optional object)

Example:
```json
"material": {
  "material_id": "F24",
  "Fy": {"value": 235, "unit": "MPa"},
  "Fu": {"value": 370, "unit": "MPa"},
  "E": {"value": 200000, "unit": "MPa"},
  "source": "sample_data",
  "metadata": {
    "requires_independent_verification_before_design_use": true
  }
}
```

### `material.E` vs `analysis.E`
- If `analysis.E` exists, it is used explicitly.
- If `analysis.E` is absent and `material.E` exists, `material.E` is used.
- Existing `analysis.E` behavior remains valid and unchanged.

## `criteria_presets` block
- Optional top-level object.
- Optional arrays:
  - `deflection`
  - `stress`

### Deflection preset syntax
Each item may be:
- String preset ID: `"deflection_L_over_600"`
- Object:
```json
{"preset_id": "deflection_L_over_750", "limit_id": "custom_L_over_750"}
```

### Stress preset syntax
Each item may be:
- String preset ID: `"stress_0_66Fy"`
- Object with optional limit override and optional item-level `Fy` override:
```json
{
  "preset_id": "stress_0_90Fy",
  "limit_id": "custom_0_90Fy",
  "Fy": {"value": 250, "unit": "MPa"}
}
```

### Fy resolution for stress presets
For `fraction_of_Fy` stress presets:
1. Use item-level `Fy` if provided.
2. Else use top-level `material.Fy` if provided.
3. Else raise case I/O error indicating `Fy` is required.

## Coexistence with explicit limits
- Explicit `serviceability_limits` + preset-derived deflection limits are combined.
- Explicit `stress_limits` + preset-derived stress limits are combined.

## Limitations
- Generic preset references only.
- No official CIRSOC/CISC/AISC checks.
- No code compliance claims.
- Material values require independent verification before design use.
- No fatigue checks.
- No torsion/warping checks.
- No LTB checks.
