# Validation Case V1-012: Built-Up I Section with Weld Interfaces

## Purpose
This integrated validation case demonstrates that component geometry, assembly operations, interface recording, and gross elastic property calculations work together for a realistic built-up section workflow.

## Geometry
A symmetric built-up I section is assembled from three plates:
- Bottom flange: 200 mm × 20 mm
- Web: 10 mm × 300 mm
- Top flange: 200 mm × 20 mm

Final assembled extents:
- `y_min = -100 mm`, `y_max = 100 mm`
- `z_min = 0 mm`, `z_max = 340 mm`
- total depth = 340 mm
- centroid: `yc = 0 mm`, `zc = 170 mm`

## Assembly sequence
1. Create bottom flange in final position (`center_y=0`, `center_z=10`).
2. Create web at an initial convenient location.
3. Apply `LineToLineJoin` from web `bottom_edge` to bottom flange `top_edge` with `create_connection=True`, weld metadata (`weld_type="fillet"`, `weld_size_mm=6`).
4. Create top flange at an initial convenient location.
5. Apply `LineToLineJoin` from top flange `bottom_edge` to web `top_edge` with `create_connection=True`, same weld metadata.

Components remain separate; no boolean union is performed.

## Weld interface recording
Two interfaces are recorded in the section:
- bottom flange ↔ web
- web ↔ top flange

These interfaces are recorded as weld-type connections for traceability and coordination. They are explicitly marked as unverified by default (`verified=False`) and include metadata note: *Interface is recorded but not structurally verified.*

## Hand-calculated formulas and expected values
Area:
- `A = 2*(200*20) + (10*300) = 11000 mm²`

Centroid:
- `yc = 0 mm`
- `zc = 170 mm`

`Iyy` about centroidal y-axis:
- `A_flange = 4000 mm²`
- `Iyy_flange_local = 200*20^3/12`
- distance flange centroid ↔ section centroid: `160 mm`
- `Iyy_web_local = 10*300^3/12`
- `Iyy = 2*(Iyy_flange_local + A_flange*160^2) + Iyy_web_local`

`Izz` about centroidal z-axis:
- `Izz_flange_local = 20*200^3/12`
- `Izz_web_local = 300*10^3/12`
- `Izz = 2*Izz_flange_local + Izz_web_local`

Product inertia:
- `Iyz = 0` (symmetry about y-axis)

Section moduli:
- `S_y_top = Iyy / 170`
- `S_y_bottom = Iyy / 170`
- `S_z_left = Izz / 100`
- `S_z_right = Izz / 100`

## Limitations
- Components remain separate objects.
- Welds are recorded but not strength-checked.
- No boolean union or overlap subtraction.
- No local buckling classification.
- No torsional properties.
- No plastic properties.
- No CIRSOC checks at this stage.
