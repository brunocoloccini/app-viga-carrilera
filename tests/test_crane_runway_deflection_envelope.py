import pytest

from section_core.crane_runway import (
    CraneLoadModel,
    CraneWheelGroup,
    DeflectionEnvelopeError,
    InvalidDeflectionEnvelopeStationError,
    InvalidDeflectionEnvelopeStepError,
    SimpleSpanMovingDeflectionEnvelopeAnalyzer,
    SimpleSpanRunwayBeamDeflectionAnalyzer,
    WheelGroupLongerThanSpanError,
    WheelLoad,
)


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_single_wheel_deflection_envelope_maximum():
    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    result = analyzer.analyze_envelope(group)

    expected = (100_000 * 10_000**3) / (48 * 200_000 * 1_000_000_000)
    assert result.max_deflection_x_mm == pytest.approx(5_000)
    assert result.max_deflection_offset_x_mm == pytest.approx(5_000)
    assert result.max_deflection_mm == pytest.approx(expected)


def test_two_wheels_positions_and_greater_than_single():
    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    single = analyzer.analyze_envelope(_group([WheelLoad.from_values("W1", 0, "m", 100, "kN")]))
    dual = analyzer.analyze_envelope(_group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 4, "m", 100, "kN"),
    ]))

    assert dual.number_of_positions() == 7
    assert dual.max_deflection_mm > single.max_deflection_mm
    assert dual.max_deflection_offset_x_mm in dual.moving_offsets_mm


def test_impact_group_scales():
    base_group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    model = CraneLoadModel(crane_id="C1", wheel_group=base_group, vertical_impact_factor=0.2)
    impact_group = [c for c in model.load_cases() if c.case_type == "vertical_with_impact"][0].wheel_group

    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    base = analyzer.analyze_envelope(base_group)
    impact = analyzer.analyze_envelope(impact_group)
    assert impact.max_deflection_mm == pytest.approx(base.max_deflection_mm * 1.2)


def test_explicit_stations_sorted_deduplicated():
    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4", movement_step=1, movement_step_unit="m", stations=[10000, 0, 5000, 2500, 5000, 7500], station_unit="mm"
    )
    result = analyzer.analyze_envelope(_group([WheelLoad.from_values("W1", 0, "m", 100, "kN")]))

    assert result.station_count() == 5
    assert [p.x_internal_mm for p in result.station_points] == [0, 2500, 5000, 7500, 10000]


def test_endpoint_inclusion():
    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4", movement_step=3, movement_step_unit="m", station_step=3, station_step_unit="m"
    )
    result = analyzer.analyze_envelope(_group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 3.5, "m", 100, "kN"),
    ]))

    assert result.moving_offsets_mm[-1] == pytest.approx(6500)
    assert result.station_points[-1].x_internal_mm == pytest.approx(10000)


def test_validation_errors():
    with pytest.raises(InvalidDeflectionEnvelopeStepError):
        SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(span=10, span_unit="m", E=200000, I=1_000_000_000, movement_step=0)
    with pytest.raises(InvalidDeflectionEnvelopeStepError):
        SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(span=10, span_unit="m", E=200000, I=1_000_000_000, movement_step=1, station_step=-1)
    with pytest.raises(DeflectionEnvelopeError):
        SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(span=10, span_unit="m", E=0, I=1_000_000_000, movement_step=1)
    with pytest.raises(DeflectionEnvelopeError):
        SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(span=10, span_unit="m", E=200000, I=-1, movement_step=1)

    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(span=10, span_unit="m", E=200000, I=1_000_000_000, movement_step=1)
    with pytest.raises(InvalidDeflectionEnvelopeStationError):
        analyzer_bad = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
            span=10, span_unit="m", E=200000, I=1_000_000_000, movement_step=1, stations=[-1], station_unit="mm"
        )
        analyzer_bad.analyze_envelope(_group([WheelLoad.from_values("W1", 0, "m", 100, "kN")]))

    long_group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN"), WheelLoad.from_values("W2", 11, "m", 100, "kN")])
    with pytest.raises(WheelGroupLongerThanSpanError):
        analyzer.analyze_envelope(long_group)


def test_consistency_with_fixed_position_for_critical_offset():
    moving = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    env = moving.analyze_envelope(group)
    critical = env.critical_result_for_max_deflection()

    fixed = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4")
    fixed_result = fixed.analyze(critical.shifted_wheel_group, sample_points=[p.x_internal_mm for p in env.station_points])
    assert fixed_result.max_deflection_mm == pytest.approx(env.max_deflection_mm)
