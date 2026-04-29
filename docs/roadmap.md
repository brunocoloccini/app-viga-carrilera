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

- V1-015: Integrated validation case for a tabulated library I/W-like shape plus a top cover plate assembled with `LineToLineJoin`, with one weld interface recorded and gross elastic properties verified against hand calculations.

- V1-016: Basic ShapeLibraryRegistry and ShapeRecord for tabulated profiles, including a tiny fake sample dataset and registry-to-component conversion.


- V1-017: JSON import/export for tabulated shape libraries with explicit quantity units, validation, and roundtrip file/dict support.


- V1-018: Manually curated CIRSOC sample shape library JSON (IPN 200 and IPB 200) with explicit unit conversion tests, metadata traceability, and section integration checks.

- V1-019: Integrated validation case for a manually curated CIRSOC sample IPN 200 profile plus a top cover plate assembled with `LineToLineJoin`, with weld interface recording and gross elastic properties verified against hand calculations.

- V1-020: Basic crane runway load modeling package (`section_core.crane_runway`) with wheel loads, wheel groups, generated impact/lateral/longitudinal cases, and validation.


- V1-021: Simple-span crane runway beam analysis for fixed wheel positions (reactions, shear, moment) in `section_core.crane_runway.analysis`.

- V1-022: Moving wheel-load envelope for simple-span crane runway beams (vertical wheel loads only, step-based position scan).

- V1-023: Station-based shear and bending-moment envelope curves for moving wheel groups on simple-span crane runway beams.


- V1-024: Simple-span fixed-position elastic vertical deflection analysis for crane runway beams (vertical wheel loads only).


- V1-025: Moving-load vertical deflection envelope for simple-span crane runway beams (grid-based moving offsets and station envelope sampling).


- V1-026: Configurable serviceability criteria/checking model for vertical crane runway deflection (span/N, absolute, and minimum-combined limits).


- V1-027: Elastic vertical bending stress calculation for crane runway beams from max moments and gross section properties (fixed, moving-envelope, and station-envelope workflows).


- V1-028: Simple-span lateral wheel-load analysis and elastic lateral bending stress using weak-axis section moduli (`S_z_left_mm3`, `S_z_right_mm3`) in `section_core.crane_runway.lateral_analysis`.

- V1-029: Elastic biaxial stress combination for crane runway beams (My/Sy + Mz/Sz) at representative corner fibers; stress calculation only (no code checks).
