import pytest

from section_core import PlateElement, RectangularElement, Transform2D
from section_core.section.errors import InvalidSectionPropertiesError
from section_core.section.section import Section


def test_transform_identity():
    t = Transform2D.identity()
    assert t.apply_to_coordinates(10.0, -3.0) == pytest.approx((10.0, -3.0))


def test_transform_translation():
    t = Transform2D.translation(5.0, -2.0)
    assert t.apply_to_coordinates(10.0, 3.0) == pytest.approx((15.0, 1.0))


def test_transform_rotation_90_origin():
    t = Transform2D.rotation(90.0)
    assert t.apply_to_coordinates(2.0, 1.0) == pytest.approx((-1.0, 2.0))


def test_transform_rotation_90_custom_center():
    t = Transform2D.rotation(90.0, center_y_mm=10.0, center_z_mm=20.0)
    assert t.apply_to_coordinates(11.0, 20.0) == pytest.approx((10.0, 21.0))


def test_transform_combine_translation_only():
    t = Transform2D.translation(1.0, 2.0).combine(Transform2D.translation(3.0, 4.0))
    assert t.apply_to_coordinates(0.0, 0.0) == pytest.approx((4.0, 6.0))


def test_rotated_rectangle_geometry_90_deg():
    r = RectangularElement.from_center(element_id="R", width=10, width_unit="mm", height=4, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm", rotation_deg=90)
    assert r.area_mm2() == pytest.approx(40.0)
    assert r.centroid_point().as_tuple() == pytest.approx((0.0, 0.0))
    assert r.get_reference_point("bottom_left").as_tuple() == pytest.approx((2.0, -5.0))
    assert r.get_reference_point("bottom_right").as_tuple() == pytest.approx((2.0, 5.0))
    assert r.get_reference_point("top_right").as_tuple() == pytest.approx((-2.0, 5.0))
    assert r.get_reference_point("top_left").as_tuple() == pytest.approx((-2.0, -5.0))
    assert r.bounding_box() == pytest.approx((-2.0, -5.0, 2.0, 5.0))
    assert r.get_reference_line("bottom_edge").start.as_tuple() == pytest.approx((2.0, -5.0))


def test_plate_factories_support_rotation():
    hp = PlateElement.horizontal_plate(element_id="HP", width=100, width_unit="mm", thickness=10, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm", rotation_deg=90)
    vp = PlateElement.vertical_plate(element_id="VP", thickness=10, thickness_unit="mm", height=100, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm", rotation_deg=90)
    assert hp.bounding_box() == pytest.approx((-5.0, -50.0, 5.0, 50.0))
    assert vp.bounding_box() == pytest.approx((-50.0, -5.0, 50.0, 5.0))


def test_transformed_translation_matches_translated():
    r = RectangularElement.from_center(element_id="R", width=10, width_unit="mm", height=6, height_unit="mm", center_y=1, center_y_unit="mm", center_z=2, center_z_unit="mm")
    assert r.transformed(Transform2D.translation(3, 4)).bounding_box() == pytest.approx(r.translated(3, 4).bounding_box())


def test_transformed_rotation_changes_rotation_and_nodes():
    r = RectangularElement.from_center(element_id="R", width=10, width_unit="mm", height=4, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm")
    rr = r.transformed(Transform2D.rotation(90))
    assert rr.rotation_deg == pytest.approx(90)
    assert rr.get_reference_point("bottom_left").as_tuple() == pytest.approx((2.0, -5.0))


def test_gross_properties_reject_rotated_components():
    r = RectangularElement.from_center(element_id="R", width=10, width_unit="mm", height=4, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm", rotation_deg=10)
    s = Section(section_id="S", components=[r])
    with pytest.raises(InvalidSectionPropertiesError, match="rotated components"):
        s.gross_elastic_properties()
