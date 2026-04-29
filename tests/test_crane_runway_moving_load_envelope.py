import pytest

from section_core.crane_runway import (
    CraneLoadModel,
    CraneWheelGroup,
    InvalidEnvelopeStepError,
    SimpleSpanMovingLoadEnvelopeAnalyzer,
    WheelGroupLongerThanSpanError,
    WheelLoad,
)
from section_core.crane_runway.envelope import MovingLoadEnvelopeError
from section_core.crane_runway.errors import InvalidWheelLoadError


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_single_wheel_envelope_maxima():
    analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=1, step_unit="m")
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])

    envelope = analyzer.analyze_envelope(group)
    assert envelope.max_moment_Nmm == pytest.approx(250_000_000)
    assert envelope.max_moment_x_mm == pytest.approx(5_000)
    assert envelope.max_moment_offset_x_mm == pytest.approx(5_000)
    assert envelope.max_left_reaction_N == pytest.approx(100_000)
    assert envelope.max_left_reaction_offset_x_mm == pytest.approx(0)
    assert envelope.max_right_reaction_N == pytest.approx(100_000)
    assert envelope.max_right_reaction_offset_x_mm == pytest.approx(10_000)


def test_two_equal_wheels_envelope():
    analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=1, step_unit="m")
    group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 4, "m", 100, "kN"),
    ])

    envelope = analyzer.analyze_envelope(group)
    assert envelope.number_of_positions() == 7
    assert envelope.max_moment_Nmm > 250_000_000
    assert envelope.max_moment_offset_x_mm == pytest.approx(2_000)
    assert envelope.max_left_reaction_N > 0
    assert envelope.max_right_reaction_N > 0


def test_impact_group_increases_max_moment():
    base_group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 4, "m", 100, "kN"),
    ])
    model = CraneLoadModel(crane_id="C1", wheel_group=base_group, vertical_impact_factor=0.2)
    impact_group = [c for c in model.load_cases() if c.case_type == "vertical_with_impact"][0].wheel_group

    analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=1, step_unit="m")
    base_env = analyzer.analyze_envelope(base_group)
    impact_env = analyzer.analyze_envelope(impact_group)

    assert impact_env.max_moment_Nmm == pytest.approx(base_env.max_moment_Nmm * 1.2)


def test_endpoint_inclusion_when_step_not_multiple():
    analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=3, step_unit="m")
    group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 3.5, "m", 100, "kN"),
    ])
    envelope = analyzer.analyze_envelope(group)

    offsets = [r.offset_x_internal_mm for r in envelope.position_results]
    assert offsets[-1] == pytest.approx(6_500)


def test_validation_errors():
    with pytest.raises(InvalidEnvelopeStepError):
        SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=0, step_unit="m")
    with pytest.raises(InvalidEnvelopeStepError):
        SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=-1, step_unit="m")

    analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=1, step_unit="m")
    long_group = _group([
        WheelLoad.from_values("W1", 0, "m", 100, "kN"),
        WheelLoad.from_values("W2", 11, "m", 100, "kN"),
    ])
    with pytest.raises(WheelGroupLongerThanSpanError):
        analyzer.analyze_envelope(long_group)

    with pytest.raises(InvalidWheelLoadError):
        CraneWheelGroup(group_id="Gx", wheels=[])


def test_critical_result_helpers_match_offsets():
    analyzer = SimpleSpanMovingLoadEnvelopeAnalyzer.from_values(span=10, span_unit="m", step=1, step_unit="m")
    group = _group([WheelLoad.from_values("W1", 0, "m", 100, "kN")])
    envelope = analyzer.analyze_envelope(group)

    assert envelope.critical_result_for_max_moment().offset_x_internal_mm == pytest.approx(envelope.max_moment_offset_x_mm)
    assert envelope.critical_result_for_max_left_reaction().offset_x_internal_mm == pytest.approx(
        envelope.max_left_reaction_offset_x_mm
    )
    assert envelope.critical_result_for_max_right_reaction().offset_x_internal_mm == pytest.approx(
        envelope.max_right_reaction_offset_x_mm
    )
