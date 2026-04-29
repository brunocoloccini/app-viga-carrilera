import math
from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.crane_runway import (
    CraneWheelGroup,
    ElasticVerticalBendingStressAnalyzer,
    InvalidMomentForStressError,
    InvalidSectionStressPropertiesError,
    SimpleSpanEnvelopeCurveAnalyzer,
    SimpleSpanMovingLoadEnvelopeAnalyzer,
    SimpleSpanRunwayBeamAnalyzer,
    WheelLoad,
)
from section_core.section import GrossElasticProperties


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_basic_stress_from_moment():
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 1, 1)
    analyzer = ElasticVerticalBendingStressAnalyzer(gross_properties=gp)
    result = analyzer.stress_from_moment(10_000_000)
    assert result.sigma_top_compression_MPa == pytest.approx(100)
    assert result.sigma_bottom_tension_MPa == pytest.approx(50)
    assert result.sigma_top_MPa == pytest.approx(-100)
    assert result.sigma_bottom_MPa == pytest.approx(50)
    assert result.max_abs_stress_MPa == pytest.approx(100)


def test_symmetric_section_equal_top_bottom_stress_magnitude():
    section = Section(
        section_id="sym",
        components=[
            PlateElement.horizontal_plate(
                element_id="R", width=200, width_unit="mm", thickness=400, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
            )
        ],
    )
    props = section.gross_elastic_properties()
    result = ElasticVerticalBendingStressAnalyzer(props).stress_from_moment(25_000_000)
    assert props.S_y_top_mm3 == pytest.approx(props.S_y_bottom_mm3)
    assert result.sigma_top_compression_MPa == pytest.approx(result.sigma_bottom_tension_MPa)


def test_monosymmetric_section_different_top_bottom_stress_magnitude():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)
    ipn = registry.to_component("CIRSOC_IPN_200", element_id="ipn")
    top_cover = PlateElement.horizontal_plate(
        element_id="top_cover", width=140, width_unit="mm", thickness=16, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=108, center_z_unit="mm"
    )
    section = Section(section_id="mono", components=[ipn, top_cover])
    props = section.gross_elastic_properties()
    result = ElasticVerticalBendingStressAnalyzer(props).stress_from_moment(100_000_000)
    assert props.S_y_top_mm3 != pytest.approx(props.S_y_bottom_mm3)
    assert result.sigma_top_compression_MPa != pytest.approx(result.sigma_bottom_tension_MPa)


def test_fixed_analysis_integration():
    fixed = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m").analyze(_group([WheelLoad.from_values("W1", 5, "m", 100, "kN")]))
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 1, 1)
    stress = ElasticVerticalBendingStressAnalyzer(gp).stress_from_fixed_analysis_result(fixed)
    assert stress.x_internal_mm == pytest.approx(fixed.max_moment_x_mm)
    assert stress.moment_Nmm == pytest.approx(fixed.max_moment_Nmm)
    assert stress.sigma_top_compression_MPa == pytest.approx(fixed.max_moment_Nmm / gp.S_y_top_mm3)


def test_moving_envelope_integration_preserves_critical_coordinates():
    env = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=1, step_unit="m").analyze_envelope(
        _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    )
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 100_000, 1, 1)
    stress = ElasticVerticalBendingStressAnalyzer(gp).stress_from_moving_envelope_result(env)
    assert stress.x_internal_mm == pytest.approx(env.max_moment_x_mm)
    assert stress.metadata["max_moment_offset_x_mm"] == pytest.approx(env.max_moment_offset_x_mm)


def test_envelope_curve_integration_station_count_and_global_critical_point():
    curve = SimpleSpanEnvelopeCurveAnalyzer.from_values(span=10, span_unit="m", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m").analyze_curves(
        _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    )
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 1, 1)
    stress_env = ElasticVerticalBendingStressAnalyzer(gp).stress_envelope_from_curve_result(curve)
    assert stress_env.station_count() == curve.station_count()
    critical = stress_env.global_critical_point()
    max_moment_point = curve.global_max_moment_point()
    assert critical.x_internal_mm == pytest.approx(max_moment_point.x_internal_mm)
    assert critical.max_moment_Nmm == pytest.approx(max_moment_point.max_moment_Nmm)


def test_validation_errors_for_section_modulus_and_moment():
    with pytest.raises(InvalidSectionStressPropertiesError):
        ElasticVerticalBendingStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 0, 1, 1, 1))
    with pytest.raises(InvalidSectionStressPropertiesError):
        ElasticVerticalBendingStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 0, 1, 1))

    analyzer = ElasticVerticalBendingStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 1, 1, 1))
    with pytest.raises(InvalidMomentForStressError):
        analyzer.stress_from_moment(math.nan)
