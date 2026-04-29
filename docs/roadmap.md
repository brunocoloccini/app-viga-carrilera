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
