import math
from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.crane_runway import (
    CraneLoadModel,
    CraneWheelGroup,
    ElasticLateralBendingStressAnalyzer,
    InvalidLateralMomentError,
    InvalidLateralStressPropertiesError,
    SimpleSpanRunwayBeamLateralAnalyzer,
    WheelLoad,
)
from section_core.crane_runway.analysis import InvalidRunwaySpanError, WheelOutsideSpanError
from section_core.section import GrossElasticProperties


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_lateral_single_wheel_centered():
    analyzer = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m")
    group = _group([WheelLoad.from_values("W1", 5, "m", 100, "kN", lateral_force=10, lateral_force_unit="kN")])
    result = analyzer.analyze(group)
    assert result.left_reaction_N == pytest.approx(5_000)
    assert result.right_reaction_N == pytest.approx(5_000)
    assert result.max_lateral_moment_Nmm == pytest.approx(25_000_000)
    assert result.equilibrium_lateral_force_residual_N() == pytest.approx(0)
    assert result.equilibrium_lateral_moment_residual_Nmm() == pytest.approx(0)


def test_lateral_single_wheel_eccentric_and_two_wheels():
    analyzer = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m")
    g1 = _group([WheelLoad.from_values("W1", 2, "m", 100, "kN", lateral_force=10, lateral_force_unit="kN")])
    r1 = analyzer.analyze(g1)
    assert r1.left_reaction_N == pytest.approx(8_000)
    assert r1.right_reaction_N == pytest.approx(2_000)
    assert analyzer.lateral_moment_at(2_000, g1) == pytest.approx(16_000_000)

    g2 = _group([
        WheelLoad.from_values("W1", 3, "m", 100, "kN", lateral_force=10, lateral_force_unit="kN"),
        WheelLoad.from_values("W2", 7, "m", 100, "kN", lateral_force=10, lateral_force_unit="kN"),
    ])
    r2 = analyzer.analyze(g2)
    assert r2.left_reaction_N == pytest.approx(10_000)
    assert r2.right_reaction_N == pytest.approx(10_000)
    assert analyzer.lateral_moment_at(5_000, g2) == pytest.approx(30_000_000)


def test_lateral_group_generated_from_model_and_validation_errors():
    base = _group([
        WheelLoad.from_values("W1", 2, "m", 50, "kN"),
        WheelLoad.from_values("W2", 8, "m", 50, "kN"),
    ])
    model = CraneLoadModel(crane_id="C1", wheel_group=base, lateral_force_factor=0.1)
    lat_group = [c for c in model.load_cases() if c.case_type == "lateral"][0].wheel_group
    result = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(lat_group)
    assert (result.left_reaction_N + result.right_reaction_N) == pytest.approx(10_000)

    with pytest.raises(InvalidRunwaySpanError):
        SimpleSpanRunwayBeamLateralAnalyzer.from_values(0, "m")
    with pytest.raises(WheelOutsideSpanError):
        SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(
            _group([WheelLoad.from_values("W1", 11, "m", 100, "kN", lateral_force=10, lateral_force_unit="kN")])
        )


def test_lateral_stress_basic_and_validation():
    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 1, 100_000, 200_000)
    analyzer = ElasticLateralBendingStressAnalyzer(gross_properties=gp)
    s = analyzer.stress_from_lateral_moment(10_000_000)
    assert s.sigma_left_compression_or_tension_MPa == pytest.approx(100)
    assert s.sigma_right_compression_or_tension_MPa == pytest.approx(50)
    assert s.max_abs_lateral_stress_MPa == pytest.approx(100)

    with pytest.raises(InvalidLateralStressPropertiesError):
        ElasticLateralBendingStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 1, 0, 1))
    with pytest.raises(InvalidLateralStressPropertiesError):
        ElasticLateralBendingStressAnalyzer(GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 1, 1, 1, 0))
    with pytest.raises(InvalidLateralMomentError):
        analyzer.stress_from_lateral_moment(math.nan)


def test_integration_lateral_analysis_and_stress_with_sample_library():
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
    lat_group = model.generated_lateral_wheel_group()
    analysis = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(lat_group)
    stress = ElasticLateralBendingStressAnalyzer(props).stress_from_lateral_analysis_result(analysis)

    assert stress.max_abs_lateral_stress_MPa > 0
    assert stress.S_z_left_mm3 == pytest.approx(props.S_z_left_mm3)
    assert stress.S_z_right_mm3 == pytest.approx(props.S_z_right_mm3)
