import pytest

from section_core.assembly import LineToLineJoin
from section_core.components import LibraryShapeComponent, PlateElement
from section_core.interfaces import WeldInterface
from section_core.section import Section


def _build_library_shape_plus_cover_plate_section() -> Section:
    base_shape = LibraryShapeComponent.from_tabulated(
        element_id="base_shape",
        shape_family="W_TEST",
        shape_name="W_TEST_600",
        area=30000,
        area_unit="mm2",
        Iyy=1_800_000_000,
        Iyy_unit="mm4",
        Izz=90_000_000,
        Izz_unit="mm4",
        Iyz=0,
        Iyz_unit="mm4",
        center_y=0,
        center_y_unit="mm",
        center_z=300,
        center_z_unit="mm",
        depth=600,
        depth_unit="mm",
        width=200,
        width_unit="mm",
    )

    cover_plate = PlateElement.horizontal_plate(
        element_id="cover_plate",
        width=300,
        width_unit="mm",
        thickness=20,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=0,
        center_z_unit="mm",
    )

    section = Section(section_id="V1-015", components=[base_shape])

    section = LineToLineJoin(
        operation_id="OP_COVER_TO_BASE",
        operation_type="ignored",
        source_component=cover_plate,
        source_line_name="bottom_edge",
        target_component_id="base_shape",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_type="fillet",
        weld_size_mm=6,
    ).apply(section)

    return section


def _expected_values() -> dict[str, float]:
    a_base = 30000.0
    yc_base = 0.0
    zc_base = 300.0
    iyy_base = 1_800_000_000.0
    izz_base = 90_000_000.0

    a_plate = 300.0 * 20.0
    yc_plate = 0.0
    zc_plate = 610.0
    iyy_plate_local = 300.0 * (20.0**3) / 12.0
    izz_plate_local = 20.0 * (300.0**3) / 12.0

    area = a_base + a_plate
    yc = (a_base * yc_base + a_plate * yc_plate) / area
    zc = (a_base * zc_base + a_plate * zc_plate) / area

    iyy = (
        iyy_base
        + a_base * (zc_base - zc) ** 2
        + iyy_plate_local
        + a_plate * (zc_plate - zc) ** 2
    )
    izz = izz_base + izz_plate_local

    return {
        "area": area,
        "yc": yc,
        "zc": zc,
        "iyy": iyy,
        "izz": izz,
        "iyz": 0.0,
        "sy_top": iyy / (620.0 - zc),
        "sy_bottom": iyy / (zc - 0.0),
        "sz": izz / 150.0,
    }


def test_validation_library_shape_plus_cover_plate_geometry_and_properties():
    section = _build_library_shape_plus_cover_plate_section()
    props = section.gross_elastic_properties()
    expected = _expected_values()

    assert len(section.components) == 2
    assert len(section.interfaces) == 1

    y_min, z_min, y_max, z_max = section.bounding_box()
    assert y_min == pytest.approx(-150.0)
    assert y_max == pytest.approx(150.0)
    assert z_min == pytest.approx(0.0)
    assert z_max == pytest.approx(620.0)

    assert props.area_mm2 == pytest.approx(expected["area"])
    assert props.centroid_y_mm == pytest.approx(expected["yc"])
    assert props.centroid_z_mm == pytest.approx(expected["zc"])
    assert props.centroid_z_mm > 300.0

    assert props.Iyy_mm4 == pytest.approx(expected["iyy"], rel=1e-12)
    assert props.Izz_mm4 == pytest.approx(expected["izz"], rel=1e-12)
    assert props.Iyz_mm4 == pytest.approx(expected["iyz"], abs=1e-12)

    assert props.S_y_top_mm3 == pytest.approx(expected["sy_top"], rel=1e-12)
    assert props.S_y_bottom_mm3 == pytest.approx(expected["sy_bottom"], rel=1e-12)
    assert props.S_y_top_mm3 != pytest.approx(props.S_y_bottom_mm3)
    assert props.S_z_left_mm3 == pytest.approx(expected["sz"], rel=1e-12)
    assert props.S_z_right_mm3 == pytest.approx(expected["sz"], rel=1e-12)


def test_validation_library_shape_plus_cover_plate_assembly_interfaces_and_trace():
    section = _build_library_shape_plus_cover_plate_section()
    props = section.gross_elastic_properties()

    by_id = {component.element_id: component for component in section.components}
    assert set(by_id) == {"base_shape", "cover_plate"}

    cover_trace = by_id["cover_plate"].metadata["assembly"]
    assert cover_trace["operation_type"] == "line_to_line_join"
    assert cover_trace["create_connection"] is True

    weld_ifaces = [
        iface for iface in section.interfaces if isinstance(iface, WeldInterface) or iface.interface_type == "weld"
    ]
    assert len(weld_ifaces) == 1

    component_ids = set(section.component_ids())
    iface = weld_ifaces[0]
    assert iface.component_a_id in component_ids
    assert iface.component_b_id in component_ids
    assert {iface.component_a_id, iface.component_b_id} == {"base_shape", "cover_plate"}
    assert iface.verified is False
    assert iface.structural_action_assumed is False
    assert iface.weld_type == "fillet"
    assert iface.weld_size_mm == pytest.approx(6.0)
    assert iface.metadata is not None
    assert "created_by_operation_id" in iface.metadata
    assert "not structurally verified" in iface.metadata.get("note", "")

    trace_ids = {entry["component_id"] for entry in props.trace}
    assert trace_ids == {"base_shape", "cover_plate"}
