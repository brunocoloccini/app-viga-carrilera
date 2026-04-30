import pytest

from section_core.rails import (
    CraneRailRecord,
    CraneRailRegistry,
    DuplicateRailRecordError,
    InvalidRailRecordError,
    RailRecordNotFoundError,
    build_sample_crane_rail_registry,
)


def _sample_record() -> CraneRailRecord:
    return CraneRailRecord.from_values(
        rail_id="R1",
        rail_name="Rail 1",
        rail_family="TEST_RAIL",
        source="unit_test",
        height=100,
        height_unit="mm",
        head_width=50,
        head_width_unit="mm",
        base_width=100,
        base_width_unit="mm",
        area=5000,
        area_unit="mm2",
        weight_per_length=39.25,
        weight_per_length_unit="kg/m",
        Ixx=8_000_000,
        Iyy=1_000_000,
        Sxx_head=120_000,
        Sxx_base=100_000,
        Syy=40_000,
        centroid_from_base=45,
    )


def test_crane_rail_record_direct_valid_creation() -> None:
    record = CraneRailRecord(
        rail_id="R1", rail_name="Rail 1", rail_family="TEST_RAIL", source="src",
        height_internal_mm=100, head_width_internal_mm=50, base_width_internal_mm=100,
        area_internal_mm2=5000, weight_per_length_internal_kg_per_m=39.25
    )
    assert record.rail_id == "R1"


def test_metadata_defaults_empty_dict() -> None:
    assert _sample_record().metadata == {}


def test_is_sample_and_requires_verification() -> None:
    record = _sample_record()
    assert not record.is_sample()
    assert not record.requires_verification()

    flagged = CraneRailRecord(**{**record.to_dict(), "metadata": {"sample_rail": True, "requires_independent_verification_before_design_use": True}})
    assert flagged.is_sample()
    assert flagged.requires_verification()


def test_to_dict_json_friendly() -> None:
    data = _sample_record().to_dict()
    assert isinstance(data, dict)
    assert data["rail_id"] == "R1"


def test_invalid_required_and_numeric_fields_rejected() -> None:
    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord("", "n", "f", "s", 1, 1, 1, 1, 1)
    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord("R", "n", "f", "s", 0, 1, 1, 1, 1)
    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord("R", "n", "f", "s", 1, 1, 1, -1, 1)
    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord("R", "n", "f", "s", 1, 1, 1, 1, 1, Ixx_internal_mm4=-1)


def test_from_values_unit_conversions_and_invalid_units() -> None:
    mm = _sample_record()
    assert mm.height_internal_mm == pytest.approx(100)

    cm = CraneRailRecord.from_values("R2", "Rail 2", "TEST_RAIL", "s", 10, "cm", 5, "cm", 10, "cm", 50, "cm2", 39.25, "kg/m", Ixx=800, Ixx_unit="cm4", Sxx_head=120, Sxx_head_unit="cm3")
    assert cm.height_internal_mm == pytest.approx(100)
    assert cm.area_internal_mm2 == pytest.approx(5000)
    assert cm.Ixx_internal_mm4 == pytest.approx(8_000_000)
    assert cm.Sxx_head_internal_mm3 == pytest.approx(120_000)

    inch = CraneRailRecord.from_values("R3", "Rail 3", "TEST_RAIL", "s", 1, "in", 2, "in", 3, "in", 10, "in2", 10, "kg/m")
    assert inch.height_internal_mm == pytest.approx(25.4)

    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord.from_values("R4", "Rail 4", "TEST_RAIL", "s", 1, "N", 1, "mm", 1, "mm", 1, "mm2", 1, "kg/m")
    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord.from_values("R5", "Rail 5", "TEST_RAIL", "s", 1, "mm", 1, "mm", 1, "mm", 1, "MPa", 1, "kg/m")
    with pytest.raises(InvalidRailRecordError):
        CraneRailRecord.from_values("R6", "Rail 6", "TEST_RAIL", "s", 1, "mm", 1, "mm", 1, "mm", 1, "mm2", 1, "kg/m", Sxx_head=1, Sxx_head_unit="mm4")


def test_registry_operations_and_roundtrips() -> None:
    record = _sample_record()
    registry = CraneRailRegistry()
    registry.add(record)
    assert registry.has("R1")
    assert registry.get("R1") == record

    with pytest.raises(DuplicateRailRecordError):
        registry.add(record)
    with pytest.raises(RailRecordNotFoundError):
        registry.get("MISSING")

    assert registry.list_rail_ids() == ["R1"]
    assert "TEST_RAIL" in registry.list_families()
    assert registry.list_by_family("TEST_RAIL") == [record]

    rebuilt = CraneRailRegistry.from_records([record])
    assert rebuilt.to_records() == registry.to_records()

    roundtrip = CraneRailRegistry.from_dict(registry.to_dict())
    assert roundtrip.to_dict()["records"] == registry.to_dict()["records"]

    with pytest.raises(InvalidRailRecordError):
        CraneRailRegistry.from_records([{"rail_id": "bad"}])


def test_sample_registry_contains_fake_records() -> None:
    registry = build_sample_crane_rail_registry()
    assert registry.has("RAIL_TEST_A")
    assert registry.has("RAIL_TEST_B")
    for rail_id in ["RAIL_TEST_A", "RAIL_TEST_B"]:
        record = registry.get(rail_id)
        assert record.is_sample()
        assert record.metadata["is_real_profile"] is False
        assert record.requires_verification()

    serialized = registry.to_dict()
    rebuilt = CraneRailRegistry.from_dict(serialized)
    assert rebuilt.has("RAIL_TEST_A") and rebuilt.has("RAIL_TEST_B")
