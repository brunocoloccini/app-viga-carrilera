from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.assembly import LineToLineJoin
from section_core.crane_runway import (
    CraneLoadModel,
    CraneRunwayCalculationWorkflow,
    CraneRunwayDemandSummary,
    CraneRunwayWorkflowInput,
    CraneRunwayWorkflowResult,
    CraneWheelGroup,
    DeflectionLimit,
    RailEccentricityModel,
    StressLimit,
    WheelLoad,
)


def _build_section() -> Section:
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)
    ipn_200 = registry.to_component("CIRSOC_IPN_200", element_id="ipn_200", center_y=0, center_z=100, center_unit="mm")
    cover_plate = PlateElement.horizontal_plate(element_id="cover_plate", width=140, width_unit="mm", thickness=10, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm")
    section = Section(section_id="V1-035-test", components=[ipn_200])
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


def _build_load_model() -> CraneLoadModel:
    wheel_group = CraneWheelGroup(
        group_id="wheels",
        wheels=[
            WheelLoad.from_values("W1", 0, "mm", 80, "kN"),
            WheelLoad.from_values("W2", 2000, "mm", 80, "kN"),
        ],
    )
    return CraneLoadModel("crane", wheel_group, vertical_impact_factor=0.25, lateral_force_factor=0.10)


def test_workflow_input_validation():
    section = _build_section()
    load_model = _build_load_model()
    ok = CraneRunwayWorkflowInput("wf", 6000, section, load_model, 250, 500, 200000)
    assert ok.workflow_id == "wf"

    with pytest.raises(Exception):
        CraneRunwayWorkflowInput("", 6000, section, load_model, 250, 500, 200000)
    with pytest.raises(Exception):
        CraneRunwayWorkflowInput("wf", 0, section, load_model, 250, 500, 200000)
    with pytest.raises(Exception):
        CraneRunwayWorkflowInput("wf", 6000, section, load_model, 0, 500, 200000)
    with pytest.raises(Exception):
        CraneRunwayWorkflowInput("wf", 6000, section, load_model, 250, 0, 200000)
    with pytest.raises(Exception):
        CraneRunwayWorkflowInput("wf", 6000, section, load_model, 250, 500, 0)


def test_workflow_input_from_values_units():
    wi = CraneRunwayWorkflowInput.from_values(
        workflow_id="wf",
        span=6,
        span_unit="m",
        section=_build_section(),
        crane_load_model=_build_load_model(),
        movement_step=25,
        movement_step_unit="cm",
        station_step=0.5,
        station_step_unit="m",
        E=200_000,
        E_unit="MPa",
    )
    assert wi.span_internal_mm == pytest.approx(6000)
    assert wi.movement_step_internal_mm == pytest.approx(250)
    assert wi.station_step_internal_mm == pytest.approx(500)
    assert wi.E_internal_MPa == pytest.approx(200_000)


def test_workflow_run_full():
    wi = CraneRunwayWorkflowInput.from_values(
        workflow_id="V1-035",
        span=6,
        span_unit="m",
        section=_build_section(),
        crane_load_model=_build_load_model(),
        movement_step=250,
        movement_step_unit="mm",
        station_step=500,
        station_step_unit="mm",
        E=200_000,
        E_unit="MPa",
        serviceability_limits=[DeflectionLimit.span_over("L600", 600)],
        stress_limits=[StressLimit.fraction_of_Fy("0.66Fy", Fy=250, factor=0.66, Fy_unit="MPa")],
        rail_eccentricity_model=RailEccentricityModel.from_values("R1", vertical_eccentricity_y=25, vertical_eccentricity_y_unit="mm", lateral_load_height_z=100, lateral_load_height_z_unit="mm", include_vertical=True, include_lateral=True),
    )
    result = CraneRunwayCalculationWorkflow(wi).run()
    assert isinstance(result, CraneRunwayWorkflowResult)
    assert isinstance(result.summary, CraneRunwayDemandSummary)
    assert "Crane Runway Demand Summary" in result.text_report
    assert "# Crane Runway Demand Summary" in result.markdown_report
    assert result.summary.max_vertical_moment_Nmm() > 0
    assert result.summary.max_vertical_deflection_mm() > 0
    assert result.summary.max_biaxial_stress_MPa() > 0
    assert result.summary.max_torsional_input_Nmm() > 0
    assert result.summary.serviceability_results
    assert result.summary.stress_utilization_results
    assert "overall_passed" in result.summary.to_dict()


def test_workflow_no_criteria():
    wi = CraneRunwayWorkflowInput.from_values(
        workflow_id="nocrit",
        span=6,
        span_unit="m",
        section=_build_section(),
        crane_load_model=_build_load_model(),
        movement_step=250,
        movement_step_unit="mm",
        station_step=500,
        station_step_unit="mm",
        E=200_000,
        E_unit="MPa",
    )
    summary = CraneRunwayCalculationWorkflow(wi).run().summary
    assert summary.serviceability_passed() is None
    assert summary.stress_criteria_passed() is None


def test_workflow_no_rail_eccentricity():
    wi = CraneRunwayWorkflowInput.from_values(
        workflow_id="norailecc",
        span=6,
        span_unit="m",
        section=_build_section(),
        crane_load_model=_build_load_model(),
        movement_step=250,
        movement_step_unit="mm",
        station_step=500,
        station_step_unit="mm",
        E=200_000,
        E_unit="MPa",
        rail_eccentricity_model=None,
    )
    summary = CraneRunwayCalculationWorkflow(wi).run().summary
    assert summary.max_torsional_input_Nmm() is None
