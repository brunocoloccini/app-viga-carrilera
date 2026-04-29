import pytest

from section_core.assembly import AssemblyGeometryError, AssemblyReferenceError, NodeToPointJoin
from section_core.components import RectangularElement
from section_core.geometry import Node, Point2D, SectionPoint
from section_core.section import Section


def _mk_source(element_id: str = "S1") -> RectangularElement:
    return RectangularElement.from_bottom_left(
        element_id=element_id,
        width=20,
        width_unit="mm",
        height=10,
        height_unit="mm",
        bottom_left_y=200,
        bottom_left_y_unit="mm",
        bottom_left_z=300,
        bottom_left_z_unit="mm",
    )


def test_node_to_point_join_basic_alignment_and_geometry_preservation():
    section = Section(section_id="SEC1")
    source = _mk_source()
    target = SectionPoint.from_values(point_id="P1", y=40, z=70, unit="mm")

    result = NodeToPointJoin(
        operation_id="OP1",
        operation_type="ignored",
        source_component=source,
        source_node_name="bottom_left",
        target_point=target,
    ).apply(section)

    joined = result.get_component("S1")
    joined_bl = joined.get_node("bottom_left")
    assert joined_bl.y_internal_mm == pytest.approx(40.0)
    assert joined_bl.z_internal_mm == pytest.approx(70.0)
    assert joined.width_internal_mm == pytest.approx(source.width_internal_mm)
    assert joined.height_internal_mm == pytest.approx(source.height_internal_mm)
    assert joined.area_mm2() == pytest.approx(source.area_mm2())

    dy = 40.0 - source.get_node("bottom_left").y_internal_mm
    dz = 70.0 - source.get_node("bottom_left").z_internal_mm
    assert joined.get_node("top_right").y_internal_mm == pytest.approx(source.get_node("top_right").y_internal_mm + dy)
    assert joined.get_node("top_right").z_internal_mm == pytest.approx(source.get_node("top_right").z_internal_mm + dz)


def test_target_variants_section_point_point2d_and_node():
    source = _mk_source()

    section_point_target = SectionPoint.from_values(point_id="P1", y=0, z=0, unit="mm")
    res1 = NodeToPointJoin(operation_id="OP2", operation_type="ignored", source_component=source, source_node_name="bottom_left", target_point=section_point_target).apply(Section(section_id="A"))
    assert res1.get_component("S1").get_node("bottom_left").y_internal_mm == pytest.approx(0.0)

    point2d_target = Point2D.from_values(10, 20, units="mm")
    res2 = NodeToPointJoin(operation_id="OP3", operation_type="ignored", source_component=source, source_node_name="bottom_left", target_point=point2d_target).apply(Section(section_id="B"))
    assert res2.get_component("S1").get_node("bottom_left").z_internal_mm == pytest.approx(20.0)

    node_target = Node(node_id="N1", name="n", y_internal_mm=12.0, z_internal_mm=34.0)
    res3 = NodeToPointJoin(operation_id="OP4", operation_type="ignored", source_component=source, source_node_name="bottom_left", target_point=node_target).apply(Section(section_id="C"))
    n = res3.get_component("S1").get_node("bottom_left")
    assert n.y_internal_mm == pytest.approx(12.0)
    assert n.z_internal_mm == pytest.approx(34.0)


def test_to_coordinates_supports_mixed_length_units():
    section = Section(section_id="SEC1")
    source = _mk_source()

    result = NodeToPointJoin.to_coordinates(
        operation_id="OP5",
        source_component=source,
        source_node_name="bottom_left",
        y=1,
        y_unit="in",
        z=25.4,
        z_unit="mm",
    ).apply(section)

    n = result.get_component("S1").get_node("bottom_left")
    assert n.y_internal_mm == pytest.approx(25.4)
    assert n.z_internal_mm == pytest.approx(25.4)


def test_section_integration_and_gross_area_update_with_existing_component():
    base = RectangularElement.from_bottom_left(
        element_id="B1",
        width=100,
        width_unit="mm",
        height=50,
        height_unit="mm",
        bottom_left_y=0,
        bottom_left_y_unit="mm",
        bottom_left_z=0,
        bottom_left_z_unit="mm",
    )
    source = _mk_source()
    section = Section(section_id="SEC1")
    section.add_component(base)

    result = NodeToPointJoin(
        operation_id="OP6",
        operation_type="ignored",
        source_component=source,
        source_node_name="bottom_left",
        target_point=Point2D.from_values(0, 0),
    ).apply(section)

    assert result.has_component("B1")
    assert result.has_component("S1")
    assert result.gross_area_mm2() == pytest.approx(base.area_mm2() + source.area_mm2())


def test_errors_for_missing_source_node_invalid_target_duplicate_id_and_invalid_units():
    section = Section(section_id="SEC1")

    with pytest.raises(AssemblyReferenceError, match="Missing source node"):
        NodeToPointJoin(operation_id="OP7", operation_type="ignored", source_component=_mk_source(), source_node_name="bad_node", target_point=Point2D.from_values(0, 0)).apply(section)

    with pytest.raises(AssemblyGeometryError, match="Invalid target point"):
        NodeToPointJoin(operation_id="OP8", operation_type="ignored", source_component=_mk_source(), source_node_name="bottom_left", target_point=object()).apply(section)

    with pytest.raises(AssemblyReferenceError, match="Duplicate component id"):
        dup = _mk_source(element_id="B1")
        section_with_b1 = Section(section_id="SEC2", components=[_mk_source(element_id="B1")])
        NodeToPointJoin(operation_id="OP9", operation_type="ignored", source_component=dup, source_node_name="bottom_left", target_point=Point2D.from_values(0, 0)).apply(section_with_b1)

    with pytest.raises(AssemblyGeometryError, match="Invalid coordinate units"):
        NodeToPointJoin.to_coordinates(
            operation_id="OP10",
            source_component=_mk_source(),
            source_node_name="bottom_left",
            y=1,
            y_unit="kN",
            z=2,
            z_unit="mm",
        )


def test_trace_metadata_contains_translation_and_target_coordinates():
    section = Section(section_id="SEC1")
    source = _mk_source()
    result = NodeToPointJoin(
        operation_id="OP11",
        operation_type="ignored",
        source_component=source,
        source_node_name="bottom_left",
        target_point=SectionPoint.from_values(point_id="P1", y=10, z=20, unit="mm"),
    ).apply(section)

    trace = result.get_component("S1").metadata["assembly"]
    assert trace["operation_id"] == "OP11"
    assert trace["operation_type"] == "node_to_point_join"
    assert trace["source_component_id"] == "S1"
    assert trace["source_node_name"] == "bottom_left"
    assert trace["target_point_id"] == "P1"
    assert trace["target_y_internal_mm"] == pytest.approx(10.0)
    assert trace["target_z_internal_mm"] == pytest.approx(20.0)
    assert trace["translation_dy_mm"] == pytest.approx(-190.0)
    assert trace["translation_dz_mm"] == pytest.approx(-280.0)
