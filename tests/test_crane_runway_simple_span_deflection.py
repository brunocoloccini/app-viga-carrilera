import pytest

from section_core.crane_runway import CraneLoadModel, CraneWheelGroup, SimpleSpanRunwayBeamDeflectionAnalyzer, WheelLoad
from section_core.crane_runway.analysis import WheelOutsideSpanError
from section_core.crane_runway.deflection import DeflectionSamplePointError, InvalidFlexuralRigidityError


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_single_centered_wheel_deflection():
    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    group = _group([WheelLoad.from_values("W1", 5, "m", 100, "kN")])

    result = analyzer.analyze(group)
    delta_mid = analyzer.deflection_at(5_000, group)
    expected = (100_000 * 10_000**3) / (48 * 200_000 * 1_000_000_000)

    assert result.max_deflection_x_mm == pytest.approx(5_000)
    assert delta_mid == pytest.approx(expected)
    assert analyzer.deflection_at(0, group) == pytest.approx(0.0)
    assert analyzer.deflection_at(10_000, group) == pytest.approx(0.0)


def test_single_eccentric_wheel_deflection():
    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    group = _group([WheelLoad.from_values("W1", 2, "m", 100, "kN")])

    L = 10_000
    a = 2_000
    b = L - a
    expected_at_load = (100_000 * b * a / (6 * L * 200_000 * 1_000_000_000)) * (L * L - b * b - a * a)

    assert analyzer.deflection_at(0, group) == pytest.approx(0.0)
    assert analyzer.deflection_at(10_000, group) == pytest.approx(0.0)
    assert analyzer.deflection_at(a, group) == pytest.approx(expected_at_load)


def test_two_wheels_midspan_superposition():
    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    group = _group([WheelLoad.from_values("W1", 3, "m", 100, "kN"), WheelLoad.from_values("W2", 7, "m", 100, "kN")])

    mid = 5_000
    expected = analyzer._point_load_deflection(100_000, 3_000, mid) + analyzer._point_load_deflection(100_000, 7_000, mid)
    assert analyzer.deflection_at(mid, group) == pytest.approx(expected)


def test_impact_group_scales_deflection():
    base = _group([WheelLoad.from_values("W1", 5, "m", 100, "kN")])
    model = CraneLoadModel(crane_id="C1", wheel_group=base, vertical_impact_factor=0.25)
    impact = [c for c in model.load_cases() if c.case_type == "vertical_with_impact"][0].wheel_group

    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    base_delta = analyzer.deflection_at(5_000, base)
    impact_delta = analyzer.deflection_at(5_000, impact)

    assert impact_delta == pytest.approx(base_delta * 1.25)


def test_units_are_converted():
    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=100000, I_unit="cm4")
    assert analyzer.span_internal_mm == pytest.approx(10_000)
    assert analyzer.I_internal_mm4 == pytest.approx(1_000_000_000)


def test_validation_errors():
    with pytest.raises(InvalidFlexuralRigidityError):
        SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=0, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    with pytest.raises(InvalidFlexuralRigidityError):
        SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=-1, I_unit="mm4")

    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    with pytest.raises(WheelOutsideSpanError):
        analyzer.analyze(_group([WheelLoad.from_values("W1", 11, "m", 100, "kN")]))

    with pytest.raises(DeflectionSamplePointError):
        analyzer.analyze(_group([WheelLoad.from_values("W1", 5, "m", 100, "kN")]), sample_points=[-1])
