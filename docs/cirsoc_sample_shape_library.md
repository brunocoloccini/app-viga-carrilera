# CIRSOC Sample Shape Library (V1-049)

## Purpose

This document describes a **small, manually curated** CIRSOC sample shape library used to validate that real tabulated profile data can be represented safely in JSON with explicit units and traceable provenance.

This dataset is intentionally limited to validation and test coverage.

## Scope and status

- Manually curated: **yes**.
- Full production CIRSOC profile database: **no**.
- Independent verification before production design use: **required**.

## Source traceability

Source metadata is included per record:

- `source_document`: `CIRSOC tablas perfiles.pdf`
- `source_table`:
  - `IPN según IRAM-IAS U 500-511`
  - `IPB según IRAM-IAS U 500-215-2`
- `source`: `CIRSOC 301-EL / 302-EL Tablas de Perfiles`

## Units and conversions

The source tables provide values in mixed units including:

- geometry in `mm`
- area in `cm2`
- moments of inertia and torsion constant `J` in `cm4`
- warping constant `Cw` in `cm6`
- weight per length in `kg/m`

On import, the package converts to internal units for section computations:

- `area -> mm2`
- `Iyy/Izz/Iyz/J -> mm4`
- `Cw -> mm6`

`Cw` is handled as `warping_constant` with internal `mm6` units.
`J` is handled as an inertia-like torsion constant with internal `mm4` units.

## Axis mapping convention

For this sample, the tabulated axis names are mapped explicitly in metadata:

- table `Ix` maps to app `Iyy`
- table `Iy` maps to app `Izz`

This mapping is stored as:

- `axis_mapping.table_Ix_maps_to = "Iyy_mm4"`
- `axis_mapping.table_Iy_maps_to = "Izz_mm4"`

## Included profiles

Only a few sample records are included:

- `CIRSOC_IPN_180`
- `CIRSOC_IPN_200`
- `CIRSOC_IPN_240`
- `CIRSOC_IPN_300`
- `CIRSOC_IPB_200`

## Limitations

- Small manually curated sample library only.
- Not a complete CIRSOC profile database.
- No automatic PDF extraction.
- No design-code checks.
- No section classification checks.
- No torsion/shear-center calculations beyond storing tabulated `J` and `Cw` values.
