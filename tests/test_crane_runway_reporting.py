from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.assembly import LineToLineJoin
from section_core.crane_runway import (
    CraneLoadModel,
    CraneRunwayDemandSummary,
    CraneRunwayDemandSummaryBuilder,
    CraneRunwayDemandSummaryFormatter,
    CraneWheelGroup,
    DeflectionLimit,
    DeflectionServiceabilityChecker,
    ElasticBiaxialStressAnalyzer,
    ElasticStressCriteriaChecker,
    InvalidReportSummaryError,
    RailEccentricityModel,
    SimpleSpanMovingDeflectionEnvelopeAnalyzer,
    SimpleSpanMovingLoadEnvelopeAnalyzer,
    SimpleSpanRunwayBeamLateralAnalyzer,
    StressLimit,
    WheelLoad,
)


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def _build_section() -> Section:
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)
    ipn_200 = registry.to_component("CIRSOC_IPN_200", element_id="ipn_200", center_y=0, center_z=100, center_unit="mm")
    cover_plate = PlateElement.horizontal_plate(
        element_id="cover_plate",
        width=140,
        width_unit="mm",
        thickness=10,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=0,
        center_z_unit="mm",
    )
    section = Section(section_id="V1-033", components=[ipn_200])
    return LineToLineJoin(
        operation_id="OP_COVER_TO_IPN200",
        operation_type="ignored",
        source_component=cover_plate,
        source_line_name="bottom_edge",
        target_component_id="ipn_200",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_type="fillet",
        weld_size_mm=6,
    ).apply(section)


def _build_integration_summary() -> CraneRunwayDemandSummary:
    wheels = _group([WheelLoad.from_values("W1", 2, "m", 50, "kN"), WheelLoad.from_values("W2", 8, "m", 50, "kN")])
    model = CraneLoadModel(crane_id="C1", wheel_group=wheels, lateral_force_factor=0.1)
    vertical_group = model.nominal_wheel_group()
    lateral_group = model.generated_lateral_wheel_group()

    vertical_env = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(10, "m", step=1, step_unit="m").analyze_envelope(vertical_group)
    defl_env = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10,
        span_unit="m",
        E=200_000,
        E_unit="MPa",
        I=2.0e8,
        I_unit="mm4",
        movement_step=1,
        movement_step_unit="m",
        station_step=1,
        station_step_unit="m",
    ).analyze_envelope(vertical_group)
    lat_result = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(lateral_group)

    section = _build_section()
    props = section.gross_elastic_properties()
    biaxial = ElasticBiaxialStressAnalyzer(props).stress_from_moments(vertical_env.max_moment_Nmm, lat_result.max_lateral_moment_Nmm)
    torsion_group = RailEccentricityModel.from_values("R1", vertical_eccentricity_y=50).torsional_group_from_wheel_group(vertical_group)

    serv = DeflectionServiceabilityChecker().check_moving_deflection_envelope(defl_env, DeflectionLimit.absolute("DABS", 100))
    stress = ElasticStressCriteriaChecker().check_biaxial_stress_result(biaxial, StressLimit.absolute("SABS", 1000))

    return CraneRunwayDemandSummaryBuilder.build_basic_summary(
        summary_id="SUM1",
        span_internal_mm=10_000,
        section_id=section.section_id,
        load_model_id=model.crane_id,
        vertical_envelope=vertical_env,
        deflection_envelope=defl_env,
        lateral_analysis_result=lat_result,
        biaxial_stress_result=biaxial,
        torsional_load_group=torsion_group,
        serviceability_results=[serv],
        stress_utilization_results=[stress],
        warnings=["integration-warning"],
    )


def test_formatter_basic_text_and_markdown():
    summary = CraneRunwayDemandSummary(summary_id="R1", span_internal_mm=10_000)
    fmt = CraneRunwayDemandSummaryFormatter()
    text = fmt.format_text(summary)
    md = fmt.format_markdown(summary)

    assert isinstance(text, str)
    assert isinstance(md, str)
    assert "summary_id: R1" in text
    assert "10.000 m" in text
    assert "N/A" in text
    assert "# Crane Runway Demand Summary" in md
    assert "## Identification" in md
    assert "## Demands" in md
    assert "## Checks" in md
    assert "## Warnings" in md


def test_formatter_units_for_moment_and_missing_values():
    summary = CraneRunwayDemandSummaryBuilder.build_basic_summary(summary_id="R2", span_internal_mm=10_000)
    fmt = CraneRunwayDemandSummaryFormatter()
    text = fmt.format_text(summary)
    assert "max vertical moment: N/A" in text


def test_status_behavior_pass_fail_na():
    fmt = CraneRunwayDemandSummaryFormatter()
    pass_summary = CraneRunwayDemandSummary(
        summary_id="PASS",
        span_internal_mm=1000,
        serviceability_results=[type("R", (), {"passed": True})()],
        stress_utilization_results=[type("R", (), {"passed": True})()],
    )
    fail_summary = CraneRunwayDemandSummary(
        summary_id="FAIL",
        span_internal_mm=1000,
        serviceability_results=[type("R", (), {"passed": False})()],
    )
    na_summary = CraneRunwayDemandSummary(summary_id="NA", span_internal_mm=1000)

    assert "overall status: PASS" in fmt.format_text(pass_summary)
    assert "overall status: FAIL" in fmt.format_text(fail_summary)
    assert "overall status: N/A" in fmt.format_text(na_summary)


def test_warnings_render_in_text_and_markdown():
    fmt = CraneRunwayDemandSummaryFormatter()
    summary = CraneRunwayDemandSummary(summary_id="W", span_internal_mm=1000, warnings=["warn-1"])
    assert "warnings: warn-1" in fmt.format_text(summary)
    assert "- warn-1" in fmt.format_markdown(summary)

    summary_no_warnings = CraneRunwayDemandSummary(summary_id="W2", span_internal_mm=1000)
    assert "warnings: None" in fmt.format_text(summary_no_warnings)
    assert "- None" in fmt.format_markdown(summary_no_warnings)


def test_integration_markdown_contains_key_values_and_statuses():
    summary = _build_integration_summary()
    fmt = CraneRunwayDemandSummaryFormatter()
    md = fmt.format_markdown(summary)
    assert "| summary_id | SUM1 |" in md
    assert "Serviceability | PASS" in md
    assert "Stress criteria | PASS" in md
    assert "### Serviceability details" in md
    assert "### Stress utilization details" in md
    assert "integration-warning" in md


def test_validation_errors():
    fmt = CraneRunwayDemandSummaryFormatter()
    with pytest.raises(InvalidReportSummaryError):
        fmt.format_text(None)
    with pytest.raises(InvalidReportSummaryError):
        fmt.format_text(object())
