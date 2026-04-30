# Workflow/API Contract (V1-051)

This document defines the current public contract for workflow execution and reporting stability.

## Public package boundaries

Top-level public usage should import from `section_core` and rely on the following package areas:

- `units`: quantity and dimensional/unit conversion primitives.
- `materials`: steel material modeling (`SteelMaterial`) and sample builders.
- `rails`: crane rail records/registry and sample builders.
- `shapes`: shape records, registries, and JSON I/O helpers.
- `section`: section container and gross elastic section properties.
- `crane_runway`: load model, analyzers, criteria checks, workflows, case I/O, and reporting.

Avoid binding consumers to internal module paths where equivalent top-level exports are available.

## Internal unit conventions

Core internal conventions used in workflow and summaries:

- Length: `mm`
- Force: `N`
- Stress / modulus: `MPa`
- Moment / torsional input: `Nmm`
- Inertia: `mm4`
- Warping constant: `mm6`

Any public JSON/API inputs should be explicitly converted into internal units before analysis execution.

## Result/report consistency expectations

`CraneRunwayDemandSummary` is the canonical aggregate object for workflow demand/results exposure.

Contract expectations:

- Getter methods (`max_vertical_moment_Nmm()`, etc.) return scalar values or `None` when unavailable.
- `summary.to_dict()` must mirror getter/status values and include `warnings` and `metadata` payloads.
- Text, Markdown, and HTML reports must all include:
  - summary title,
  - identification (summary/case/load model context),
  - demand rows,
  - serviceability/stress/overall statuses,
  - warnings.
- Missing demand values are rendered as `N/A` in all report formats.
- Status mapping is semantically consistent across formats:
  - `True -> PASS`
  - `False -> FAIL`
  - `None -> N/A`

## Warnings and metadata expectations

- Warnings are list-based, deterministic, and surfaced in:
  - summary object,
  - `to_dict()`,
  - text/markdown/html outputs.
- Workflow metadata may include material-derived metadata (`material_id`, `Fy_internal_MPa`) when material inputs are provided.
- Warnings can include analysis-scope disclaimers (e.g., no design-code compliance checks).

## JSON case flow contract

Expected high-level execution flow for case files:

1. Validate case dictionary against schema/validation helpers.
2. Build workflow input from validated case payload.
3. Run `CraneRunwayCalculationWorkflow`.
4. Produce demand summary and deterministic text/markdown reports.
5. Optionally produce deterministic HTML summaries.

## Current limitations

Current implementation limitations (intentional scope boundaries):

- No official CIRSOC/CISC/AISC code-check implementation yet.
- No fatigue checks.
- No torsional/warping stress checks.
- No lateral-torsional buckling (LTB) checks.
- Sample/example datasets are for demonstration and require independent engineering verification.
