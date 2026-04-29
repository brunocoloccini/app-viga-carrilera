# Shape Library Registry (V1-016)

`ShapeLibraryRegistry` stores tabulated structural profile data so it can be reused to instantiate section components.

## Purpose

- Keep profile-table records separate from section assembly instances.
- Support future profile sources (AISC W, IPE, IPN, HEA/HEB/IPB, UPN, channels, angles, tubes, and custom user libraries).
- Preserve a UI-independent core model.

## ShapeRecord vs LibraryShapeComponent

- `ShapeRecord`: immutable tabulated data row for one profile (`shape_id`, dimensions, area, inertias, optional section moduli, optional torsion constants, metadata).
- `LibraryShapeComponent`: an actual section component placed in a section with location and element id.

The registry bridges them through `to_component(...)`.

## Sample library in V1-016

V1-016 intentionally provides only a tiny in-code sample dataset:

- `W_TEST_600`
- `IPE_TEST_300`

These are **FAKE SAMPLE DATA ONLY** for tests/examples and are not real catalog values.

## Unit handling

`ShapeRecord.from_values(...)` performs explicit dimensional conversion to internal units:

- length -> mm
- area -> mm2
- inertia / J -> mm4
- section modulus -> mm3
- weight per length -> kg/m
- warping constant Cw -> mm6 (supported via explicit mm6/cm6/m6/in6/ft6 mapping)

Incompatible units are rejected with clear `InvalidShapeRecordError` messages.

## Why keep profile databases separate from section instances

- A profile table is a reusable reference dataset.
- A `Section` contains concrete placed components and assembly operations.
- Separation simplifies validation, serialization, and future import/export workflows.

## Future scope

Future versions can add richer tables and optional validation metadata for:

- CIRSOC
- AISC
- CISC
- European profile tables

## Current limitations

- No full profile database yet.
- No automatic PDF extraction.
- No design-code classification/checking yet.
- No torsion/shear-center calculations beyond stored optional fields.
