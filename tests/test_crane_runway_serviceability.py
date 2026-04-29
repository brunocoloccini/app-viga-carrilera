import pytest

from section_core.crane_runway import (
    CraneWheelGroup,
    DeflectionCriteriaSet,
    DeflectionLimit,
    DeflectionServiceabilityChecker,
    DuplicateServiceabilityLimitError,
    InvalidDeflectionLimitError,
    ServiceabilityError,
    SimpleSpanMovingDeflectionEnvelopeAnalyzer,
    SimpleSpanRunwayBeamDeflectionAnalyzer,
    WheelLoad,
)


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_deflection_limit_span_over_allowable():
    limit = DeflectionLimit.span_over("L600", 600)
    assert limit.allowable_deflection_mm(12000) == pytest.approx(20)


def test_deflection_limit_absolute_mm():
    limit = DeflectionLimit.absolute("ABS25", 25, unit="mm")
    assert limit.allowable_deflection_mm(12000) == pytest.approx(25)


def test_deflection_limit_absolute_inches_conversion():
    limit = DeflectionLimit.absolute("ABS1IN", 1, unit="in")
    assert limit.allowable_deflection_mm(12000) == pytest.approx(25.4)


def test_deflection_limit_minimum_of_span_and_absolute():
    limit = DeflectionLimit.minimum_of_span_over_and_absolute("MIN", 600, 25, unit="mm")
    assert limit.allowable_deflection_mm(12000) == pytest.approx(20)


def test_deflection_limit_invalid_values_rejected():
    with pytest.raises(InvalidDeflectionLimitError):
        DeflectionLimit.span_over("L0", 0)
    with pytest.raises(InvalidDeflectionLimitError):
        DeflectionLimit.absolute("NEG", -1, unit="mm")
    with pytest.raises(InvalidDeflectionLimitError):
        DeflectionLimit(limit_id="X", limit_type="unsupported")


def test_moving_deflection_pass_fail_and_metadata_preserved():
    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10,
        span_unit="m",
        E=200000,
        E_unit="MPa",
        I=1_000_000_000,
        I_unit="mm4",
        movement_step=1,
        movement_step_unit="m",
        station_step=1,
        station_step_unit="m",
    )
    env = analyzer.analyze_envelope(_group([WheelLoad.from_values("W1", 0, "m", 100, "kN")]))

    checker = DeflectionServiceabilityChecker()
    pass_result = checker.check_moving_deflection_envelope(env, DeflectionLimit.span_over("L300", 300))
    fail_result = checker.check_moving_deflection_envelope(env, DeflectionLimit.span_over("L1200", 1200))

    assert pass_result.passed is True
    assert fail_result.passed is False
    assert pass_result.utilization_ratio == pytest.approx(pass_result.demand_deflection_mm / pass_result.allowable_deflection_mm)
    assert pass_result.demand_x_mm == pytest.approx(env.max_deflection_x_mm)
    assert pass_result.demand_offset_x_mm == pytest.approx(env.max_deflection_offset_x_mm)


def test_fixed_deflection_result_can_be_checked():
    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4"
    )
    result = analyzer.analyze(_group([WheelLoad.from_values("W1", 5, "m", 100, "kN")]))

    checker = DeflectionServiceabilityChecker()
    check = checker.check_fixed_deflection_result(result, DeflectionLimit.span_over("L600", 600))

    assert check.limit_id == "L600"
    assert check.demand_offset_x_mm is None
    assert check.demand_x_mm == pytest.approx(result.max_deflection_x_mm)


def test_criteria_set_validation_and_multiple_checks():
    limits = [DeflectionLimit.span_over("L600", 600), DeflectionLimit.absolute("ABS25", 25)]
    criteria = DeflectionCriteriaSet(criteria_id="SLS", limits=limits)

    analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer.from_values(
        span=10, span_unit="m", E=200000, E_unit="MPa", I=1_000_000_000, I_unit="mm4"
    )
    result = analyzer.analyze(_group([WheelLoad.from_values("W1", 5, "m", 100, "kN")]))
    checks = criteria.check_fixed_deflection_result(result)

    assert len(checks) == 2
    assert {c.limit_id for c in checks} == {"L600", "ABS25"}

    with pytest.raises(DuplicateServiceabilityLimitError):
        DeflectionCriteriaSet(criteria_id="dup", limits=[DeflectionLimit.span_over("L600", 600), DeflectionLimit.span_over("L600", 700)])

    with pytest.raises(ServiceabilityError):
        DeflectionCriteriaSet(criteria_id="empty", limits=[])


def test_integration_moving_envelope_checked_against_l600():
    analyzer = SimpleSpanMovingDeflectionEnvelopeAnalyzer.from_values(
        span=10,
        span_unit="m",
        E=200000,
        E_unit="MPa",
        I=1_000_000_000,
        I_unit="mm4",
        movement_step=1,
        movement_step_unit="m",
        station_step=1,
        station_step_unit="m",
    )
    env = analyzer.analyze_envelope(_group([WheelLoad.from_values("W1", 0, "m", 100, "kN")]))

    check = DeflectionServiceabilityChecker().check_moving_deflection_envelope(env, DeflectionLimit.span_over("L600", 600))

    assert check.allowable_deflection_mm == pytest.approx(10000 / 600)
    assert check.demand_deflection_mm == pytest.approx(env.max_deflection_mm)
    assert check.utilization_ratio == pytest.approx(env.max_deflection_mm / (10000 / 600))
