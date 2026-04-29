import pytest

from section_core import Section
from section_core.components import LibraryShapeComponent
from section_core.shapes import (
    DuplicateShapeError,
    InvalidShapeRecordError,
    ShapeLibraryRegistry,
    ShapeNotFoundError,
    ShapeRecord,
    build_sample_shape_library_registry,
)


def _record() -> ShapeRecord:
    return ShapeRecord(
        shape_id="W_TEST_1",
        shape_family="W",
        shape_name="W_TEST_1",
        source="tests_fake_data",
        depth_mm=500.0,
        width_mm=200.0,
        area_mm2=15000.0,
        Iyy_mm4=5.0e8,
        Izz_mm4=4.0e7,
    )


def test_shape_record_valid_creation():
    rec = _record()
    assert rec.shape_id == "W_TEST_1"


def test_shape_record_invalid_zero_depth_rejected():
    with pytest.raises(InvalidShapeRecordError):
        ShapeRecord(shape_id="A", shape_family="W", shape_name="W", source="x", depth_mm=0, width_mm=1, area_mm2=1, Iyy_mm4=0, Izz_mm4=0)


def test_shape_record_invalid_negative_area_rejected():
    with pytest.raises(InvalidShapeRecordError):
        ShapeRecord(shape_id="A", shape_family="W", shape_name="W", source="x", depth_mm=1, width_mm=1, area_mm2=-1, Iyy_mm4=0, Izz_mm4=0)


def test_shape_record_from_values_unit_aware_conversion():
    rec = ShapeRecord.from_values(
        shape_id="A",
        shape_family="W",
        shape_name="W_A",
        source="tests_fake_data",
        depth=30,
        depth_unit="cm",
        width=10,
        width_unit="in",
        area=20,
        area_unit="cm2",
        Iyy=10,
        Iyy_unit="in4",
        Izz=12,
        Izz_unit="cm4",
    )
    assert rec.depth_mm == pytest.approx(300.0)
    assert rec.width_mm == pytest.approx(254.0)
    assert rec.area_mm2 == pytest.approx(2000.0)
    assert rec.Iyy_mm4 == pytest.approx(10 * 25.4**4)
    assert rec.Izz_mm4 == pytest.approx(12 * 10000.0)


def test_registry_add_get_duplicate_missing():
    reg = ShapeLibraryRegistry()
    reg.add(_record())
    assert reg.get("W_TEST_1").shape_name == "W_TEST_1"
    with pytest.raises(DuplicateShapeError):
        reg.add(_record())
    with pytest.raises(ShapeNotFoundError):
        reg.get("NOPE")


def test_registry_find_list_methods():
    reg = ShapeLibraryRegistry([
        _record(),
        ShapeRecord(shape_id="IPE_TEST_1", shape_family="IPE", shape_name="IPE_TEST_1", source="tests_fake_data", depth_mm=300, width_mm=150, area_mm2=5000, Iyy_mm4=9e7, Izz_mm4=7e6),
    ])
    assert reg.find_by_name("W", "W_TEST_1").shape_id == "W_TEST_1"
    assert reg.list_families() == ["IPE", "W"]
    assert [x.shape_id for x in reg.list_shapes()] == ["IPE_TEST_1", "W_TEST_1"]
    assert [x.shape_id for x in reg.list_shapes("W")] == ["W_TEST_1"]


def test_to_component_and_section_integration():
    reg = ShapeLibraryRegistry([_record()])
    comp = reg.to_component("W_TEST_1", element_id="LIB1")
    assert isinstance(comp, LibraryShapeComponent)
    assert comp.area_tabulated_mm2 == pytest.approx(15000.0)
    assert comp.Iyy_tabulated_mm4 == pytest.approx(5.0e8)
    assert comp.Izz_tabulated_mm4 == pytest.approx(4.0e7)

    section = Section(section_id="S_REG", components=[comp])
    props = section.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(15000.0)
    assert props.Iyy_mm4 == pytest.approx(5.0e8)
    assert props.Izz_mm4 == pytest.approx(4.0e7)


def test_records_roundtrip():
    reg = ShapeLibraryRegistry([_record()])
    serialized = reg.to_records()
    restored = ShapeLibraryRegistry.from_records(serialized)
    assert restored.get("W_TEST_1").area_mm2 == pytest.approx(15000.0)


def test_sample_registry_includes_fake_test_shape():
    reg = build_sample_shape_library_registry()
    assert reg.has("W_TEST_600")
    assert "FAKE SAMPLE DATA" in reg.get("W_TEST_600").metadata["note"]
