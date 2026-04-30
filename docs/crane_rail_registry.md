# Crane Rail Registry

## Purpose
`CraneRailRecord` is a dedicated data model for crane rail section properties.
`CraneRailRegistry` stores and retrieves rail records by `rail_id` for future crane runway workflows.

## Why separate from `ShapeRecord`
Crane rails are modeled separately from structural `ShapeRecord` entries so runway workflows can evolve rail-specific metadata and checks without coupling to generic structural shape libraries.

## Internal units
All internal values are stored in:
- length: `mm`
- area: `mm2`
- inertia: `mm4`
- section modulus: `mm3`
- mass per length: `kg/m`

## Sample registry
`build_sample_crane_rail_registry()` provides two records:
- `RAIL_TEST_A`
- `RAIL_TEST_B`

⚠️ **Warning:** `RAIL_TEST_A` and `RAIL_TEST_B` are fake test records only. They are not real crane rail catalog profiles and must not be used as authoritative design data.

## Future use
This model is intended to support future additions such as:
- manually curated real crane rail libraries,
- rail selection utilities,
- rail eccentricity configuration,
- rail local checks,
- rail attachment checks.

## Current limitations
- No real rail catalog data yet.
- No rail design checks.
- No fatigue checks.
- No torsion/warping checks.
- No UI integration.
