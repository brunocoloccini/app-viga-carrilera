import math

import pytest

from section_core.crane_runway.loads import CraneLoadModel, CraneWheelGroup, WheelLoad
from section_core.crane_runway.rail_eccentricity import (
    DuplicateTorsionalWheelError,
    InvalidRailEccentricityError,
    InvalidTorsionalLoadError,
    RailEccentricityModel,
    WheelTorsionalLoad,
    WheelTorsionalLoadGroup,
)


def _sample_wheels() -> CraneWheelGroup:
    w1 = WheelLoad.from_values("W1", 0, "mm", 100, "kN")
    w2 = WheelLoad.from_values("W2", 2, "m", 80, "kN", lateral_force=8, lateral_force_unit="kN")
    return CraneWheelGroup(group_id="G1", wheels=[w1, w2])


def test_wheel_torsional_load_valid_creation_and_signed_value():
    load = WheelTorsionalLoad("W1", 1000.0, -250000.0)
    assert load.wheel_id == "W1"
    assert load.torsional_moment_internal_Nmm == pytest.approx(-250000.0)


def test_wheel_torsional_load_missing_wheel_id_rejected():
    with pytest.raises(InvalidTorsionalLoadError):
        WheelTorsionalLoad("", 0.0, 100.0)


def test_wheel_torsional_load_nan_torsional_moment_rejected():
    with pytest.raises(InvalidTorsionalLoadError):
        WheelTorsionalLoad("W1", 0.0, math.nan)


def test_wheel_torsional_load_group_behaviors_and_translation():
    g = WheelTorsionalLoadGroup(
        group_id="TG1",
        torsional_loads=[
            WheelTorsionalLoad("W1", 0.0, 100.0),
            WheelTorsionalLoad("W2", 2000.0, -20.0),
        ],
    )
    assert g.total_torsional_moment_Nmm() == pytest.approx(80.0)
    assert g.torsional_positions_mm() == [0.0, 2000.0]
    assert g.bounding_x() == (0.0, 2000.0)

    gt = g.translated(500.0)
    assert gt.torsional_positions_mm() == [500.0, 2500.0]
    assert gt.total_torsional_moment_Nmm() == pytest.approx(g.total_torsional_moment_Nmm())


def test_wheel_torsional_load_group_duplicate_rejected():
    with pytest.raises(DuplicateTorsionalWheelError):
        WheelTorsionalLoadGroup(
            group_id="TG1",
            torsional_loads=[WheelTorsionalLoad("W1", 0.0, 1.0), WheelTorsionalLoad("W1", 1.0, 2.0)],
        )


def test_wheel_torsional_load_group_empty_rejected():
    with pytest.raises(InvalidTorsionalLoadError):
        WheelTorsionalLoadGroup(group_id="TG1", torsional_loads=[])


def test_rail_eccentricity_vertical_only_mm():
    wheel = WheelLoad.from_values("W1", 0, "mm", 100, "kN")
    model = RailEccentricityModel.from_values("R1", vertical_eccentricity_y=50, vertical_eccentricity_y_unit="mm")
    t = model.torsional_load_from_wheel(wheel)
    assert t.torsional_moment_internal_Nmm == pytest.approx(5_000_000.0)


def test_rail_eccentricity_negative_vertical_eccentricity():
    wheel = WheelLoad.from_values("W1", 0, "mm", 100, "kN")
    model = RailEccentricityModel.from_values("R1", vertical_eccentricity_y=-50, vertical_eccentricity_y_unit="mm")
    t = model.torsional_load_from_wheel(wheel)
    assert t.torsional_moment_internal_Nmm == pytest.approx(-5_000_000.0)


def test_rail_eccentricity_vertical_inches_conversion():
    wheel = WheelLoad.from_values("W1", 0, "mm", 100, "kN")
    model = RailEccentricityModel.from_values("R1", vertical_eccentricity_y=2, vertical_eccentricity_y_unit="in")
    t = model.torsional_load_from_wheel(wheel)
    assert t.torsional_moment_internal_Nmm == pytest.approx(100000 * 50.8)


def test_rail_eccentricity_lateral_only_contribution():
    wheel = WheelLoad.from_values("W1", 0, "mm", 100, "kN", lateral_force=10, lateral_force_unit="kN")
    model = RailEccentricityModel.from_values(
        "R1",
        vertical_eccentricity_y=0,
        include_vertical=False,
        include_lateral=True,
        lateral_load_height_z=200,
        lateral_load_height_z_unit="mm",
    )
    t = model.torsional_load_from_wheel(wheel)
    assert t.torsional_moment_internal_Nmm == pytest.approx(2_000_000.0)


def test_rail_eccentricity_combined_vertical_and_lateral():
    wheel = WheelLoad.from_values("W1", 0, "mm", 100, "kN", lateral_force=10, lateral_force_unit="kN")
    model = RailEccentricityModel.from_values(
        "R1",
        vertical_eccentricity_y=50,
        include_vertical=True,
        include_lateral=True,
        lateral_load_height_z=200,
        lateral_load_height_z_unit="mm",
    )
    t = model.torsional_load_from_wheel(wheel)
    assert t.torsional_moment_internal_Nmm == pytest.approx(7_000_000.0)


def test_rail_eccentricity_both_flags_false_rejected():
    with pytest.raises(InvalidRailEccentricityError):
        RailEccentricityModel.from_values("R1", vertical_eccentricity_y=10, include_vertical=False, include_lateral=False)


def test_rail_eccentricity_invalid_eccentricity_unit_rejected():
    with pytest.raises(InvalidRailEccentricityError):
        RailEccentricityModel.from_values("R1", vertical_eccentricity_y=10, vertical_eccentricity_y_unit="kN")
    with pytest.raises(InvalidRailEccentricityError):
        RailEccentricityModel.from_values("R1", vertical_eccentricity_y=10, vertical_eccentricity_y_unit="MPa")


def test_integration_with_crane_load_model_and_translation():
    base = _sample_wheels()
    load_model = CraneLoadModel(crane_id="C1", wheel_group=base, lateral_force_factor=0.1)
    lateral_group = load_model.generated_lateral_wheel_group()

    model = RailEccentricityModel.from_values(
        "R1",
        vertical_eccentricity_y=40,
        include_vertical=True,
        include_lateral=True,
        lateral_load_height_z=150,
    )
    torsion_group = model.torsional_group_from_wheel_group(lateral_group)

    assert torsion_group.torsional_positions_mm() == lateral_group.wheel_positions_mm()
    expected = [
        (100000 * 40) + (10000 * 150),
        (80000 * 40) + (8000 * 150),
    ]
    assert [t.torsional_moment_internal_Nmm for t in torsion_group.torsional_loads] == pytest.approx(expected)

    shifted = torsion_group.translated(350)
    assert shifted.torsional_positions_mm() == [x + 350 for x in torsion_group.torsional_positions_mm()]
