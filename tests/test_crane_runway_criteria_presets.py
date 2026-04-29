import pytest

from section_core.crane_runway import (
    CriteriaPresetNotFoundError,
    CriteriaPresetRegistry,
    DeflectionLimitPreset,
    DuplicateCriteriaPresetError,
    ElasticStressCriteriaChecker,
    InvalidCriteriaPresetError,
    StressLimitPreset,
    build_generic_criteria_preset_registry,
)
from section_core.section import GrossElasticProperties
from section_core.crane_runway import ElasticVerticalBendingStressAnalyzer


def test_deflection_limit_preset_span_divisor_converts_and_allows_l600_for_12000_mm():
    preset = DeflectionLimitPreset(preset_id="L600", preset_type="deflection", limit_type="span_divisor", span_divisor=600)
    limit = preset.to_deflection_limit()
    assert limit.limit_type == "span_divisor"
    assert limit.allowable_deflection_mm(12000) == pytest.approx(20)


def test_deflection_limit_preset_invalid_zero_divisor_rejected():
    with pytest.raises(InvalidCriteriaPresetError):
        DeflectionLimitPreset(preset_id="L0", preset_type="deflection", limit_type="span_divisor", span_divisor=0)


def test_deflection_limit_preset_unsupported_limit_type_rejected():
    with pytest.raises(InvalidCriteriaPresetError):
        DeflectionLimitPreset(preset_id="X", preset_type="deflection", limit_type="unsupported")


def test_stress_limit_preset_fraction_of_fy_converts_with_fy_and_gives_165_mpa():
    preset = StressLimitPreset(preset_id="FY66", preset_type="stress", limit_type="fraction_of_Fy", factor=0.66)
    limit = preset.to_stress_limit(Fy=250)
    assert limit.limit_type == "fraction_of_Fy"
    assert limit.allowable_stress_MPa() == pytest.approx(165)


def test_stress_limit_preset_fraction_of_fy_missing_fy_rejected():
    preset = StressLimitPreset(preset_id="FY66", preset_type="stress", limit_type="fraction_of_Fy", factor=0.66)
    with pytest.raises(InvalidCriteriaPresetError):
        preset.to_stress_limit()


def test_stress_limit_preset_absolute_converts():
    preset = StressLimitPreset(
        preset_id="ABS165", preset_type="stress", limit_type="absolute", allowable_stress_internal_MPa=165
    )
    limit = preset.to_stress_limit()
    assert limit.limit_type == "absolute"
    assert limit.allowable_stress_MPa() == pytest.approx(165)


def test_stress_limit_preset_unsupported_limit_type_rejected():
    with pytest.raises(InvalidCriteriaPresetError):
        StressLimitPreset(preset_id="X", preset_type="stress", limit_type="unsupported")


def test_registry_deflection_add_get_list_has_and_convert():
    registry = CriteriaPresetRegistry()
    preset = DeflectionLimitPreset(preset_id="L600", preset_type="deflection", limit_type="span_divisor", span_divisor=600)
    registry.add_deflection_preset(preset)

    assert registry.has_deflection_preset("L600") is True
    assert registry.get_deflection_preset("L600") == preset
    assert registry.list_deflection_preset_ids() == ["L600"]
    assert registry.to_deflection_limit("L600").allowable_deflection_mm(12000) == pytest.approx(20)

    with pytest.raises(DuplicateCriteriaPresetError):
        registry.add_deflection_preset(preset)
    with pytest.raises(CriteriaPresetNotFoundError):
        registry.get_deflection_preset("missing")


def test_registry_stress_add_get_list_has_and_convert():
    registry = CriteriaPresetRegistry()
    preset = StressLimitPreset(preset_id="FY66", preset_type="stress", limit_type="fraction_of_Fy", factor=0.66)
    registry.add_stress_preset(preset)

    assert registry.has_stress_preset("FY66") is True
    assert registry.get_stress_preset("FY66") == preset
    assert registry.list_stress_preset_ids() == ["FY66"]
    assert registry.to_stress_limit("FY66", Fy=250).allowable_stress_MPa() == pytest.approx(165)

    with pytest.raises(DuplicateCriteriaPresetError):
        registry.add_stress_preset(preset)
    with pytest.raises(CriteriaPresetNotFoundError):
        registry.get_stress_preset("missing")


def test_builtin_registry_contains_expected_ids_and_converts():
    registry = build_generic_criteria_preset_registry()
    assert registry.has_deflection_preset("deflection_L_over_600")
    assert registry.has_deflection_preset("deflection_L_over_750")
    assert registry.has_stress_preset("stress_0_66Fy")
    assert registry.has_stress_preset("stress_0_90Fy")

    assert registry.to_deflection_limit("deflection_L_over_600").allowable_deflection_mm(12000) == pytest.approx(20)
    assert registry.to_stress_limit("stress_0_66Fy", Fy=250).allowable_stress_MPa() == pytest.approx(165)


def test_integration_with_existing_checker_using_builtin_presets():
    registry = build_generic_criteria_preset_registry()
    stress_limit = registry.to_stress_limit("stress_0_66Fy", Fy=250)

    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 50_000, 100_000)
    vertical = ElasticVerticalBendingStressAnalyzer(gp).stress_from_moment(5_000_000, x_internal_mm=1000)
    result = ElasticStressCriteriaChecker().check_vertical_stress_result(vertical, stress_limit)

    assert result.allowable_stress_MPa == pytest.approx(165)
    assert result.utilization_ratio == pytest.approx(abs(result.demand_stress_MPa) / 165)
