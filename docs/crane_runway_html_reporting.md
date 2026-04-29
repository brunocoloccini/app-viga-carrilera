# Crane Runway HTML Reporting (V1-043)

## Purpose
`section_core.crane_runway.html_reporting` adds deterministic static HTML export for `CraneRunwayDemandSummary`.

It complements existing text/Markdown reporting and reuses the same demand units and fixed precision.

## Output structure
The formatter produces a full HTML document with:
- `<!doctype html>`;
- `html/head/body`;
- embedded lightweight CSS;
- title + H1: `Crane Runway Demand Summary`;
- Identification table;
- Demands table;
- Checks table;
- optional Serviceability Checks and Stress Criteria Checks tables;
- Warnings section.

## Escaping and safety
User-provided fields are escaped with `html.escape`, including summary identifiers, check identifiers, warnings, and rendered metadata values.

## Units and precision
Demand values follow existing reporting behavior:
- span: m;
- vertical/lateral/torsional moments: kN·m;
- vertical shear: kN;
- deflection: mm;
- biaxial stress: MPa;
- fixed precision with deterministic formatting;
- missing values render `N/A`.


## Regression coverage
The demo HTML output for `examples/crane_runway_case_demo.json` is covered by golden regression in `tests/test_crane_runway_html_golden_regression.py` against `examples/golden/crane_runway_case_demo_golden_report.html`.

## Limitations
- Static HTML only.
- No PDF export.
- No DOCX export.
- No UI.
- No normative report template generation.
- No CIRSOC-specific checks.
