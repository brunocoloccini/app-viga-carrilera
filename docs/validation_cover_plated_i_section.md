# Validation Case V1-013: Cover-Plated Monosymmetric I Section

## Purpose
This integrated validation case extends the built-up I workflow by adding a top cover plate, representing a simplified first step toward crane runway beam-like sections (I/W section + top cover plate) while staying limited to gross elastic properties.

## Why this section is monosymmetric
The section remains symmetric about the vertical z-axis because all plates are centered at `y=0`, but it is not symmetric about the horizontal y-axis due to the extra top cover plate. Therefore, `S_y_top` and `S_y_bottom` are different.

## Geometry
- Bottom flange: `200 mm × 20 mm`
- Web: `10 mm × 300 mm`
- Top flange: `200 mm × 20 mm`
- Top cover plate: `260 mm × 10 mm`

Final assembled extents:
- `y_min = -130 mm`, `y_max = 130 mm`
- `z_min = 0 mm`, `z_max = 350 mm`
- total depth = `350 mm`

## Assembly sequence
1. Place bottom flange directly at final position (`center_y=0`, `center_z=10`).
2. Place web at an initial convenient location.
3. Join web `bottom_edge` to bottom flange `top_edge` via `LineToLineJoin` with `create_connection=True` and weld metadata.
4. Place top flange at an initial convenient location.
5. Join top flange `bottom_edge` to web `top_edge` via `LineToLineJoin` with `create_connection=True` and weld metadata.
6. Place top cover plate at an initial convenient location.
7. Join cover plate `bottom_edge` to top flange `top_edge` via `LineToLineJoin` with `create_connection=True` and weld metadata.

Components remain separate. No boolean union is performed.

## Weld interface recording
Three weld interfaces are recorded:
- bottom flange ↔ web
- web ↔ top flange
- top flange ↔ cover plate

Interfaces are tracking objects only at this stage:
- `verified=False`
- `structural_action_assumed=False`
- metadata includes operation id and the note that the interface is recorded but not structurally verified.

## Hand-calculated formulas
Area:
- `A_bottom = 200*20`
- `A_web = 10*300`
- `A_top = 200*20`
- `A_cover = 260*10`
- `A_total = A_bottom + A_web + A_top + A_cover`

Centroid:
- `yc = 0`
- `zc = sum(Ai*zi) / sum(Ai)` with `zi = [10, 170, 330, 345] mm`

`Iyy` about centroidal y-axis:
- `Iyy_i = b*h^3/12`
- `Iyy = sum(Iyy_i + Ai*(zi-zc)^2)`

`Izz` about centroidal z-axis:
- `Izz_i = h*b^3/12`
- all components centered at `y=0`, so `Izz = sum(Izz_i)`

`Iyz`:
- expected `Iyz = 0` (symmetry about z-axis)

Section moduli:
- `S_y_top = Iyy / (z_max - zc)`
- `S_y_bottom = Iyy / (zc - z_min)`
- `S_z_left = Izz / (yc - y_min)`
- `S_z_right = Izz / (y_max - yc)`

## Expected behavior
- `zc > 170 mm` because the cover plate is above the original symmetric I section centroid.
- `S_y_top != S_y_bottom` due to monosymmetry.
- `S_z_left = S_z_right` due to y-axis symmetry.

## Limitations
- Components remain separate.
- Welds are recorded but not checked for strength.
- No boolean union or overlap subtraction.
- No local buckling classification.
- No torsion.
- No shear center.
- No plastic properties.
- No CIRSOC checks yet.
