import pytest

from section_core.components import PlateElement, RectangularElement
from section_core.components.errors import InvalidComponentGeometryError, UnsupportedComponentOperationError
from section_core.units.errors import UnitCompatibilityError


def test_create_rectangle_from_center_mm():
    r = RectangularElement.from_center(
        element_id="R1", width=200, width_unit="mm", height=100, height_unit="mm",
        center_y=10, center_y_unit="mm", center_z=20, center_z_unit="mm"
    )
    assert r.width_internal_mm == pytest.approx(200)
    assert r.height_internal_mm == pytest.approx(100)


def test_create_rectangle_width_in_inches():
    r = RectangularElement.from_center(
        element_id="R1", width=10, width_unit="in", height=100, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    assert r.width_internal_mm == pytest.approx(254.0)


def test_reject_negative_width():
    with pytest.raises(InvalidComponentGeometryError):
        RectangularElement.from_center(element_id="R1", width=-1, width_unit="mm", height=10, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm")


def test_reject_zero_height():
    with pytest.raises(InvalidComponentGeometryError):
        RectangularElement.from_center(element_id="R1", width=1, width_unit="mm", height=0, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm")


def test_reject_force_unit_for_width():
    with pytest.raises(UnitCompatibilityError):
        RectangularElement.from_center(element_id="R1", width=1, width_unit="kN", height=1, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm")


def test_rectangle_nodes_lines_and_references():
    r = RectangularElement.from_bottom_left(
        element_id="R1", width=100, width_unit="mm", height=50, height_unit="mm",
        bottom_left_y=10, bottom_left_y_unit="mm", bottom_left_z=20, bottom_left_z_unit="mm"
    )
    assert len(r.nodes()) == 4
    assert len(r.lines()) == 4
    assert r.get_reference_point("bottom_left").as_tuple() == pytest.approx((10, 20))
    assert r.get_reference_point("top_right").as_tuple() == pytest.approx((110, 70))
    assert r.area_mm2() == pytest.approx(5000)
    assert r.centroid_point().as_tuple() == pytest.approx((60, 45))
    assert r.bounding_box() == pytest.approx((10, 20, 110, 70))
    assert r.get_reference_point("mid_top").as_tuple() == pytest.approx((60, 70))
    assert r.get_reference_line("top_edge").line_id.endswith("top_edge")


def test_translated_preserves_dimensions_and_shifts():
    r = RectangularElement.from_center(
        element_id="R1", width=20, width_unit="mm", height=10, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    rt = r.translated(5, -3)
    assert rt.width_internal_mm == pytest.approx(r.width_internal_mm)
    assert rt.height_internal_mm == pytest.approx(r.height_internal_mm)
    assert rt.get_reference_point("bottom_left").as_tuple() == pytest.approx((-5, -8))


def test_unsupported_rotation_raises_clear_error():
    with pytest.raises(UnsupportedComponentOperationError):
        RectangularElement.from_center(element_id="R1", width=1, width_unit="mm", height=1, height_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm", rotation_deg=10)


def test_plate_horizontal_vertical_and_ids():
    hp = PlateElement.horizontal_plate(
        element_id="P1", width=200, width_unit="mm", thickness=10, thickness_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    vp = PlateElement.vertical_plate(
        element_id="P2", thickness=12, thickness_unit="mm", height=300, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    assert hp.width_internal_mm == pytest.approx(200)
    assert hp.height_internal_mm == pytest.approx(10)
    assert vp.width_internal_mm == pytest.approx(12)
    assert vp.height_internal_mm == pytest.approx(300)
    assert hp.element_type == "plate"
    assert all(node.element_id == "P1" for node in hp.nodes())
    assert all(line.element_id == "P1" for line in hp.lines())
