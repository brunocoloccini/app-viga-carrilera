from pathlib import Path

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
    ElasticLateralBendingStressAnalyzer,
    ElasticStressCriteriaChecker,
    ElasticVerticalBendingStressAnalyzer,
    RailEccentricityModel,
    SimpleSpanEnvelopeCurveAnalyzer,
    SimpleSpanMovingDeflectionEnvelopeAnalyzer,
    SimpleSpanMovingLoadEnvelopeAnalyzer,
    SimpleSpanRunwayBeamLateralAnalyzer,
    StressLimit,
    WheelLoad,
)


def _build_demo_section() -> Section:
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

    section = Section(section_id="V1-034-demo", components=[ipn_200])
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


def build_demo_summary() -> CraneRunwayDemandSummary:
    section = _build_demo_section()
    gross = section.gross_elastic_properties()

    wheel_group = CraneWheelGroup(
        group_id="demo_wheels",
        wheels=[
            WheelLoad.from_values("W1", 0, "mm", 80, "kN"),
            WheelLoad.from_values("W2", 2000, "mm", 80, "kN"),
        ],
    )
    load_model = CraneLoadModel(
        crane_id="demo_crane",
        wheel_group=wheel_group,
        vertical_impact_factor=0.25,
        lateral_force_factor=0.10,
        longitudinal_force_factor=0.0,
    )

    vertical_group = load_model.factored_vertical_wheel_group()
    lateral_group = load_model.generated_lateral_wheel_group()

    moving_envelope = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(6, "m", step=250, step_unit="mm").analyze_envelope(vertical_group)
    envelope_curves = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        6,
        "m",
        movement_step=250,
        movement_step_unit="mm",
        station_step=500,
        station_step_unit="mm",
    ).analyze_curves(vertical_group)

    deflection_envelope = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=6,
        span_unit="m",
        E=200_000,
        E_unit="MPa",
        I=gross.Iyy_mm4,
        I_unit="mm4",
        movement_step=250,
        movement_step_unit="mm",
        station_step=500,
        station_step_unit="mm",
    ).analyze_envelope(vertical_group)

    serviceability = DeflectionServiceabilityChecker().check_moving_deflection_envelope(
        deflection_envelope,
        DeflectionLimit.span_over("L_over_600", 600),
    )

    vertical_stress = ElasticVerticalBendingStressAnalyzer(gross).stress_from_moving_envelope_result(moving_envelope)

    representative_offset = moving_envelope.max_moment_offset_x_mm if moving_envelope.max_moment_offset_x_mm is not None else 0.0
    representative_lateral_group = lateral_group.translated(representative_offset)
    lateral_analysis = SimpleSpanRunwayBeamLateralAnalyzer.from_values(6, "m").analyze(representative_lateral_group)
    lateral_stress = ElasticLateralBendingStressAnalyzer(gross).stress_from_lateral_analysis_result(lateral_analysis)

    biaxial = ElasticBiaxialStressAnalyzer(gross).stress_from_moments(
        vertical_moment_Nmm=moving_envelope.max_moment_Nmm,
        lateral_moment_Nmm=lateral_analysis.max_lateral_moment_Nmm,
        metadata={"assumption": "same-section combination using representative vertical/lateral moments"},
    )

    stress_util = ElasticStressCriteriaChecker().check_biaxial_stress_result(
        biaxial,
        StressLimit.fraction_of_Fy("0.66Fy", Fy=250, factor=0.66, Fy_unit="MPa"),
    )

    combined_group = CraneWheelGroup(
        group_id="representative_vertical_plus_lateral",
        wheels=[
            WheelLoad(
                wheel_id=f"{v.wheel_id}_VL",
                position_x_internal_mm=v.position_x_internal_mm,
                vertical_force_internal_N=v.vertical_force_internal_N,
                lateral_force_internal_N=l.lateral_force_internal_N,
            )
            for v, l in zip(vertical_group.wheels, representative_lateral_group.wheels)
        ],
    )

    torsional_group = RailEccentricityModel.from_values(
        model_id="rail_ecc_demo",
        vertical_eccentricity_y=25,
        vertical_eccentricity_y_unit="mm",
        lateral_load_height_z=100,
        lateral_load_height_z_unit="mm",
        include_vertical=True,
        include_lateral=True,
    ).torsional_group_from_wheel_group(combined_group)

    summary = CraneRunwayDemandSummaryBuilder.build_basic_summary(
        summary_id="V1-034-demo-summary",
        span_internal_mm=6000,
        section_id=section.section_id,
        load_model_id=load_model.crane_id,
        gross_properties=gross,
        vertical_envelope=moving_envelope,
        deflection_envelope=deflection_envelope,
        lateral_analysis_result=lateral_analysis,
        biaxial_stress_result=biaxial,
        torsional_load_group=torsional_group,
        serviceability_results=[serviceability],
        stress_utilization_results=[stress_util],
        warnings=[
            "CIRSOC sample profile data is manually curated and must be independently verified before production use.",
            "No CIRSOC design-code checks are performed.",
            "No torsional or warping stress check is performed.",
            "No fatigue check is performed.",
        ],
    )
    summary.envelope_curves = envelope_curves
    summary.vertical_stress_result = vertical_stress
    summary.lateral_stress_result = lateral_stress
    summary.metadata["lateral_position_assumption"] = (
        "Lateral group translated to vertical max-moment offset when available; fallback offset is 0 mm."
    )
    return summary


def build_demo_reports() -> tuple[str, str]:
    summary = build_demo_summary()
    formatter = CraneRunwayDemandSummaryFormatter()
    return formatter.format_text(summary), formatter.format_markdown(summary)


if __name__ == "__main__":
    text_report, markdown_report = build_demo_reports()
    print(text_report)
    print("\n" + "=" * 80 + "\n")
    print(markdown_report)
