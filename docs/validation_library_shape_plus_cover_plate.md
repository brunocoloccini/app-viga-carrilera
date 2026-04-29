# Validation: Library shape plus top cover plate (V1-015)

## Purpose
This integrated validation case demonstrates a mixed-component section where the base profile is modeled as a tabulated library shape and the top cover plate is modeled geometrically. It is a simplified precursor to crane runway beam-like configurations such as `W610x217 + top cover plate`.

## Why tabulated base shapes are useful
Tabulated shapes allow fast section modeling when trusted catalog properties are known in advance. This avoids reconstructing every flange/web detail for early-stage section composition workflows while keeping assembly and interface tracking available.

## Component definitions
- Base shape (`LibraryShapeComponent`):
  - `shape_family="W_TEST"`, `shape_name="W_TEST_600"`
  - `depth=600 mm`, `width=200 mm`
  - `A=30000 mm2`, `Iyy=1_800_000_000 mm4`, `Izz=90_000_000 mm4`, `Iyz=0`
  - centroid at `(y=0, z=300) mm`
  - reference bounding box from `y=-100..100 mm`, `z=0..600 mm`
- Top cover plate (`PlateElement.horizontal_plate`):
  - `width=300 mm`, `thickness=20 mm`
  - after assembly occupies `y=-150..150 mm`, `z=600..620 mm`
  - centroid at `z=610 mm`

## Assembly sequence
1. Create a section with the base tabulated shape.
2. Create the top cover plate.
3. Apply `LineToLineJoin` from cover plate `bottom_edge` to base shape `top_edge` with:
   - `create_connection=True`
   - `interface_type="weld"`
   - `weld_type="fillet"`
   - `weld_size_mm=6`

Components remain separate (no boolean union or overlap subtraction).

## Weld interface recording
The join records a weld interface between base shape and cover plate. It is metadata-level connectivity used for assembly traceability:
- interface type weld;
- `verified=False` by default;
- no weld strength verification performed in this validation.

## Combined property formulas
Let:
- Base: `A_base=30000`, `yc_base=0`, `zc_base=300`, `Iyy_base=1_800_000_000`, `Izz_base=90_000_000`, `Iyz_base=0`
- Plate: `A_plate=300*20=6000`, `yc_plate=0`, `zc_plate=610`
- `Iyy_plate_local = 300*20^3/12`
- `Izz_plate_local = 20*300^3/12`

Then:
- `A_total = A_base + A_plate`
- `yc = 0`
- `zc = (A_base*zc_base + A_plate*zc_plate) / A_total`
- `Iyy_total = Iyy_base + A_base*(zc_base-zc)^2 + Iyy_plate_local + A_plate*(zc_plate-zc)^2`
- `Izz_total = Izz_base + Izz_plate_local` (both centered at `y=0`)
- `Iyz_total = 0`

Section moduli:
- `S_y_top = Iyy / (620 - zc)`
- `S_y_bottom = Iyy / (zc - 0)`
- `S_z_left = S_z_right = Izz / 150`

Expected behavior includes `S_y_top != S_y_bottom` and `S_z_left = S_z_right`.

## Limitations
- Uses a fake test shape, not a real `W610` entry.
- No steel profile database is implemented here.
- Base-shape bounding box is reference geometry only.
- Components remain separate (no geometric merge).
- Weld is recorded but not structurally checked.
- No boolean union or overlap subtraction.
- No plastic properties.
- No torsional properties or shear-center calculations.
- No CIRSOC/design-code checks yet.
