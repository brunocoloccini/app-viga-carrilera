# Roadmap

Planned modules:
- units
- coordinates
- geometry
- components
- assembly
- elastic section properties
- plastic section properties
- torsion properties
- JSON import/export
- validation cases


## Milestones
- V1-004: Component primitives (`SectionElement`, `RectangularElement`, `PlateElement`) in `section_core.components`.

- V1-005: Section container and gross elastic properties for rectangular/plate components in `section_core.section`.

- V1-006: Assembly node-to-node join (`AssemblyOperation`, `NodeToNodeJoin`) in `section_core.assembly`.

- V1-007: Assembly node-to-point join (`NodeToPointJoin`) in `section_core.assembly`.


- V1-008: Assembly line-to-line join/alignment (`LineToLineJoin`) in `section_core.assembly`.

- V1-009: Transform2D and rotation-capable rectangle/plate geometry foundation (gross inertias for rotated components deferred).

- V1-010: Rotation-capable line-to-line assembly with alignment/overlap positioning controls (`LineToLineJoin`) in `section_core.assembly`.

- V1-011: Component interface models (weld/contact/shared-boundary/construction-joint/bolt-group) with Section and line-to-line integration.

- V1-012: Integrated validation case for a symmetric built-up I section assembled with `LineToLineJoin`, with weld interfaces recorded and gross elastic properties verified against hand calculations.

- V1-013: Integrated validation case for a monosymmetric cover-plated built-up I section assembled with `LineToLineJoin`, with weld interfaces recorded and gross elastic properties verified against hand calculations.

- V1-014: LibraryShapeComponent (tabulated structural shape properties + bounding-box reference geometry) with gross elastic property integration in `section_core.section`.
