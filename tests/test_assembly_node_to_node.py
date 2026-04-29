import pytest

from section_core.assembly import AssemblyReferenceError, NodeToNodeJoin
from section_core.components import RectangularElement
from section_core.section import Section


def _mk_target() -> RectangularElement:
    return RectangularElement.from_bottom_left(
        element_id="T1",
        width=100,
        width_unit="mm",
        height=50,
        height_unit="mm",
        bottom_left_y=0,
        bottom_left_y_unit="mm",
        bottom_left_z=0,
        bottom_left_z_unit="mm",
    )


def _mk_source() -> RectangularElement:
    return RectangularElement.from_bottom_left(
        element_id="S1",
        width=20,
        width_unit="mm",
        height=10,
        height_unit="mm",
        bottom_left_y=200,
        bottom_left_y_unit="mm",
        bottom_left_z=300,
        bottom_left_z_unit="mm",
    )


def test_node_to_node_join_basic_alignment_and_geometry_preservation():
    section = Section(section_id="SEC1")
    target = _mk_target()
    source = _mk_source()
    section.add_component(target)

    op = NodeToNodeJoin(
        operation_id="OP1",
        operation_type="ignored",
        source_component=source,
        source_node_name="bottom_left",
        target_component_id="T1",
        target_node_name="top_right",
    )
    result = op.apply(section)

    joined = result.get_component("S1")
    joined_bl = joined.get_node("bottom_left")
    target_tr = target.get_node("top_right")
    assert joined_bl.y_internal_mm == pytest.approx(target_tr.y_internal_mm)
    assert joined_bl.z_internal_mm == pytest.approx(target_tr.z_internal_mm)
    assert joined.width_internal_mm == pytest.approx(source.width_internal_mm)
    assert joined.height_internal_mm == pytest.approx(source.height_internal_mm)
    assert joined.area_mm2() == pytest.approx(source.area_mm2())

    dy = target.get_node("top_right").y_internal_mm - source.get_node("bottom_left").y_internal_mm
    dz = target.get_node("top_right").z_internal_mm - source.get_node("bottom_left").z_internal_mm
    assert joined.get_node("top_right").y_internal_mm == pytest.approx(source.get_node("top_right").y_internal_mm + dy)
    assert joined.get_node("top_right").z_internal_mm == pytest.approx(source.get_node("top_right").z_internal_mm + dz)


def test_section_integration_area_and_centroid_update():
    section = Section(section_id="SEC1")
    target = _mk_target()
    source = _mk_source()
    section.add_component(target)

    result = NodeToNodeJoin(
        operation_id="OP2",
        operation_type="ignored",
        source_component=source,
        source_node_name="bottom_left",
        target_component_id="T1",
        target_node_name="top_right",
    ).apply(section)

    assert result.has_component("T1")
    assert result.has_component("S1")
    assert result.gross_area_mm2() == pytest.approx(target.area_mm2() + source.area_mm2())

    yc, zc = result.gross_centroid()
    expected_y = (target.area_mm2() * 50.0 + source.area_mm2() * 110.0) / (target.area_mm2() + source.area_mm2())
    expected_z = (target.area_mm2() * 25.0 + source.area_mm2() * 55.0) / (target.area_mm2() + source.area_mm2())
    assert yc == pytest.approx(expected_y)
    assert zc == pytest.approx(expected_z)


def test_error_on_missing_target_component():
    section = Section(section_id="SEC1")
    with pytest.raises(AssemblyReferenceError, match="Missing target component"):
        NodeToNodeJoin(
            operation_id="OP3",
            operation_type="ignored",
            source_component=_mk_source(),
            source_node_name="bottom_left",
            target_component_id="MISSING",
            target_node_name="top_right",
        ).apply(section)


def test_error_on_missing_source_node():
    section = Section(section_id="SEC1")
    section.add_component(_mk_target())
    with pytest.raises(AssemblyReferenceError, match="Missing source node"):
        NodeToNodeJoin(
            operation_id="OP4",
            operation_type="ignored",
            source_component=_mk_source(),
            source_node_name="not_a_node",
            target_component_id="T1",
            target_node_name="top_right",
        ).apply(section)


def test_error_on_missing_target_node():
    section = Section(section_id="SEC1")
    section.add_component(_mk_target())
    with pytest.raises(AssemblyReferenceError, match="Missing target node"):
        NodeToNodeJoin(
            operation_id="OP5",
            operation_type="ignored",
            source_component=_mk_source(),
            source_node_name="bottom_left",
            target_component_id="T1",
            target_node_name="bad_node",
        ).apply(section)


def test_error_on_duplicate_component_id():
    section = Section(section_id="SEC1")
    target = _mk_target()
    source_same_id = RectangularElement.from_bottom_left(
        element_id="T1",
        width=20,
        width_unit="mm",
        height=10,
        height_unit="mm",
        bottom_left_y=200,
        bottom_left_y_unit="mm",
        bottom_left_z=300,
        bottom_left_z_unit="mm",
    )
    section.add_component(target)
    with pytest.raises(AssemblyReferenceError, match="Duplicate component id"):
        NodeToNodeJoin(
            operation_id="OP6",
            operation_type="ignored",
            source_component=source_same_id,
            source_node_name="bottom_left",
            target_component_id="T1",
            target_node_name="top_right",
        ).apply(section)


def test_trace_metadata_contains_translation_and_references():
    section = Section(section_id="SEC1")
    target = _mk_target()
    source = _mk_source()
    section.add_component(target)
    result = NodeToNodeJoin(
        operation_id="OP7",
        operation_type="ignored",
        source_component=source,
        source_node_name="bottom_left",
        target_component_id="T1",
        target_node_name="top_right",
    ).apply(section)

    trace = result.get_component("S1").metadata["assembly"]
    assert trace["operation_id"] == "OP7"
    assert trace["operation_type"] == "node_to_node_join"
    assert trace["source_component_id"] == "S1"
    assert trace["source_node_name"] == "bottom_left"
    assert trace["target_component_id"] == "T1"
    assert trace["target_node_name"] == "top_right"
    assert trace["translation_dy_mm"] == pytest.approx(-100.0)
    assert trace["translation_dz_mm"] == pytest.approx(-250.0)
