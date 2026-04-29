import pytest

from section_core.crane_runway import CraneLoadModel, CraneWheelGroup, SimpleSpanRunwayBeamAnalyzer, WheelLoad
from section_core.crane_runway.analysis import CraneRunwayAnalysisError, InvalidRunwaySpanError, WheelOutsideSpanError


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_single_wheel_centered():
    analyzer = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m")
    group = _group([WheelLoad.from_values("W1", 5, "m", 100, "kN")])
    result = analyzer.analyze(group)

    assert result.left_reaction_N == pytest.approx(50_000)
    assert result.right_reaction_N == pytest.approx(50_000)
    assert result.max_moment_Nmm == pytest.approx(250_000_000)
    assert result.equilibrium_vertical_force_residual_N() == pytest.approx(0.0)
    assert result.equilibrium_moment_residual_Nmm() == pytest.approx(0.0)

    assert analyzer.shear_at(4_999.999999, group) > 0
    assert analyzer.shear_at(5_000.0, group) < 0


def test_single_wheel_eccentric():
    analyzer = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m")
    group = _group([WheelLoad.from_values("W1", 2, "m", 100, "kN")])

    result = analyzer.analyze(group)
    assert result.left_reaction_N == pytest.approx(80_000)
    assert result.right_reaction_N == pytest.approx(20_000)
    assert analyzer.moment_at(2_000.0, group) == pytest.approx(160_000_000)


def test_two_wheels_symmetric():
    analyzer = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m")
    group = _group(
        [
            WheelLoad.from_values("W1", 3, "m", 100, "kN"),
            WheelLoad.from_values("W2", 7, "m", 100, "kN"),
        ]
    )

    result = analyzer.analyze(group)
    assert result.left_reaction_N == pytest.approx(100_000)
    assert result.right_reaction_N == pytest.approx(100_000)
    assert analyzer.moment_at(5_000, group) == pytest.approx(300_000_000)


def test_wheel_group_from_load_model_with_impact():
    base = _group(
        [
            WheelLoad.from_values("W1", 2, "m", 50, "kN"),
            WheelLoad.from_values("W2", 8, "m", 50, "kN"),
        ]
    )
    model = CraneLoadModel(crane_id="C1", wheel_group=base, vertical_impact_factor=0.2)
    case = [c for c in model.load_cases() if c.case_type == "vertical_with_impact"][0]

    analyzer = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m")
    result = analyzer.analyze(case.wheel_group)
    assert (result.left_reaction_N + result.right_reaction_N) == pytest.approx(120_000)


def test_validation_errors():
    with pytest.raises(InvalidRunwaySpanError):
        SimpleSpanRunwayBeamAnalyzer.from_values(0, "m")
    with pytest.raises(InvalidRunwaySpanError):
        SimpleSpanRunwayBeamAnalyzer.from_values(-1, "m")

    analyzer = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m")
    with pytest.raises(WheelOutsideSpanError):
        analyzer.analyze(_group([WheelLoad.from_values("W1", 11, "m", 100, "kN")]))

    with pytest.raises(CraneRunwayAnalysisError):
        analyzer.analyze(_group([WheelLoad.from_values("W1", 5, "m", 100, "kN")]), sample_points=[-1])
