import pytest

from section_core.assembly import AssemblyGeometryError, AssemblyReferenceError, LineToLineJoin
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


def test_rotation_alignment_vertical_to_horizontal():
    section = Section(section_id="SEC1", components=[_mk_target()])
    source = _mk_source()

    result = LineToLineJoin(
        operation_id="OP12",
        operation_type="ignored",
        source_component=source,
        source_line_name="left_edge",
        target_component_id="T1",
        target_line_name="top_edge",
        allow_rotation=True,
    ).apply(section)

    joined = result.get_component("S1")
    jline = joined.get_reference_line("left_edge")
    tline = section.get_component("T1").get_reference_line("top_edge")
    assert jline.is_parallel_to(tline, __import__("section_core.geometry", fromlist=["GeometryTolerance"]).GeometryTolerance.default())
    assert joined.width_internal_mm == pytest.approx(source.width_internal_mm)
    assert joined.height_internal_mm == pytest.approx(source.height_internal_mm)
    assert ((joined.rotation_deg - source.rotation_deg) % 360.0) == pytest.approx(270.0)


def test_alignment_modes():
    section = Section(section_id="SEC1", components=[_mk_target()])
    for mode, sp, tp in [
        ("midpoint_to_midpoint", "midpoint", "midpoint"),
        ("start_to_start", "start", "start"),
        ("end_to_end", "end", "end"),
        ("start_to_end", "start", "end"),
        ("end_to_start", "end", "start"),
    ]:
        res = LineToLineJoin(operation_id=f"M_{mode}", operation_type="ignored", source_component=_mk_source("S"+mode), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge", alignment_mode=mode).apply(section)
        line = res.get_component("S"+mode).get_reference_line("bottom_edge")
        tgt = section.get_component("T1").get_reference_line("top_edge")
        src_pt = getattr(line, sp) if sp != "midpoint" else line.midpoint
        tgt_pt = getattr(tgt, tp) if tp != "midpoint" else tgt.midpoint
        assert src_pt.y_internal_mm == pytest.approx(tgt_pt.y_internal_mm)
        assert src_pt.z_internal_mm == pytest.approx(tgt_pt.z_internal_mm)


def test_overlap_modes_and_offsets_and_trace():
    section = Section(section_id="SEC1", components=[_mk_target()])
    for mode in ["centered", "from_target_start", "from_target_end"]:
        res = LineToLineJoin(operation_id=f"O_{mode}", operation_type="ignored", source_component=_mk_source("SO"+mode), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge", overlap_mode=mode, tangential_offset_mm=3.0, normal_offset_mm=2.0).apply(section)
        trace = res.get_component("SO"+mode).metadata["assembly"]
        assert trace["overlap_mode"] == mode
        assert trace["rotation_angle_deg"] == pytest.approx(0.0)
        assert "source_line_length_mm" in trace and "target_line_length_mm" in trace
        assert "translation_dy_mm" in trace and "translation_dz_mm" in trace

    with pytest.raises(AssemblyGeometryError, match="Unsupported overlap mode"):
        LineToLineJoin(operation_id="OP13", operation_type="ignored", source_component=_mk_source("SX"), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge", overlap_mode="bad").apply(section)

    with pytest.raises(AssemblyGeometryError, match="Unsupported alignment mode"):
        LineToLineJoin(operation_id="OP14", operation_type="ignored", source_component=_mk_source("SY"), source_line_name="bottom_edge", target_component_id="T1", target_line_name="top_edge", alignment_mode="bad").apply(section)
