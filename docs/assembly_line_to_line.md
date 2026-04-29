# Assembly: line-to-line join/alignment (V1-010)

## Purpose
`LineToLineJoin` performs geometric placement by rotating (optional) and translating a source component so one selected source reference line aligns with one target reference line.

This is geometric placement only:
- no boolean union,
- no overlap subtraction,
- no topological merge,
- no implied weld/bolt/contact/composite action.

## V1-010 behavior
Required options:
- `allow_rotation` (default `False`)
- `rotation_mode` (default `"align_direction"`)
- `alignment_mode` (default `"midpoint_to_midpoint"`)
- `overlap_mode` (default `"none"`)
- `normal_offset_mm`, `tangential_offset_mm`
- `reverse_source_direction`

If lines are non-parallel and `allow_rotation=False`, an `AssemblyGeometryError` is raised.
If `allow_rotation=True`, source is rotated to align its selected line direction with target line direction.

## Rotation convention
- Source angle = angle of source line direction.
- Target angle = angle of target line direction.
- Rotation = `target_angle - source_angle`.
- If `reverse_source_direction=True`, target angle is shifted by `+180°`.
- Rotation center is source line midpoint.

After rotation, source line is recomputed and translated to final aligned position.

## Alignment modes
- `midpoint_to_midpoint`
- `start_to_start`
- `end_to_end`
- `start_to_end`
- `end_to_start`

Unknown modes raise a clear error.

## Overlap modes (positioning only)
- `none`: use `alignment_mode`.
- `centered`: midpoint-to-midpoint.
- `from_target_start`: start-to-start.
- `from_target_end`: end-to-end.

For V1-010 these are line-positioning controls only (no geometric merge/cut).

## Offset convention in section Y-Z plane
Given target line unit tangent `t = (ty, tz)` and normal `n = (-tz, ty)`:

`final_target_point = base_alignment_point + tangential_offset_mm * t + normal_offset_mm * n`

Positive tangential offset moves along target `start -> end` direction.
Positive normal offset moves in left normal direction.

## Traceability metadata
Join result metadata stores assembly trace fields including:
- rotation angle and rotation center,
- alignment/overlap modes,
- offsets,
- translation components,
- source/target line lengths,
- note: `"No boolean merge or structural connection implied."`

## Future extension
- true topological/boolean merge,
- explicit weld/contact/interfacial modeling,
- overlap trimming/subtraction controls.
