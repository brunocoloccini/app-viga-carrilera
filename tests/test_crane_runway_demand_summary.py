from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.assembly import LineToLineJoin
from section_core.crane_runway import (
    CraneLoadModel,
    CraneRunwayDemandSummary,
    CraneRunwayDemandSummaryBuilder,
    CraneWheelGroup,
    DeflectionLimit,
    DeflectionServiceabilityChecker,
    ElasticBiaxialStressAnalyzer,
    ElasticStressCriteriaChecker,
    InvalidDemandSummaryError,
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
    section = Section(section_id="V1-032", components=[ipn_200])
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


def test_basic_object_validation_and_defaults():
    s = CraneRunwayDemandSummary(summary_id="S1", span_internal_mm=10_000)
    assert s.summary_id == "S1"
    assert s.warnings == []
    assert s.metadata == {}
    assert s.serviceability_results == []
    assert s.stress_utilization_results == []

    with pytest.raises(InvalidDemandSummaryError):
        CraneRunwayDemandSummary(summary_id="", span_internal_mm=10_000)
    with pytest.raises(InvalidDemandSummaryError):
        CraneRunwayDemandSummary(summary_id="S2", span_internal_mm=0)


def test_getters_and_flags_and_to_dict():
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

    summary = CraneRunwayDemandSummaryBuilder.build_basic_summary(
        summary_id="SUM1",
        span_internal_mm=10_000,
        section_id=section.section_id,
        load_model_id=model.crane_id,
        gross_properties=props,
        vertical_envelope=vertical_env,
        deflection_envelope=defl_env,
        lateral_analysis_result=lat_result,
        biaxial_stress_result=biaxial,
        torsional_load_group=torsion_group,
        serviceability_results=[serv],
        stress_utilization_results=[stress],
        warnings=["example"],
        metadata={"phase": "integration"},
    )

    assert summary.max_vertical_moment_Nmm() == pytest.approx(vertical_env.max_moment_Nmm)
    assert summary.max_vertical_shear_abs_N() == pytest.approx(vertical_env.max_shear_abs_N)
    assert summary.max_vertical_deflection_mm() == pytest.approx(defl_env.max_deflection_mm)
    assert summary.max_lateral_moment_Nmm() == pytest.approx(lat_result.max_lateral_moment_Nmm)
    assert summary.max_biaxial_stress_MPa() == pytest.approx(biaxial.max_abs_stress_MPa)
    assert summary.max_torsional_input_Nmm() == pytest.approx(max(abs(x.torsional_moment_internal_Nmm) for x in torsion_group.torsional_loads))

    assert summary.serviceability_passed() is True
    assert summary.stress_criteria_passed() is True
    assert summary.overall_passed() is True

    out = summary.to_dict()
    assert out["summary_id"] == "SUM1"
    assert out["overall_passed"] is True
    assert out["warnings"] == ["example"]
    assert out["metadata"] == {"phase": "integration"}


def test_flag_edge_cases():
    s_none = CraneRunwayDemandSummary(summary_id="S_NONE", span_internal_mm=1_000)
    assert s_none.serviceability_passed() is None
    assert s_none.stress_criteria_passed() is None
    assert s_none.overall_passed() is None

    s_fail_serv = CraneRunwayDemandSummary(
        summary_id="S_FAIL_SERV",
        span_internal_mm=1_000,
        serviceability_results=[type("R", (), {"passed": True})(), type("R", (), {"passed": False})()],
    )
    assert s_fail_serv.serviceability_passed() is False
    assert s_fail_serv.overall_passed() is False

    s_fail_stress = CraneRunwayDemandSummary(
        summary_id="S_FAIL_STRESS",
        span_internal_mm=1_000,
        stress_utilization_results=[type("R", (), {"passed": False})()],
    )
    assert s_fail_stress.stress_criteria_passed() is False
    assert s_fail_stress.overall_passed() is False
