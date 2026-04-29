import pytest

from section_core.crane_runway import (
    CraneLoadModel,
    CraneWheelGroup,
    InvalidEnvelopeStationError,
    InvalidEnvelopeStepError,
    SimpleSpanEnvelopeCurveAnalyzer,
    SimpleSpanMovingLoadEnvelopeAnalyzer,
    WheelGroupLongerThanSpanError,
    WheelLoad,
)


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_single_wheel_envelope_curve_maxima():
    analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10, span_unit="m", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])

    result = analyzer.analyze_curves(group)
    assert result.global_max_moment() == pytest.approx(250_000_000)
    assert result.global_max_moment_point().x_internal_mm == pytest.approx(5_000)

    point_mid = next(p for p in result.station_points if p.x_internal_mm == 5_000)
    assert point_mid.max_moment_Nmm == pytest.approx(250_000_000)
    assert result.global_max_shear_abs() == pytest.approx(100_000)


def test_two_equal_wheels_envelope_curve():
    analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10, span_unit="m", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 4, "m", 100, "kN"),
    ])

    result = analyzer.analyze_curves(group)
    assert result.station_count() == 11
    assert result.global_max_moment() > 250_000_000

    mid_point = next(p for p in result.station_points if p.x_internal_mm == 5_000)
    assert mid_point.max_shear_N > 0
    assert mid_point.min_shear_N < 0


def test_explicit_stations_are_sorted_and_deduplicated():
    analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10,
        span_unit="m",
        movement_step=1,
        movement_step_unit="m",
        stations=[10_000, 2_500, 5_000, 2_500, 0, 7_500],
        station_unit="mm",
    )
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])

    result = analyzer.analyze_curves(group)
    assert result.station_count() == 5
    assert [p.x_internal_mm for p in result.station_points] == [0, 2_500, 5_000, 7_500, 10_000]


def test_endpoint_inclusion_for_offsets_and_stations():
    analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10, span_unit="m", movement_step=3, movement_step_unit="m", station_step=3, station_step_unit="m"
    )
    group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 3.5, "m", 100, "kN"),
    ])

    result = analyzer.analyze_curves(group)
    assert result.moving_offsets_mm[-1] == pytest.approx(6_500)
    assert result.station_points[-1].x_internal_mm == pytest.approx(10_000)


def test_impact_group_scales_moment():
    base_group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 4, "m", 100, "kN"),
    ])
    model = CraneLoadModel(crane_id="C1", wheel_group=base_group, vertical_impact_factor=0.2)
    impact_group = [c for c in model.load_cases() if c.case_type == "vertical_with_impact"][0].wheel_group

    analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10, span_unit="m", movement_step=1, movement_step_unit="m", station_step=1, station_step_unit="m"
    )
    base_env = analyzer.analyze_curves(base_group)
    impact_env = analyzer.analyze_curves(impact_group)

    assert impact_env.global_max_moment() == pytest.approx(base_env.global_max_moment() * 1.2)


def test_validation_errors_for_steps_stations_and_group_length():
    with pytest.raises(InvalidEnvelopeStepError):
        SimpleSpanEnvelopeCurveAnalyzer.from_values(span=10, span_unit="m", movement_step=0, movement_step_unit="m")

    with pytest.raises(InvalidEnvelopeStepError):
        SimpleSpanEnvelopeCurveAnalyzer.from_values(
            span=10, span_unit="m", movement_step=1, movement_step_unit="m", station_step=-1, station_step_unit="m"
        )

    analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10, span_unit="m", movement_step=1, movement_step_unit="m", stations=[0, 11], station_unit="m"
    )
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    with pytest.raises(InvalidEnvelopeStationError):
        analyzer.analyze_curves(group)

    analyzer_ok = SimpleSpanEnvelopeCurveAnalyzer.from_values(span=10, span_unit="m", movement_step=1, movement_step_unit="m")
    long_group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 11, "m", 100, "kN"),
    ])
    with pytest.raises(WheelGroupLongerThanSpanError):
        analyzer_ok.analyze_curves(long_group)


def test_consistency_with_v1_022_global_envelope():
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    movement = 1
    station = 1

    curve_analyzer = SimpleSpanEnvelopeCurveAnalyzer.from_values(
        span=10, span_unit="m", movement_step=movement, movement_step_unit="m", station_step=station, station_step_unit="m"
    )
    moving_analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(
        span=10, span_unit="m", step=movement, step_unit="m"
    )

    curve_result = curve_analyzer.analyze_curves(group)
    moving_result = moving_analyzer.analyze_envelope(group)

    assert curve_result.global_max_moment() == pytest.approx(moving_result.max_moment_Nmm)
