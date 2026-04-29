# Steel materials (V1-047)

## Purpose
`SteelMaterial` provides a reusable, validated steel material data object for section-core workflows.
It is intentionally focused on data modeling only so it can be reused later by JSON case I/O, stress criteria presets, and future code-specific checks.

## Internal units
- `Fy_internal_MPa`, `Fu_internal_MPa`, and `E_internal_MPa` are stored in **MPa**.
- `density_internal_kg_per_m3` is stored in **kg/m3** when provided.

## Factory usage
Use `SteelMaterial.from_values(...)` for explicit dimensional conversion of stress/modulus values through `Quantity` and `UnitRegistry` (`Dimension.STRESS`).

Examples:
- MPa input: `SteelMaterial.from_values(material_id="A", Fy=250, Fy_unit="MPa", E=200000, E_unit="MPa")`
- ksi input: `SteelMaterial.from_values(material_id="B", Fy=50, Fy_unit="ksi", E=29000, E_unit="ksi")`

Density handling in V1-047 is intentionally minimal:
- If density is supplied, raw `kg/m3` is accepted.
- `density_unit` may be omitted or set to `"kg/m3"`.
- Any other density unit raises `InvalidMaterialError`.

## Sample materials helper
`build_sample_steel_materials()` returns sample materials including:
- `F24`: Fy=235 MPa, Fu=370 MPa, E=200000 MPa
- `F36`: Fy=355 MPa, Fu=510 MPa, E=200000 MPa

Each sample includes metadata flags:
- `sample_material: true`
- `requires_independent_verification_before_design_use: true`
- `not_official_complete_material_library: true`

## Sample data limitations
These values are sample placeholders only, and are not an official complete steel material library.
Independent engineering verification is required before design use.

## Future intended use
- JSON case material blocks
- Stress criteria presets
- Code-specific checks in future milestones

## Current limitations (explicit)
- Not an official material library
- No CIRSOC/CISC/AISC checks
- No resistance factors
- No fatigue modeling
- No temperature/fire/corrosion modeling
- Density unit conversion intentionally minimal in V1-047
