# V1-019 Validation: CIRSOC IPN 200 + Top Cover Plate

## Purpose
This validation case verifies integrated behavior for a tabulated profile loaded from a manually curated CIRSOC sample JSON library and assembled with a top cover plate using `LineToLineJoin`.

The target use case is an early modeling step for crane runway-like sections composed of a rolled/tabulated profile plus a welded top plate.

## Source of Base Profile
The base profile is `CIRSOC_IPN_200` from:

- `data/shape_libraries/cirsoc_sample_shapes.json`

This is a **sample** library entry, not a complete production CIRSOC profile set.

## Manual-Curation Warning
The sample CIRSOC data is manually curated and includes metadata indicating it requires independent verification before production design use.

## Geometry
Base component (`LibraryShapeComponent`):

- `element_id = "ipn_200"`
- center: `y = 0 mm`, `z = 100 mm`
- depth = `200 mm`, width = `90 mm`
- bounding box:
  - `y_min = -45 mm`, `y_max = 45 mm`
  - `z_min = 0 mm`, `z_max = 200 mm`

Top cover plate (`PlateElement.horizontal_plate`):

- `element_id = "cover_plate"`
- width = `140 mm`
- thickness = `10 mm`
- assembled by joining plate `bottom_edge` to profile `top_edge`
- final bounding box:
  - `y_min = -70 mm`, `y_max = 70 mm`
  - `z_min = 200 mm`, `z_max = 210 mm`
- plate centroid: `z = 205 mm`

Final section bounding box:

- `y_min = -70 mm`, `y_max = 70 mm`
- `z_min = 0 mm`, `z_max = 210 mm`

## Assembly Sequence
1. Load JSON library and fetch `CIRSOC_IPN_200`.
2. Convert record to `LibraryShapeComponent` at `(0, 100) mm`.
3. Create top cover plate (`140 x 10 mm`).
4. Apply `LineToLineJoin` with:
   - source = `cover_plate.bottom_edge`
   - target = `ipn_200.top_edge`
   - `create_connection=True`
   - `interface_type="weld"`
   - `weld_type="fillet"`
   - `weld_size_mm=6`

## Weld Interface Recording
The case expects exactly one interface in the resulting section:

- weld type (`WeldInterface` or `interface_type="weld"`)
- references both `ipn_200` and `cover_plate`
- `verified = False`
- `structural_action_assumed = False` unless explicitly overridden
- metadata includes `created_by_operation_id`
- metadata note indicates interface is recorded, not structurally verified

## Combined-Property Formulas
Base tabulated values (after unit conversion):

- `A_base = 3340 mm2`
- `yc_base = 0`
- `zc_base = 100 mm`
- `Iyy_base = 21,400,000 mm4`
- `Izz_base = 1,170,000 mm4`
- `Iyz_base = 0`

Plate values:

- `A_plate = 140 * 10 = 1400 mm2`
- `yc_plate = 0`
- `zc_plate = 205 mm`
- `Iyy_plate_local = 140 * 10^3 / 12`
- `Izz_plate_local = 10 * 140^3 / 12`

Total area:

- `A_total = A_base + A_plate`

Centroid:

- `yc = 0`
- `zc = (A_base * zc_base + A_plate * zc_plate) / A_total`

About `y` axis:

- `Iyy_total = Iyy_base + A_base * (zc_base - zc)^2 + Iyy_plate_local + A_plate * (zc_plate - zc)^2`

About `z` axis:

- `Izz_total = Izz_base + Izz_plate_local`

Product inertia:

- `Iyz_total = 0`

Section moduli:

- `S_y_top = Iyy_total / (210 - zc)`
- `S_y_bottom = Iyy_total / (zc - 0)`
- `S_z_left = Izz_total / 70`
- `S_z_right = Izz_total / 70`

Expected behavior:

- `S_y_top != S_y_bottom` (monosymmetric in `z`)
- `S_z_left == S_z_right` (symmetric in `y`)

## Axis Mapping Note
For CIRSOC tabulated axes in this sample dataset:

- table `Ix` maps to app `Iyy`
- table `Iy` maps to app `Izz`

## Limitations
- Uses one sample profile (`CIRSOC_IPN_200`) only.
- No complete CIRSOC profile database yet.
- No design-code checks (including CIRSOC checks).
- No crane runway design checks.
- Weld is recorded as interface metadata, not strength-checked.
- No torsion or shear-center calculations.
- No boolean union / overlap subtraction.
