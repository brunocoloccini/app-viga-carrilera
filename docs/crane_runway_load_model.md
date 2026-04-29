# Crane runway load model (V1-020)

This package introduces a **load-modeling-only** foundation for overhead crane runway problems in `section_core.crane_runway`.

## Purpose

- Represent crane wheel loads with explicit units and validation.
- Group wheels into reusable wheel sets.
- Build basic nominal and generated load cases (vertical, impact-amplified, lateral, longitudinal).

## Scope boundary

This is **not** structural analysis. It does not compute:
- moving load envelopes;
- span reactions;
- beam shear/moment;
- fatigue cycles;
- design-code checks (CIRSOC/CISC/AISC).

## Coordinate and internal units

- Wheel coordinate `x` is along the runway beam span.
- Internal length unit is **mm**.
- Internal force unit is **N**.

## Model behavior

- `vertical_impact_factor`: each wheel vertical force is multiplied by `(1 + factor)`.
- `lateral_force_factor`: if provided, lateral force is generated as `factor * wheel_vertical_force` per wheel.
- `longitudinal_force_factor`: if provided, longitudinal force is generated from `factor * total_vertical_force`, then **distributed equally across all wheels**.

## Notes

- Unit validation is explicit via the existing `Quantity`/`UnitRegistry` pattern.
- The model is intended as a stable base for future runway analysis modules.
