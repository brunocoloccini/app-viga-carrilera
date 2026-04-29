# Crane Runway Generic Criteria Presets (V1-046)

## Purpose
This module introduces reusable **generic preset infrastructure** for crane runway criteria.
It allows common criteria templates to be defined once and converted into existing runtime objects:
- `DeflectionLimit`
- `StressLimit`

## Generic presets vs. official design-code checks
These presets are convenience templates only.
They are **not** official code checks and do **not** imply compliance with any standard.

Specifically:
- Not CIRSOC-specific.
- Not CISC/AISC-specific.
- No resistance factors.
- No fatigue checks.
- No torsion/warping checks.
- No lateral-torsional buckling (LTB).
- No automatic code compliance determination.

## Supported preset types
- `deflection`
- `stress`

## Preset models
- `GenericCriteriaPreset`: common base fields (`preset_id`, `preset_type`, optional `description`, optional `metadata`).
- `DeflectionLimitPreset`: generic deflection template with supported `limit_type` values:
  - `span_divisor`
  - `absolute`
  - `minimum_of_span_divisor_and_absolute`
- `StressLimitPreset`: generic stress template with supported `limit_type` values:
  - `absolute`
  - `fraction_of_Fy`

## Registry
`CriteriaPresetRegistry` stores and manages preset collections:
- Deflection presets by `preset_id`
- Stress presets by `preset_id`

It provides add/get/list/has operations and conversion helpers:
- `to_deflection_limit(...)`
- `to_stress_limit(...)`

## Built-in generic preset registry
`build_generic_criteria_preset_registry()` returns a registry preloaded with generic presets:

Deflection:
- `deflection_L_over_600`
- `deflection_L_over_750`

Stress:
- `stress_0_66Fy`
- `stress_0_90Fy`

## Conversion and Fy handling
Deflection presets convert directly to `DeflectionLimit`.

Stress presets:
- `absolute` presets convert directly.
- `fraction_of_Fy` presets require `factor` and an `Fy` value.
- `Fy` can be stored in the preset (`Fy_internal_MPa`) or supplied at conversion time.
- If missing in both places, conversion raises a clear validation error.
