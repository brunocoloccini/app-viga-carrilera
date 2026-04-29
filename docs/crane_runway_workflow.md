# Crane Runway Workflow (V1-035)

This module adds a reusable high-level workflow layer for crane runway calculations. It orchestrates existing low-level analyzers into one application-facing operation that can be called by future API/UI layers without embedding engineering sequencing logic in those layers.

## Low-level analyzers vs high-level workflow

- **Low-level analyzers** compute one thing (moving-load envelope, deflection envelope, stress, criteria check).
- **High-level workflow** coordinates the full sequence and returns a single summary plus reports.

## Inputs

`CraneRunwayWorkflowInput` includes:
- span, section, crane load model;
- movement and station discretization steps;
- elastic modulus `E`;
- optional serviceability limits;
- optional stress limits;
- optional rail eccentricity model;
- optional warnings/metadata.

A unit-aware `from_values(...)` constructor accepts engineering units and converts to internal units.

## Sequence

1. Section gross properties.
2. Nominal/factored-vertical/lateral wheel groups.
3. Vertical moving load envelope.
4. Envelope curves.
5. Moving deflection envelope.
6. Optional serviceability checks.
7. Vertical stress.
8. Lateral analysis using representative vertical critical offset.
9. Lateral stress.
10. Biaxial stress combination.
11. Optional stress criteria checks.
12. Optional torsional load input from rail eccentricity model.
13. Demand summary build.
14. Text and Markdown report generation.

## Outputs

`CraneRunwayWorkflowResult` returns:
- workflow id;
- `CraneRunwayDemandSummary`;
- text report;
- markdown report;
- metadata.

## Assumptions

- Lateral wheel group uses a representative position based on vertical critical offset.
- Biaxial combination may use same-section simplification from independent vertical/lateral peaks.

## Limitations

- No CIRSOC design-code checks.
- No fatigue checks.
- No torsional/warping stress checks.
- No LTB checks.
- No PDF/DOCX export.
- No UI.
