# Crane Runway Reporting (V1-033)

## Purpose

This module adds a lightweight report-preparation layer for converting `CraneRunwayDemandSummary` outputs into deterministic, human-readable formats.

It is presentation-only and does not alter demand calculations, checks, or design logic.

## Relationship to `CraneRunwayDemandSummary`

The formatter consumes existing summary objects and reads key demand/check values through summary members and helper methods:

- `span_internal_mm`
- `max_vertical_moment_Nmm()`
- `max_vertical_shear_abs_N()`
- `max_vertical_deflection_mm()`
- `max_lateral_moment_Nmm()`
- `max_biaxial_stress_MPa()`
- `max_torsional_input_Nmm()`
- aggregate pass/fail helpers and warnings

## Output formats

- Plain text: concise line-by-line summary for logs and simple reports.
- Markdown: structured report with sections and tables for report assembly workflows.

## Engineering unit conversions (presentation only)

The formatter applies simple internal conversions for readability:

- `span_internal_mm` → m using `1 m = 1000 mm`
- moments `Nmm` → `kN·m` using `1 kN·m = 1,000,000 Nmm`
- shear `N` → `kN` using `1 kN = 1000 N`
- deflection kept in `mm`
- stress kept in `MPa`

These conversions are local to reporting output. No core unit registry changes are required.

## Deterministic precision

All reported numeric values use fixed precision:

- span: 3 decimals in m
- forces: 3 decimals in kN
- moments: 3 decimals in kN·m
- deflection: 3 decimals in mm
- stress: 3 decimals in MPa
- utilization values (when shown): 3 decimals

## Current limitations

- No PDF export.
- No DOCX export.
- No UI.
- No normative report templates.
- No CIRSOC-specific memory format yet.
