import pytest

from section_core.crane_runway.errors import DuplicateWheelError, InvalidCraneLoadModelError, InvalidWheelLoadError
from section_core.crane_runway.loads import CraneLoadCase, CraneLoadModel, CraneWheelGroup, WheelLoad


def _sample_group() -> CraneWheelGroup:
    w1 = WheelLoad.from_values("W1", 0, "mm", 100, "kN")
    w2 = WheelLoad.from_values("W2", 2, "m", 100, "kN", lateral_force=10, lateral_force_unit="kN")
    return CraneWheelGroup(group_id="G1", wheels=[w1, w2])


def test_wheel_load_n_mm_creation():
    w = WheelLoad.from_values("W1", 1000, "mm", 25000, "N")
    assert w.position_x_internal_mm == pytest.approx(1000)
    assert w.vertical_force_internal_N == pytest.approx(25000)


def test_wheel_load_kn_m_creation():
    w = WheelLoad.from_values("W1", 2.5, "m", 125, "kN")
    assert w.position_x_internal_mm == pytest.approx(2500)
    assert w.vertical_force_internal_N == pytest.approx(125000)


def test_wheel_load_kip_ft_creation():
    w = WheelLoad.from_values("W1", 10, "ft", 5, "kip")
    assert w.position_x_internal_mm == pytest.approx(3048)
    assert w.vertical_force_internal_N == pytest.approx(5 * 4448.2216152605)


def test_wheel_load_reject_negative_vertical_force():
    with pytest.raises(InvalidWheelLoadError):
        WheelLoad.from_values("W1", 1, "m", -10, "kN")


def test_wheel_load_reject_stress_unit_for_force():
    with pytest.raises(InvalidWheelLoadError):
        WheelLoad.from_values("W1", 1, "m", 10, "MPa")


def test_wheel_load_reject_force_unit_for_position():
    with pytest.raises(InvalidWheelLoadError):
        WheelLoad.from_values("W1", 1, "kN", 10, "kN")


def test_crane_wheel_group_totals_positions_bounds_translate():
    g = _sample_group()
    assert g.total_vertical_force_N() == pytest.approx(200000)
    assert g.total_lateral_force_N() == pytest.approx(10000)
    assert g.total_longitudinal_force_N() == pytest.approx(0)
    assert g.wheel_positions_mm() == [0, 2000]
    assert g.bounding_x() == (0, 2000)

    gt = g.translated(500)
    assert gt.wheel_positions_mm() == [500, 2500]
    assert gt.total_vertical_force_N() == pytest.approx(g.total_vertical_force_N())


def test_crane_wheel_group_duplicate_rejected():
    w1 = WheelLoad.from_values("W1", 0, "mm", 100, "kN")
    w2 = WheelLoad.from_values("W1", 500, "mm", 50, "kN")
    with pytest.raises(DuplicateWheelError):
        CraneWheelGroup(group_id="G1", wheels=[w1, w2])


def test_crane_wheel_group_empty_rejected():
    with pytest.raises(InvalidWheelLoadError):
        CraneWheelGroup(group_id="G1", wheels=[])


def test_crane_load_model_vertical_impact_factor():
    model = CraneLoadModel(crane_id="C1", wheel_group=_sample_group(), vertical_impact_factor=0.25)
    factored = model.factored_vertical_wheel_group()
    assert factored.total_vertical_force_N() == pytest.approx(250000)


def test_crane_load_model_lateral_factor_generation():
    model = CraneLoadModel(crane_id="C1", wheel_group=_sample_group(), lateral_force_factor=0.1)
    lateral = model.generated_lateral_wheel_group()
    assert [w.lateral_force_internal_N for w in lateral.wheels] == pytest.approx([10000, 10000])


def test_crane_load_model_longitudinal_factor_generation():
    model = CraneLoadModel(crane_id="C1", wheel_group=_sample_group(), longitudinal_force_factor=0.05)
    longitudinal = model.generated_longitudinal_wheel_group()
    assert longitudinal.total_longitudinal_force_N() == pytest.approx(10000)
    assert [w.longitudinal_force_internal_N for w in longitudinal.wheels] == pytest.approx([5000, 5000])


def test_crane_load_model_load_cases_expected_types():
    model = CraneLoadModel(crane_id="C1", wheel_group=_sample_group(), vertical_impact_factor=0.1)
    case_types = [c.case_type for c in model.load_cases()]
    assert case_types == ["vertical_nominal", "vertical_with_impact", "lateral", "longitudinal"]


def test_crane_load_model_negative_factors_rejected():
    g = _sample_group()
    with pytest.raises(InvalidCraneLoadModelError):
        CraneLoadModel(crane_id="C1", wheel_group=g, vertical_impact_factor=-0.1)
    with pytest.raises(InvalidCraneLoadModelError):
        CraneLoadModel(crane_id="C1", wheel_group=g, lateral_force_factor=-0.1)
    with pytest.raises(InvalidCraneLoadModelError):
        CraneLoadModel(crane_id="C1", wheel_group=g, longitudinal_force_factor=-0.1)


def test_crane_load_case_valid_creation():
    c = CraneLoadCase(case_id="LC1", case_type="vertical_nominal", wheel_group=_sample_group())
    assert c.case_id == "LC1"


def test_crane_load_case_missing_case_id_rejected():
    with pytest.raises(InvalidCraneLoadModelError):
        CraneLoadCase(case_id="", case_type="vertical_nominal", wheel_group=_sample_group())


def test_crane_load_case_missing_wheel_group_rejected():
    with pytest.raises(InvalidCraneLoadModelError):
        CraneLoadCase(case_id="LC1", case_type="vertical_nominal", wheel_group=None)
