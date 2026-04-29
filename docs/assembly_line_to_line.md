# Assembly: line-to-line join/alignment (V1-008)

## Purpose
`LineToLineJoin` performs geometric alignment by translating a source component so one of its reference lines aligns to a reference line in a target component already in the section.

This is geometric placement only:
- no boolean union,
- no overlap subtraction,
- no material-region merge,
- no implied weld/bolt/contact/composite action.

## V1-008 behavior
- Supported mode: `midpoint_to_midpoint`.
- Translation only (rigid-body shift in Y-Z).
- Rotation is **not** implemented. Non-parallel/anti-parallel line pairs raise an `AssemblyGeometryError`.

## Offset convention in section Y-Z plane
Given target line unit tangent `t = (ty, tz)` and normal `n = (-tz, ty)`:

- target alignment point = `target_midpoint + tangential_offset_mm * t + normal_offset_mm * n`
- source alignment point = `source_midpoint`
- translation:
  - `dy = target_alignment_y - source_midpoint_y`
  - `dz = target_alignment_z - source_midpoint_z`

Positive tangential offset moves along the target line direction (`start -> end`).
Positive normal offset moves using the left-hand normal `(-tz, ty)`.

## Typical uses
- cover plate positioning,
- flange/web/stiffener positioning,
- assembling box-like built-up sections while keeping components separate.

## Future extensions
- rotation-capable alignment,
- partial-overlap positioning controls,
- true topological merge/boolean operations,
- explicit weld/interface modeling.
