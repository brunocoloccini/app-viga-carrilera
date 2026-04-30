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

- V1-030: Generic elastic stress utilization criteria/checking layer for vertical, lateral, and biaxial stress demand vs configurable allowable stress limits.


- V1-031: Rail/load eccentricity torsional input model for crane runway beams (signed wheel torsional moments from vertical eccentricity and lateral load height).


## V1-032 - Crane Runway Demand Summary
- Add `CraneRunwayDemandSummary` as a reporting/aggregation object for key crane runway analysis outputs.
- Add pass/fail aggregation helpers and a basic JSON-serializable `to_dict()` export.
- Add `CraneRunwayDemandSummaryBuilder.build_basic_summary(...)` convenience constructor.

## V1-033 - Crane Runway Demand Summary Reporting
- Add a lightweight formatting layer (`reporting.py`) for converting `CraneRunwayDemandSummary` into text and Markdown outputs.
- Add deterministic engineering-unit conversions and fixed-precision presentation formatting.
- Add summary validation and reporting-specific errors for invalid formatting inputs.
- Add tests and documentation for report formatting behavior and limitations.

## V1-034 - End-to-End Crane Runway Demo and Integration Validation
- Add `examples/end_to_end_crane_runway_demo.py` as the first full workflow demo from section assembly through reporting.
- Add integration tests validating summary outputs, report content, and script execution.
- Add dedicated documentation describing assumptions, analysis scope, and limitations.

## V1-035 - Crane Runway High-Level Calculation Workflow
- Add `workflow.py` orchestrator to execute full crane runway analysis sequence and produce demand summary + text/markdown reports.
- Add workflow input/output data models with unit-aware factory and validation.
- Add dedicated workflow tests and documentation for assumptions and limitations.


## V1-036 - Crane Runway Case JSON I/O
- Add `case_io.py` to load/dump crane runway case JSON files, validate required fields, and parse explicit quantity payloads.
- Add conversion/build/run helpers that map case dictionaries into `CraneRunwayWorkflowInput` and execute `CraneRunwayCalculationWorkflow`.
- Add case input/result dataclasses, user-facing error types, example case + script, documentation, and tests.

## V1-037 - Versioned Crane Runway Case Schema and Validation
- Add `case_schema.py` with versioned schema constants, validation issue/result dataclasses, and strict/non-strict validators.
- Integrate schema validation into `case_io.py` run paths before workflow execution.
- Export a JSON-schema-like V1 document and add schema-focused tests + documentation.


## V1-038 - Crane Runway Demo Golden Regression Outputs
- Add golden baseline files for demo case summary JSON and markdown report under `examples/golden/`.
- Add regression tests that compare key summary demands/check flags and report output against the golden baselines.
- Add update script + documentation for intentional golden refresh workflow and limitations.

## V1-039 - Crane Runway Scenario Matrix Demo Cases and Regression
- Add a compact matrix of demo JSON cases under `examples/cases/` covering baseline, no-cover-plate, no-rail-eccentricity, intentional deflection fail, and intentional stress fail variants.
- Add scenario matrix tests that strictly validate each case schema and execute each case through `run_crane_runway_case_json` with deterministic expected status checks.
- Add scenario matrix documentation describing scope, intent, relation to V1-038 golden regression, and engineering limitations.


- V1-040: Add user-facing validation error formatting for crane runway case files.


- V1-041: Add CLI-style crane runway JSON case validator script with strict/non-strict and JSON/text outputs, plus tests and documentation.


- V1-042: Add CLI-style crane runway JSON case execution script with text/markdown/both/summary-json outputs, optional file output, tests, and documentation.


- V1-043: Add static HTML export for crane runway demand summaries, integrate `--html` mode in case execution CLI, and add tests/documentation for deterministic escaped report output.

- V1-044: Add deterministic HTML golden baseline for the crane runway demo case, extend golden update script, and add CLI/formatter regression tests plus documentation updates.

- V1-045: Add static HTML scenario-matrix index reporting (`matrix_reporting.py`), expose matrix reporting models/formatter, add CLI `--html`/`--output` support in case matrix runner, and add tests/documentation.

- V1-046: Add generic criteria preset architecture for crane runway checks, including preset dataclasses, registry operations, built-in generic presets, conversion helpers, tests, and documentation.

- V1-047: Add reusable steel material data modeling package (`section_core.materials`) with `SteelMaterial`, validated unit-aware factory conversion for stress/modulus values, and sample steel grades (F24/F36) for non-code-compliance demo use.


- V1-048: Extend crane runway case schema/case I/O with optional JSON `material` blocks and `criteria_presets` references, including preset-to-limit conversion, material-aware Fy resolution, example case, and tests/documentation updates.

- V1-049: Expand manually curated CIRSOC sample shape library with additional IPN records (IPN 180, 240, 300), plus validation tests and documentation updates.

- V1-050: Add dedicated crane rail data model (`CraneRailRecord`), rail registry (`CraneRailRegistry`), and fake sample rail dataset (`RAIL_TEST_A`, `RAIL_TEST_B`) for future library and runway integration.

- V1-051: Add public API export, workflow consistency, and reporting consistency contract tests; document workflow/API boundaries and result/report determinism expectations.


- V1-052: Add report package export layer for crane runway case execution, including deterministic artifact folder writing, CLI integration (`--package-output`, `--overwrite-package`), tests, and documentation.

- V1-053: Add a minimal pure-Python crane runway local API service boundary (`api_service.py`) for dict/JSON-text validation + execution with structured response dataclasses, optional output format selection, tests, and documentation.
