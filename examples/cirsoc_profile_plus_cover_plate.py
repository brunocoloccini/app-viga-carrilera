from pathlib import Path

from section_core.assembly import LineToLineJoin
from section_core.components import PlateElement
from section_core.section import Section
from section_core.shapes import load_shape_library_json


def build_section() -> Section:
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)

    ipn_200 = registry.to_component(
        "CIRSOC_IPN_200",
        element_id="ipn_200",
        center_y=0,
        center_z=100,
        center_unit="mm",
    )

    cover_plate = PlateElement.horizontal_plate(
        element_id="cover_plate",
        width=140,
        width_unit="mm",
        thickness=10,
        thickness_unit="mm",
        center_y=0,
        center_y_unit="mm",
        center_z=0,
        center_z_unit="mm",
    )

    section = Section(section_id="V1-019-example", components=[ipn_200])
    section = LineToLineJoin(
        operation_id="OP_COVER_TO_IPN200",
        operation_type="ignored",
        source_component=cover_plate,
        source_line_name="bottom_edge",
        target_component_id="ipn_200",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_type="fillet",
        weld_size_mm=6,
    ).apply(section)
    return section


if __name__ == "__main__":
    section = build_section()
    props = section.gross_elastic_properties()

    print("Component IDs:", section.component_ids())
    print("Interface IDs:", [iface.interface_id for iface in section.interfaces])
    print(f"Gross area [mm2]: {props.area_mm2:.3f}")
    print(f"Centroid [mm]: y={props.centroid_y_mm:.3f}, z={props.centroid_z_mm:.3f}")
    print(f"Iyy [mm4]: {props.Iyy_mm4:.3f}")
    print(f"Izz [mm4]: {props.Izz_mm4:.3f}")
    print(f"Iyz [mm4]: {props.Iyz_mm4:.3f}")
    print(f"S_y_top [mm3]: {props.S_y_top_mm3:.3f}")
    print(f"S_y_bottom [mm3]: {props.S_y_bottom_mm3:.3f}")
    print(f"S_z_left [mm3]: {props.S_z_left_mm3:.3f}")
    print(f"S_z_right [mm3]: {props.S_z_right_mm3:.3f}")
    print(
        "Note: CIRSOC sample data is manually curated and must be independently "
        "verified before production design use."
    )
