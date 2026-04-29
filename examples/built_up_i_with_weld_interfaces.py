from section_core.assembly import LineToLineJoin
from section_core.components import PlateElement
from section_core.section import Section


def build_built_up_i_section() -> Section:
    bottom_flange = PlateElement.horizontal_plate(
        element_id="bottom_flange", width=200, width_unit="mm", thickness=20, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=10, center_z_unit="mm"
    )
    web = PlateElement.vertical_plate(
        element_id="web", height=300, height_unit="mm", thickness=10, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    top_flange = PlateElement.horizontal_plate(
        element_id="top_flange", width=200, width_unit="mm", thickness=20, thickness_unit="mm", center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )

    section = Section(section_id="V1-012-example", components=[bottom_flange])
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
    return section


if __name__ == "__main__":
    built_up_i = build_built_up_i_section()
    props = built_up_i.gross_elastic_properties()

    print("Component IDs:", built_up_i.component_ids())
    print("Interface IDs:", built_up_i.interface_ids())
    print(f"Gross area [mm^2]: {props.area_mm2:.3f}")
    print(f"Centroid [mm]: y={props.centroid_y_mm:.3f}, z={props.centroid_z_mm:.3f}")
    print(f"Iyy [mm^4]: {props.Iyy_mm4:.3f}")
    print(f"Izz [mm^4]: {props.Izz_mm4:.3f}")
    print(f"Iyz [mm^4]: {props.Iyz_mm4:.3f}")
    print(f"S_y_top [mm^3]: {props.S_y_top_mm3:.3f}")
    print(f"S_y_bottom [mm^3]: {props.S_y_bottom_mm3:.3f}")
    print(f"S_z_left [mm^3]: {props.S_z_left_mm3:.3f}")
    print(f"S_z_right [mm^3]: {props.S_z_right_mm3:.3f}")
