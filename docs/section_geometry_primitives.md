# Section geometry primitives

## Internal geometry convention (mm)

`section_core.geometry` stores geometric coordinates in internal **millimeters**. This keeps geometric operations deterministic and avoids mixed-unit ambiguity during comparisons and merging.

## Node vs SectionPoint vs SectionLine

- `Node`: generic coordinate carrier used by coordinate frames and topology-adjacent workflows.
- `SectionPoint`: section-builder point primitive with stable point identity (`point_id`) and optional source/metadata.
- `SectionLine`: segment connecting two `SectionPoint`s with topology-aware checks (parallelism, collinearity, containment, mergeability).

## GeometryTolerance role

`GeometryTolerance` centralizes geometric thresholds:

- point merge distance
- line merge gap
- parallel detection epsilon
- collinearity epsilon
- minimum non-degenerate segment length

This prevents hidden “magic numbers” in geometric logic.

## Why merges are tolerance-controlled

CAD/import pipelines and floating-point conversions introduce tiny coordinate noise. Strict exact comparisons often break expected line merging. Tolerance-controlled merge operations make geometric behavior robust while still rejecting truly distinct geometry.

## Preparation for Section Builder operations

These primitives prepare future section-building steps:

1. Node-to-node joining by point proximity.
2. Node-to-coordinate joining for snapping imported nodes onto explicit coordinates.
3. Collinear/overlapping segment consolidation for contour cleanup.
