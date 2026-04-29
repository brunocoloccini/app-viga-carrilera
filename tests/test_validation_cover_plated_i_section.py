import pytest

from section_core.assembly import LineToLineJoin
from section_core.components import PlateElement
from section_core.interfaces import WeldInterface
from section_core.section import Section


def _build_cover_plated_i_section() -> Section:
    bottom_flange = PlateElement.horizontal_plate(
        element_id="bottom_flange",
        width=200,
        width_unit="mm",
        thickness=20,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=10,
        center_z_unit="mm",
    )

    web = PlateElement.vertical_plate(
        element_id="web",
        height=300,
        height_unit="mm",
        thickness=10,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=0,
        center_z_unit="mm",
    )

    top_flange = PlateElement.horizontal_plate(
        element_id="top_flange",
        width=200,
        width_unit="mm",
        thickness=20,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=0,
        center_z_unit="mm",
    )

    cover_plate = PlateElement.horizontal_plate(
        element_id="cover_plate",
        width=260,
        width_unit="mm",
        thickness=10,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=0,
        center_z_unit="mm",
    )

    section = Section(section_id="V1-013", components=[bottom_flange])

    section = LineToLineJoin(
        operation_id="OP_WEB_TO_BOTTOM",
        operation_type="ignored",
        source_component=web,
        source_line_name="bottom_edge",
        target_component_id="bottom_flange",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_type="fillet",
        weld_size_mm=6,
    ).apply(section)

    section = LineToLineJoin(
        operation_id="OP_TOP_TO_WEB",
        operation_type="ignored",
        source_component=top_flange,
        source_line_name="bottom_edge",
        target_component_id="web",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_type="fillet",
        weld_size_mm=6,
    ).apply(section)

    section = LineToLineJoin(
        operation_id="OP_COVER_TO_TOP",
        operation_type="ignored",
        source_component=cover_plate,
        source_line_name="bottom_edge",
        target_component_id="top_flange",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_type="fillet",
        weld_size_mm=6,
    ).apply(section)

    return section


def _expected_values() -> dict[str, float]:
    a_bottom = 200.0 * 20.0
    a_web = 10.0 * 300.0
    a_top = 200.0 * 20.0
    a_cover = 260.0 * 10.0
    area = a_bottom + a_web + a_top + a_cover

    yc = 0.0
    zc = (a_bottom * 10.0 + a_web * 170.0 + a_top * 330.0 + a_cover * 345.0) / area

    iyy_bottom_local = 200.0 * (20.0**3) / 12.0
    iyy_web_local = 10.0 * (300.0**3) / 12.0
    iyy_top_local = 200.0 * (20.0**3) / 12.0
    iyy_cover_local = 260.0 * (10.0**3) / 12.0
    iyy = (
        iyy_bottom_local + a_bottom * (10.0 - zc) ** 2
        + iyy_web_local + a_web * (170.0 - zc) ** 2
        + iyy_top_local + a_top * (330.0 - zc) ** 2
        + iyy_cover_local + a_cover * (345.0 - zc) ** 2
    )

    izz_bottom_local = 20.0 * (200.0**3) / 12.0
    izz_web_local = 300.0 * (10.0**3) / 12.0
    izz_top_local = 20.0 * (200.0**3) / 12.0
    izz_cover_local = 10.0 * (260.0**3) / 12.0
    izz = izz_bottom_local + izz_web_local + izz_top_local + izz_cover_local

    return {
        "area": area,
        "yc": yc,
        "zc": zc,
        "iyy": iyy,
        "izz": izz,
        "iyz": 0.0,
        "sy_top": iyy / (350.0 - zc),
        "sy_bottom": iyy / (zc - 0.0),
        "sz": izz / 130.0,
    }


def test_validation_cover_plated_i_geometry_and_properties():
    section = _build_cover_plated_i_section()
    props = section.gross_elastic_properties()
    expected = _expected_values()

    assert len(section.components) == 4
    assert len(section.interfaces) == 3

    y_min, z_min, y_max, z_max = section.bounding_box()
    assert y_min == pytest.approx(-130.0)
    assert y_max == pytest.approx(130.0)
    assert z_min == pytest.approx(0.0)
    assert z_max == pytest.approx(350.0)

    assert props.area_mm2 == pytest.approx(expected["area"])
    assert props.centroid_y_mm == pytest.approx(expected["yc"])
    assert props.centroid_z_mm == pytest.approx(expected["zc"])
    assert props.centroid_z_mm > 170.0

    assert props.Iyy_mm4 == pytest.approx(expected["iyy"], rel=1e-12)
    assert props.Izz_mm4 == pytest.approx(expected["izz"], rel=1e-12)
    assert props.Iyz_mm4 == pytest.approx(expected["iyz"], abs=1e-12)

    assert props.S_y_top_mm3 == pytest.approx(expected["sy_top"], rel=1e-12)
    assert props.S_y_bottom_mm3 == pytest.approx(expected["sy_bottom"], rel=1e-12)
    assert props.S_y_top_mm3 != pytest.approx(props.S_y_bottom_mm3)
    assert props.S_z_left_mm3 == pytest.approx(expected["sz"], rel=1e-12)
    assert props.S_z_right_mm3 == pytest.approx(expected["sz"], rel=1e-12)


def test_validation_cover_plated_i_assembly_interfaces_and_trace():
    section = _build_cover_plated_i_section()
    props = section.gross_elastic_properties()

    by_id = {component.element_id: component for component in section.components}
    assert set(by_id) == {"bottom_flange", "web", "top_flange", "cover_plate"}

    web_trace = by_id["web"].metadata["assembly"]
    top_trace = by_id["top_flange"].metadata["assembly"]
    cover_trace = by_id["cover_plate"].metadata["assembly"]

    assert web_trace["operation_type"] == "line_to_line_join"
    assert top_trace["operation_type"] == "line_to_line_join"
    assert cover_trace["operation_type"] == "line_to_line_join"
    assert web_trace["create_connection"] is True
    assert top_trace["create_connection"] is True
    assert cover_trace["create_connection"] is True

    weld_ifaces = [
        iface for iface in section.interfaces if isinstance(iface, WeldInterface) or iface.interface_type == "weld"
    ]
    assert len(weld_ifaces) == 3

    component_ids = set(section.component_ids())
    for iface in weld_ifaces:
        assert iface.component_a_id in component_ids
        assert iface.component_b_id in component_ids
        assert iface.verified is False
        assert iface.structural_action_assumed is False
        assert iface.weld_type == "fillet"
        assert iface.weld_size_mm == pytest.approx(6.0)
        assert iface.metadata is not None
        assert "created_by_operation_id" in iface.metadata
        assert "not structurally verified" in iface.metadata.get("note", "")

    trace_ids = {entry["component_id"] for entry in props.trace}
    assert trace_ids == {"bottom_flange", "web", "top_flange", "cover_plate"}
