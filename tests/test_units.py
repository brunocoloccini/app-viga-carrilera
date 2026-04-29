import pytest

from section_core.units.dimensions import Dimension
from section_core.units.errors import UnitCompatibilityError
from section_core.units.quantity import Quantity


def test_in_to_mm_exact():
    q = Quantity(1, "in", Dimension.LENGTH)
    assert q.internal_unit == "mm"
    assert q.internal_value == pytest.approx(25.4)


def test_ft_to_mm_exact():
    q = Quantity(1, "ft", Dimension.LENGTH)
    assert q.internal_value == pytest.approx(304.8)


def test_kip_to_n_exact():
    q = Quantity(1, "kip", Dimension.FORCE)
    assert q.internal_value == pytest.approx(4448.2216152605)


def test_ksi_to_mpa():
    q = Quantity(50, "ksi", Dimension.STRESS)
    assert q.internal_unit == "MPa"
    assert q.internal_value == pytest.approx(344.737864658418)


def test_lb_per_yd_as_line_force():
    q = Quantity(135, "lb/yd", Dimension.LINE_FORCE)
    # internal is N/mm; convert to kN/m numerically equal to N/mm
    assert q.internal_value == pytest.approx(0.6567, rel=1e-4)


def test_12_7_mm_equals_half_inch():
    q_mm = Quantity(12.7, "mm", Dimension.LENGTH)
    q_in = Quantity(0.5, "in", Dimension.LENGTH)
    assert q_mm.internal_value == pytest.approx(q_in.internal_value)


def test_inertia_rejects_mm3():
    with pytest.raises(UnitCompatibilityError):
        Quantity(1000, "mm3", Dimension.INERTIA)


def test_stress_rejects_kn():
    with pytest.raises(UnitCompatibilityError):
        Quantity(250, "kN", Dimension.STRESS)


def test_force_rejects_mass_unit():
    with pytest.raises(UnitCompatibilityError):
        Quantity(100, "kg", Dimension.FORCE)


def test_original_unit_preserved():
    q = Quantity(250, "kN", Dimension.FORCE)
    assert q.unit == "kN"
    assert q.original_text == "250 kN"
