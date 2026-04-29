# Node-to-node join (V1-006)

## Purpose

`NodeToNodeJoin` is the first geometric assembly operation for Section Builder.
It places a new source component in a section by matching one source node to one target node that already exists in the section.

## Geometric placement only

This operation only moves geometry.

It **does not** imply:
- welds;
- bolts;
- rigid connectivity;
- composite action;
- standards/design-code checks.

## Translation formula

Given a source node `(y_s, z_s)` and target node `(y_t, z_t)` in internal mm:

- `dy = y_t - y_s`
- `dz = z_t - z_s`

The translated source component is created with that `(dy, dz)` shift and then added to the section.

## Traceability

The translated component metadata stores an `assembly` trace with:
- `operation_id`
- `operation_type = "node_to_node_join"`
- `source_component_id`
- `source_node_name`
- `target_component_id`
- `target_node_name`
- `translation_dy_mm`
- `translation_dz_mm`

## Relationship to future assembly modes

V1-006 covers only **node-to-node** assembly.
Future milestones will add:
- node-to-YZ-point join;
- line-to-line merge.
