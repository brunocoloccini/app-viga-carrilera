# End-to-End Crane Runway Demo (V1-034)

## Purpose

This demo provides the first full, runnable crane-runway integration flow using existing modules only. It connects section assembly, load modeling, vertical/lateral analysis, serviceability checks, stress checks, torsional input generation, and text/Markdown reporting.

## Section construction

The section is assembled from the manually curated sample library file:

- `data/shape_libraries/cirsoc_sample_shapes.json`

Configuration:

- Base profile: `CIRSOC_IPN_200` as `LibraryShapeComponent` (`element_id="ipn_200"`) at `center_y=0 mm`, `center_z=100 mm`.
- Top cover plate: `PlateElement` (`element_id="cover_plate"`) with `width=140 mm`, `thickness=10 mm`.
- Assembly: `LineToLineJoin` from `cover_plate.bottom_edge` to `ipn_200.top_edge`.
- Connection metadata: `create_connection=True`, `interface_type="weld"`, `weld_type="fillet"`, `weld_size_mm=6`.

## Crane loading assumptions

Simple demo loading is defined for a `6 m` runway span:

- Two wheels.
- Wheel spacing: `2 m`.
- Wheel loads: `80 kN` vertical each.
- Wheel x positions: `0 mm`, `2000 mm`.
- `CraneLoadModel`:
  - `crane_id="demo_crane"`
  - `vertical_impact_factor=0.25`
  - `lateral_force_factor=0.10`
  - `longitudinal_force_factor=0.0`

Usage in analyses:

- Vertical analysis uses `factored_vertical_wheel_group()`.
- Lateral analysis uses `generated_lateral_wheel_group()`.

## Analyses performed

The demo runs:

1. Moving vertical global envelope (`SimpleSpanMovingLoadEnvelopeAnalyzer`, step `250 mm`).
2. Moving vertical station envelope curves (`SimpleSpanEnvelopeCurveAnalyzer`, movement `250 mm`, station `500 mm`).
3. Moving deflection envelope (`SimpleSpanMovingDeflectionEnvelopeAnalyzer`) with `E=200000 MPa` and section gross `Iyy`.
4. Vertical bending stress from vertical moving envelope.
5. Lateral fixed-position analysis and lateral bending stress.
6. Biaxial stress combination using representative vertical and lateral moments.

### Representative lateral-position assumption

For simplicity, the lateral wheel group is translated to the offset that produced maximum vertical moment (`max_moment_offset_x_mm`) when available; otherwise offset `0 mm` is used.

## Generic criteria checks

- Deflection serviceability: `DeflectionLimit.span_over("L_over_600", 600)`.
- Stress utilization: `StressLimit.fraction_of_Fy("0.66Fy", Fy=250 MPa, factor=0.66)` checked against biaxial stress.

## Torsional input model

Torsional input is generated (not stress-checked) with:

- `RailEccentricityModel`
  - `vertical_eccentricity_y = 25 mm`
  - `lateral_load_height_z = 100 mm`
  - `include_vertical = True`
  - `include_lateral = True`

A representative wheel group carrying both vertical and lateral wheel forces is used.

## Demand summary and reporting

The demo builds a `CraneRunwayDemandSummary` (via `CraneRunwayDemandSummaryBuilder`) and includes:

- gross properties
- vertical envelope
- envelope curves
- deflection envelope
- vertical stress
- lateral analysis
- lateral stress
- biaxial stress
- torsional load group
- serviceability result
- stress utilization result
- warnings

Reports are generated with `CraneRunwayDemandSummaryFormatter`:

- Plain text report
- Markdown report

The example script prints both reports and does not write output files by default.

## Limitations

- CIRSOC sample profile data is manually curated and must be independently verified.
- No CIRSOC design-code checks are performed.
- No fatigue check is performed.
- No torsional stress or warping stress checks are performed.
- No lateral-torsional buckling checks are performed.
- No rail/local component checks are performed.
- No UI is included.
- No PDF/DOCX export is included.
