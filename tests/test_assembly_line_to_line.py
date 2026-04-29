import pytest

from section_core.assembly import AssemblyGeometryError, AssemblyReferenceError, LineToLineJoin
from section_core.components import PlateElement, RectangularElement
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


def test_basic_midpoint_alignment_bottom_to_top_edge():
    section = Section(section_id="SEC1")
    target = _mk_target()
    source = _mk_source()
    section.add_component(target)

    result = LineToLineJoin(
        operation_id="OP1",
        operation_type="ignored",
        source_component=source,
        source_line_name="bottom_edge",
        target_component_id="T1",
        target_line_name="top_edge",
    ).apply(section)

    joined = result.get_component("S1")
    assert joined.get_reference_line("bottom_edge").midpoint.y_internal_mm == pytest.approx(target.get_reference_line("top_edge").midpoint.y_internal_mm)
    assert joined.get_reference_line("bottom_edge").midpoint.z_internal_mm == pytest.approx(target.get_reference_line("top_edge").midpoint.z_internal_mm)


def test_offsets_follow_tangent_and_normal_convention():
    section = Section(section_id="SEC1", components=[_mk_target()])
    source = _mk_source()

    result = LineToLineJoin(
        operation_id="OP2",
        operation_type="ignored",
        source_component=source,
        source_line_name="bottom_edge",
        target_component_id="T1",
        target_line_name="top_edge",
        tangential_offset_mm=15.0,
        normal_offset_mm=7.0,
    ).apply(section)

    joined_mid = result.get_component("S1").get_reference_line("bottom_edge").midpoint
    target_mid = section.get_component("T1").get_reference_line("top_edge").midpoint
    ty, tz = section.get_component("T1").get_reference_line("top_edge").direction
    ny, nz = -tz, ty

    assert joined_mid.y_internal_mm == pytest.approx(target_mid.y_internal_mm + 15.0 * ty + 7.0 * ny)
    assert joined_mid.z_internal_mm == pytest.approx(target_mid.z_internal_mm + 15.0 * tz + 7.0 * nz)


def test_geometry_preservation_and_section_integration():
    target = _mk_target()
    source = _mk_source()
    section = Section(section_id="SEC1", components=[target])

    result = LineToLineJoin(
        operation_id="OP3",
        operation_type="ignored",
        source_component=source,
        source_line_name="left_edge",
        target_component_id="T1",
        target_line_name="right_edge",
    ).apply(section)

    joined = result.get_component("S1")
    assert joined.width_internal_mm == pytest.approx(source.width_internal_mm)
    assert joined.height_internal_mm == pytest.approx(source.height_internal_mm)
    assert joined.area_mm2() == pytest.approx(source.area_mm2())

    source_lengths = sorted(line.length_mm for line in source.lines())
    joined_lengths = sorted(line.length_mm for line in joined.lines())
    assert joined_lengths == pytest.approx(source_lengths)

    assert result.has_component("T1") and result.has_component("S1")
    assert result.gross_area_mm2() == pytest.approx(target.area_mm2() + source.area_mm2())


def test_errors_for_missing_references_parallelism_mode_duplicate_and_invalid_type():
    section = Section(section_id="SEC1", components=[_mk_target()])

    with pytest.raises(AssemblyReferenceError, match="Missing target component"):
        LineToLineJoin(operation_id="OP4", operation_type="ignored", source_component=_mk_source(), source_line_name="bottom_edge", target_component_id="MISSING", target_line_name="top_edge").apply(section)

    with pytest.raises(AssemblyReferenceError, match="Missing source line"):
        LineToLineJoin(operation_id="OP5", operation_type="ignored", source_component=_mk_source(), source_line_name="bad_line", target_component_id="T1", target_line_name="top_edge").apply(section)

    with pytest.raises(AssemblyReferenceError, match="Missing target line"):
        LineToLineJoin(operation_id="OP6", operation_type="ignored", source_component=_mk_source(), source_line_name="bottom_edge", target_component_id="T1", target_line_name="bad_line").apply(section)

    with pytest.raises(AssemblyGeometryError, match="not parallel/anti-parallel"):
        LineToLineJoin(operation_id="OP7", operation_type="ignored", source_component=_mk_source(), source_line_name="left_edge", target_component_id="T1", target_line_name="top_edge").apply(section)

    with pytest.raises(AssemblyGeometryError, match="Unsupported alignment mode"):
        LineToLineJoin(operation_id="OP8", operation_type="ignored", source_component=_mk_source(), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge", alignment_mode="start_to_start").apply(section)

    with pytest.raises(AssemblyReferenceError, match="Duplicate component id"):
        LineToLineJoin(operation_id="OP9", operation_type="ignored", source_component=_mk_source(element_id="T1"), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge").apply(section)

    with pytest.raises(AssemblyGeometryError, match="Invalid source component type"):
        LineToLineJoin(operation_id="OP10", operation_type="ignored", source_component=object(), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge").apply(section)


def test_trace_metadata_contains_required_fields():
    section = Section(section_id="SEC1", components=[_mk_target()])
    result = LineToLineJoin(
        operation_id="OP11",
        operation_type="ignored",
        source_component=_mk_source(),
        source_line_name="bottom_edge",
        target_component_id="T1",
        target_line_name="top_edge",
        tangential_offset_mm=5.0,
        normal_offset_mm=2.0,
        create_connection=False,
    ).apply(section)

    trace = result.get_component("S1").metadata["assembly"]
    assert trace["operation_id"] == "OP11"
    assert trace["source_line_name"] == "bottom_edge"
    assert trace["target_line_name"] == "top_edge"
    assert trace["normal_offset_mm"] == pytest.approx(2.0)
    assert trace["tangential_offset_mm"] == pytest.approx(5.0)
    assert "translation_dy_mm" in trace and "translation_dz_mm" in trace
