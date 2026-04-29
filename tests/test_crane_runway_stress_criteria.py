from pathlib import Path

import pytest

from section_core import PlateElement, Section, load_shape_library_json
from section_core.section import GrossElasticProperties
from section_core.crane_runway import (
    CraneLoadModel,
    CraneWheelGroup,
    DuplicateStressLimitError,
    ElasticBiaxialStressAnalyzer,
    ElasticLateralBendingStressAnalyzer,
    ElasticStressCriteriaChecker,
    ElasticVerticalBendingStressAnalyzer,
    InvalidStressLimitError,
    SimpleSpanRunwayBeamAnalyzer,
    SimpleSpanRunwayBeamLateralAnalyzer,
    StressCriteriaError,
    StressCriteriaSet,
    StressLimit,
    WheelLoad,
)


def _group(items):
    return CraneWheelGroup(group_id="G", wheels=items)


def test_stress_limit_absolute_mpa():
    limit = StressLimit.absolute("ABS165", 165, unit="MPa")
    assert limit.allowable_stress_MPa() == pytest.approx(165)


def test_stress_limit_absolute_ksi_conversion():
    limit = StressLimit.absolute("ABS24KSI", 24, unit="ksi")
    assert limit.allowable_stress_MPa() == pytest.approx(165.47424, rel=1e-6)


def test_stress_limit_fraction_of_fy():
    limit = StressLimit.fraction_of_Fy("FY66", Fy=250, factor=0.66, Fy_unit="MPa")
    assert limit.allowable_stress_MPa() == pytest.approx(165)


def test_stress_limit_invalid_values_rejected():
    with pytest.raises(InvalidStressLimitError):
        StressLimit.absolute("ZERO", 0)
    with pytest.raises(InvalidStressLimitError):
        StressLimit.fraction_of_Fy("NEG_FY", Fy=-250, factor=0.66)
    with pytest.raises(InvalidStressLimitError):
        StressLimit(limit_id="X", limit_type="unsupported")


def test_checker_vertical_pass_fail_and_ratio_and_x_offset_preserved():
    checker = ElasticStressCriteriaChecker()
    pass_limit = StressLimit.absolute("ABS200", 200)
    fail_limit = StressLimit.absolute("ABS99", 99)

    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 50_000, 100_000)
    result = ElasticVerticalBendingStressAnalyzer(gp).stress_from_moment(10_000_000, x_internal_mm=2_500, metadata={"max_moment_offset_x_mm": 750})

    passed = checker.check_vertical_stress_result(result, pass_limit)
    failed = checker.check_vertical_stress_result(result, fail_limit)

    assert passed.passed is True
    assert failed.passed is False
    assert passed.utilization_ratio == pytest.approx(abs(passed.demand_stress_MPa) / passed.allowable_stress_MPa)
    assert passed.x_internal_mm == pytest.approx(2500)
    assert passed.offset_x_internal_mm == pytest.approx(750)


def test_checker_lateral_and_biaxial_preserve_fields():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)
    ipn = registry.to_component("CIRSOC_IPN_200", element_id="ipn")
    top_cover = PlateElement.horizontal_plate(
        element_id="top_cover", width=140, width_unit="mm", thickness=16, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=108, center_z_unit="mm"
    )
    props = Section(section_id="mono", components=[ipn, top_cover]).gross_elastic_properties()

    base = _group([WheelLoad.from_values("W1", 2, "m", 50, "kN"), WheelLoad.from_values("W2", 8, "m", 50, "kN")])
    model = CraneLoadModel(crane_id="C1", wheel_group=base, lateral_force_factor=0.1)
    vertical_group = model.nominal_wheel_group()
    lateral_group = model.generated_lateral_wheel_group()

    vertical_result = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m").analyze(vertical_group)
    lateral_result = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(lateral_group)

    vertical_stress = ElasticVerticalBendingStressAnalyzer(props).stress_from_fixed_analysis_result(vertical_result)
    lateral_stress = ElasticLateralBendingStressAnalyzer(props).stress_from_lateral_analysis_result(lateral_result)
    biaxial = ElasticBiaxialStressAnalyzer(props).stress_from_vertical_and_lateral_results(
        vertical_stress,
        lateral_stress,
        metadata={"max_moment_offset_x_mm": 1234},
    )

    checker = ElasticStressCriteriaChecker()
    limit = StressLimit.absolute("ABS250", 250)

    lateral_check = checker.check_lateral_stress_result(lateral_stress, limit)
    biaxial_check = checker.check_biaxial_stress_result(biaxial, limit)

    assert lateral_check.demand_source == "lateral_bending"
    assert lateral_check.demand_stress_MPa == pytest.approx(lateral_stress.max_abs_lateral_stress_MPa)
    assert biaxial_check.demand_source == "biaxial_elastic"
    assert biaxial_check.critical_point_id == biaxial.max_abs_stress_point_id
    assert biaxial_check.x_internal_mm == pytest.approx(biaxial.x_internal_mm)
    assert biaxial_check.offset_x_internal_mm == pytest.approx(1234)


def test_stress_criteria_set_validation_and_multiple_checks():
    limits = [StressLimit.absolute("ABS165", 165), StressLimit.fraction_of_Fy("FY90", Fy=250, factor=0.9)]
    criteria = StressCriteriaSet(criteria_id="ELS", limits=limits)

    gp = GrossElasticProperties(1, 0, 0, 1, 1, 0, -1, 1, -1, 1, 100_000, 200_000, 50_000, 100_000)
    vertical = ElasticVerticalBendingStressAnalyzer(gp).stress_from_moment(5_000_000, x_internal_mm=1000)
    checks = criteria.check_vertical_stress_result(vertical)

    assert len(checks) == 2
    assert {c.limit_id for c in checks} == {"ABS165", "FY90"}

    with pytest.raises(DuplicateStressLimitError):
        StressCriteriaSet(criteria_id="dup", limits=[StressLimit.absolute("A", 100), StressLimit.absolute("A", 120)])

    with pytest.raises(StressCriteriaError):
        StressCriteriaSet(criteria_id="empty", limits=[])


def test_integration_biaxial_checked_against_absolute_limit_deterministic():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)
    ipn = registry.to_component("CIRSOC_IPN_200", element_id="ipn")
    top_cover = PlateElement.horizontal_plate(
        element_id="top_cover", width=140, width_unit="mm", thickness=16, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=108, center_z_unit="mm"
    )
    props = Section(section_id="mono", components=[ipn, top_cover]).gross_elastic_properties()

    base = _group([WheelLoad.from_values("W1", 2, "m", 50, "kN"), WheelLoad.from_values("W2", 8, "m", 50, "kN")])
    model = CraneLoadModel(crane_id="C1", wheel_group=base, lateral_force_factor=0.1)

    vr = SimpleSpanRunwayBeamAnalyzer.from_values(10, "m").analyze(model.nominal_wheel_group())
    lr = SimpleSpanRunwayBeamLateralAnalyzer.from_values(10, "m").analyze(model.generated_lateral_wheel_group())

    v_stress = ElasticVerticalBendingStressAnalyzer(props).stress_from_fixed_analysis_result(vr)
    l_stress = ElasticLateralBendingStressAnalyzer(props).stress_from_lateral_analysis_result(lr)
    biaxial = ElasticBiaxialStressAnalyzer(props).stress_from_vertical_and_lateral_results(v_stress, l_stress)

    limit = StressLimit.absolute("ABS180", 180)
    check = ElasticStressCriteriaChecker().check_biaxial_stress_result(biaxial, limit)

    assert check.demand_stress_MPa == pytest.approx(biaxial.max_abs_stress_MPa)
    assert check.allowable_stress_MPa == pytest.approx(180)
    assert check.utilization_ratio == pytest.approx(biaxial.max_abs_stress_MPa / 180)
