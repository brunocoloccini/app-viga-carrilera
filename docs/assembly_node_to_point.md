# Node-to-point join (V1-007)

## Purpose

`NodeToPointJoin` is the second geometric assembly operation for Section Builder.
It places a source component by matching one source node to a target Y-Z point.

## Supported target definitions

Target point may be provided as:
- `SectionPoint`;
- `Point2D`;
- `Node`;
- explicit Y/Z coordinate values through `NodeToPointJoin.to_coordinates(...)` with units.

## Geometric placement only

This operation only translates geometry.

It **does not** imply:
- welds;
- bolts;
- structural connection behavior;
- composite action;
- code checks (including CIRSOC).

## Translation formula

Given source node `(y_s, z_s)` and target point `(y_t, z_t)` in internal mm:

- `dy = y_t - y_s`
- `dz = z_t - z_s`

A translated copy of the source component is created and added to the section.

## Unit handling for explicit coordinates

When using `to_coordinates`, both `y_unit` and `z_unit` must be length units (for example `mm`, `cm`, `in`, `m`).
Non-length units (for example `kN`, `MPa`) are rejected.

## Traceability

The translated component metadata includes an `assembly` trace with:
- `operation_id`
- `operation_type = "node_to_point_join"`
- `source_component_id`
- `source_node_name`
- `target_y_internal_mm`
- `target_z_internal_mm`
- `translation_dy_mm`
- `translation_dz_mm`
- `target_point_id` (if available)

## Typical use cases

- placing stiffeners relative to a known section point;
- placing cover plates using measured repair coordinates;
- existing-section modifications from survey coordinates.
