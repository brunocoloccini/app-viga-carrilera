# LibraryShapeComponent (V1-014)

`LibraryShapeComponent` lets the section model use **trusted tabulated properties** for structural shapes (for example W, IPE, HEA, UPN) instead of approximating them with a set of simple rectangles.

## Why this is needed

Rolled and tabulated profiles have published gross properties (area, `Iyy`, `Izz`, etc.) that should be treated as authoritative for gross elastic analysis. Rebuilding these shapes as rough rectangles introduces avoidable modeling error.

## Tabulated properties vs. reference geometry

A `LibraryShapeComponent` stores tabulated properties directly:
- area
- centroidal `Iyy`, `Izz`, `Iyz`
- optional supplemental fields (`J`, `Cw`, elastic section moduli, etc.)

At the same time, it exposes a simple **bounding-box reference geometry** (nodes/lines/points) to support placement and assembly operations (`NodeToNodeJoin`, `NodeToPointJoin`, `LineToLineJoin`).

Important: this reference box is **not** the true polygon of the rolled shape; it is only an assembly aid.

## How this prepares future profile libraries

This component is the foundation for future families and data sources:
- W
- IPE/IPN
- HEA/HEB
- UPN
- angles
- tubes
- custom profile catalogs/databases

## Current limitations in V1-014

- No built-in real profile database yet.
- Reference geometry is bounding-box based only.
- Component rotation is not supported yet (`rotation_deg` must be `0`).
- `transformed()` currently supports translation only.
- No plastic properties, torsional properties, or shear-center calculations yet.
