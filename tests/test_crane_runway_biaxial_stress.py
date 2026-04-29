import math
from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.crane_runway import (
    BiaxialStressAtPoint,
    CraneLoadModel,
    CraneWheelGroup,
    ElasticBiaxialStressAnalyzer,
    ElasticLateralBendingStressAnalyzer,
    ElasticVerticalBendingStressAnalyzer,
    InvalidBiaxialMomentError,
    InvalidBiaxialStressPropertiesError,
    SimpleSpanRunwayBeamAnalyzer,
    SimpleSpanRunwayBeamLateralAnalyzer,
    WheelLoad,
)
from section_core.section import GrossElasticProperties


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def _point_map(points: list[BiaxialStressAtPoint]) -> dict[str, BiaxialStressAtPoint]:
    return {p.point_id: p for p in points}


def test_basic_biaxial_combination():
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 50_000, 100_000)
    result = ElasticBiaxialStressAnalyzer(gp).stress_from_moments(10_000_000, 5_000_000)
    p = _point_map(result.points)

    assert p["top_left"].sigma_vertical_MPa == pytest.approx(-100)
    assert p["bottom_left"].sigma_vertical_MPa == pytest.approx(50)
    assert p["top_left"].sigma_lateral_MPa == pytest.approx(100)
    assert p["top_right"].sigma_lateral_MPa == pytest.approx(-50)

    assert p["top_left"].sigma_total_MPa == pytest.approx(0)
    assert p["top_right"].sigma_total_MPa == pytest.approx(-150)
    assert p["bottom_left"].sigma_total_MPa == pytest.approx(150)
    assert p["bottom_right"].sigma_total_MPa == pytest.approx(0)


def test_symmetric_section_pattern():
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 100_000, 80_000, 80_000)
    r = ElasticBiaxialStressAnalyzer(gp).stress_from_moments(20_000_000, 8_000_000)
    p = _point_map(r.points)
    assert p["top_left"].sigma_total_MPa == pytest.approx(-(p["bottom_right"].sigma_total_MPa))
    assert p["top_right"].sigma_total_MPa == pytest.approx(-(p["bottom_left"].sigma_total_MPa))


def test_vertical_only_and_lateral_only():
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 50_000, 100_000)
    analyzer = ElasticBiaxialStressAnalyzer(gp)

    v_only = analyzer.stress_from_moments(10_000_000, 0)
    pv = _point_map(v_only.points)
    assert pv["top_left"].sigma_total_MPa == pytest.approx(-100)
    assert pv["top_right"].sigma_total_MPa == pytest.approx(-100)
    assert pv["bottom_left"].sigma_total_MPa == pytest.approx(50)
    assert pv["bottom_right"].sigma_total_MPa == pytest.approx(50)

    l_only = analyzer.stress_from_moments(0, 5_000_000)
    pl = _point_map(l_only.points)
    assert pl["top_left"].sigma_total_MPa == pytest.approx(100)
    assert pl["bottom_left"].sigma_total_MPa == pytest.approx(100)
    assert pl["top_right"].sigma_total_MPa == pytest.approx(-50)
    assert pl["bottom_right"].sigma_total_MPa == pytest.approx(-50)


def test_result_integration_from_existing_stress_results_preserves_x():
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 50_000, 100_000)
    vertical = ElasticVerticalBendingStressAnalyzer(gp).stress_from_moment(10_000_000, x_internal_mm=3_000)
    lateral = ElasticLateralBendingStressAnalyzer(gp).stress_from_lateral_moment(5_000_000, x_internal_mm=3_000)
    combined = ElasticBiaxialStressAnalyzer(gp).stress_from_vertical_and_lateral_results(vertical, lateral)
    assert combined.x_internal_mm == pytest.approx(3_000)
    assert len(combined.points) == 4


def test_full_integration_with_sample_library():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)
    ipn = registry.to_component("CIRSOC_IPN_200", element_id="ipn")
    top_cover = PlateElement.horizontal_plate(
        element_id="top_cover", width=140, width_unit="mm", thickness=16, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=108, center_z_unit="mm"
    )
    section = Section(section_id="mono", components=[ipn, top_cover])
    props = section.gross_elastic_properties()

    base = _group([
        WheelLoad.from_values("W1", 2, "m", 50, "kN"),
        WheelLoad.from_values("W2", 8, "m", 50, "kN"),
    ])
    model = CraneLoadModel(crane_id="C1", wheel_group=base, lateral_force_factor=0.1)
    vertical_group = model.nominal_wheel_group()
    lateral_group = model.generated_lateral_wheel_group()

    vertical_result = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m").analyze(vertical_group)
    lateral_result = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(lateral_group)

    combined = ElasticBiaxialStressAnalyzer(props).stress_from_moments(
        vertical_moment_Nmm=vertical_result.max_moment_Nmm,
        lateral_moment_Nmm=lateral_result.max_lateral_moment_Nmm,
        x_internal_mm=vertical_result.max_moment_x_mm,
    )
    assert len(combined.points) == 4
    assert combined.max_abs_stress_MPa > 0


def test_validation_errors_for_properties_and_moments():
    with pytest.raises(InvalidBiaxialStressPropertiesError):
        ElasticBiaxialStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 0, 1, 1, 1))
    with pytest.raises(InvalidBiaxialStressPropertiesError):
        ElasticBiaxialStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 1, 0, 1))

    analyzer = ElasticBiaxialStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 1, 1, 1))
    with pytest.raises(InvalidBiaxialMomentError):
        analyzer.stress_from_moments(math.nan, 1)
    with pytest.raises(InvalidBiaxialMomentError):
        analyzer.stress_from_moments(1, math.nan)
