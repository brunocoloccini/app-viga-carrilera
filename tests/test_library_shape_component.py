import pytest

from section_core import LineToLineJoin, Section, Transform2D
from section_core.components import LibraryShapeComponent, PlateElement
from section_core.components.errors import InvalidComponentGeometryError, UnknownReferenceError, UnsupportedComponentOperationError


def _make_w_shape():
    return LibraryShapeComponent.from_tabulated(
        element_id="W1",
        shape_family="W",
        shape_name="W_TEST",
        area=10000,
        area_unit="mm2",
        Iyy=8.0e7,
        Iyy_unit="mm4",
        Izz=2.5e7,
        Izz_unit="mm4",
        depth=300,
        depth_unit="mm",
        width=200,
        width_unit="mm",
    )


def test_basic_creation_and_references():
    w = _make_w_shape()
    assert w.area_mm2() == pytest.approx(10000)
    assert w.Iyy_tabulated_mm4 == pytest.approx(8.0e7)
    assert w.Izz_tabulated_mm4 == pytest.approx(2.5e7)
    assert w.centroid_point().as_tuple() == pytest.approx((0, 0))
    assert w.bounding_box() == pytest.approx((-100, -150, 100, 150))
    assert len(w.nodes()) == 4
    assert len(w.reference_lines()) == 6
    assert w.get_reference_line("top_edge").line_id.endswith("top_edge")


def test_translation_shifts_geometry_but_not_tabulated_properties():
    w = _make_w_shape().translated(10, 25)
    assert w.centroid_point().as_tuple() == pytest.approx((10, 25))
    assert w.bounding_box() == pytest.approx((-90, -125, 110, 175))
    n = w.get_node("top_left")
    assert (n.y_internal_mm, n.z_internal_mm) == pytest.approx((-90, 175))
    assert w.area_mm2() == pytest.approx(10000)
    assert w.Iyy_tabulated_mm4 == pytest.approx(8.0e7)


def test_transform_translation_ok_and_rotation_unsupported():
    w = _make_w_shape().transformed(Transform2D.translation(5, -5))
    assert w.centroid_point().as_tuple() == pytest.approx((5, -5))
    with pytest.raises(UnsupportedComponentOperationError):
        _make_w_shape().transformed(Transform2D.rotation(5.0))


def test_section_integration_single_library_shape():
    s = Section(section_id="S_LIB", components=[_make_w_shape()])
    props = s.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(10000)
    assert props.centroid_y_mm == pytest.approx(0)
    assert props.centroid_z_mm == pytest.approx(0)
    assert props.Iyy_mm4 == pytest.approx(8.0e7)
    assert props.Izz_mm4 == pytest.approx(2.5e7)


def test_section_integration_with_cover_plate_parallel_axis_and_modulus_asymmetry():
    w = _make_w_shape()
    top_plate = PlateElement.horizontal_plate(
        element_id="CP",
        width=220,
        width_unit="mm",
        thickness=20,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=400,
        center_z_unit="mm",
    )
    base = Section(section_id="S_TMP", components=[w])
    assembled = LineToLineJoin(
        operation_id="OP_LIB",
        operation_type="ignored",
        source_component=top_plate,
        source_line_name="bottom_edge",
        target_component_id="W1",
        target_line_name="top_edge",
    ).apply(base)

    s = Section(section_id="S_COVER", components=[assembled.get_component("W1"), assembled.get_component("CP")])
    props = s.gross_elastic_properties()
    assert props.centroid_z_mm > 0
    assert props.Iyy_mm4 > w.Iyy_tabulated_mm4
    assert props.Izz_mm4 > w.Izz_tabulated_mm4
    assert props.S_y_top_mm3 != pytest.approx(props.S_y_bottom_mm3)


def test_validation_and_reference_errors():
    with pytest.raises(InvalidComponentGeometryError):
        LibraryShapeComponent.from_tabulated(
            element_id="BAD_A", shape_family="W", shape_name="BAD", area=-1, area_unit="mm2",
            Iyy=1, Iyy_unit="mm4", Izz=1, Izz_unit="mm4", depth=100, depth_unit="mm", width=100, width_unit="mm"
        )
    with pytest.raises(InvalidComponentGeometryError):
        LibraryShapeComponent.from_tabulated(
            element_id="BAD_I", shape_family="W", shape_name="BAD", area=1, area_unit="mm2",
            Iyy=-1, Iyy_unit="mm4", Izz=1, Izz_unit="mm4", depth=100, depth_unit="mm", width=100, width_unit="mm"
        )
    with pytest.raises(InvalidComponentGeometryError):
        LibraryShapeComponent.from_tabulated(
            element_id="BAD_D", shape_family="W", shape_name="BAD", area=1, area_unit="mm2",
            Iyy=1, Iyy_unit="mm4", Izz=1, Izz_unit="mm4", depth=0, depth_unit="mm", width=100, width_unit="mm"
        )
    with pytest.raises(UnsupportedComponentOperationError):
        LibraryShapeComponent.from_tabulated(
            element_id="BAD_R", shape_family="W", shape_name="BAD", area=1, area_unit="mm2",
            Iyy=1, Iyy_unit="mm4", Izz=1, Izz_unit="mm4", depth=100, depth_unit="mm", width=100, width_unit="mm", rotation_deg=10
        )
    with pytest.raises(UnknownReferenceError):
        _make_w_shape().get_reference_line("not_a_line")
