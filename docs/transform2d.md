# Transform2D (V1-009)

`Transform2D` applies translation + rotation in the **Y-Z section plane** (internal units: mm).

## Conventions
- Coordinates are `(y, z)` in the section plane.
- Positive rotation is counterclockwise in the Y-Z plane.
- Rotation is around `(rotation_center_y_mm, rotation_center_z_mm)`.

## Fields
- `translation_dy_mm`
- `translation_dz_mm`
- `rotation_deg`
- `rotation_center_y_mm`
- `rotation_center_z_mm`

## Local vs global axes for rectangles
`RectangularElement.width_internal_mm` and `height_internal_mm` are local rectangle dimensions.
Rotation changes the global corner/node positions, reference lines, and axis-aligned bounding box, but not area or centroid location (except translation).

## Current limitation
`Section.gross_elastic_properties()` raises an explicit error when any component has `rotation_deg != 0`.
Rotated-rectangle inertia contributions are intentionally deferred to a future milestone to avoid silent wrong results.

## Why this matters
This adds a robust transform foundation for future assembly operations, including rotation-capable line-to-line alignment and partial-overlap controls.
