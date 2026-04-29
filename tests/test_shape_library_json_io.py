import json

import pytest

from section_core import Section
from section_core.shapes import (
    InvalidShapeLibraryFileError,
    ShapeLibraryRegistry,
    dump_shape_library_json,
    load_shape_library_json,
    registry_from_json_dict,
    registry_to_json_dict,
)


def _sample_json_dict() -> dict:
    return {
        "library_id": "sample_shapes",
        "name": "Sample Shape Library",
        "source": "test_data",
        "version": "0.1.0",
        "unit_system": "mixed_explicit",
        "description": "Fake sample data for tests only.",
        "records": [
            {
                "shape_id": "W_TEST_600",
                "shape_family": "W_TEST",
                "shape_name": "W_TEST_600",
                "source": "test_data",
                "depth": {"value": 600, "unit": "mm"},
                "width": {"value": 200, "unit": "mm"},
                "area": {"value": 30000, "unit": "mm2"},
                "Iyy": {"value": 1_800_000_000, "unit": "mm4"},
                "Izz": {"value": 90_000_000, "unit": "mm4"},
                "Iyz": {"value": 0, "unit": "mm4"},
                "Cw": {"value": 0, "unit": "mm6"},
                "J": {"value": 0, "unit": "mm4"},
                "metadata": {"is_sample": True, "is_real_profile": False},
            },
            {
                "shape_id": "IPE_TEST_300",
                "shape_family": "IPE_TEST",
                "shape_name": "IPE_TEST_300",
                "source": "test_data",
                "depth": {"value": 300, "unit": "mm"},
                "width": {"value": 150, "unit": "mm"},
                "area": {"value": 5300, "unit": "mm2"},
                "Iyy": {"value": 84_000_000, "unit": "mm4"},
                "Izz": {"value": 6_300_000, "unit": "mm4"},
            },
        ],
    }


def test_registry_from_json_dict_loads_valid_sample_dict():
    registry = registry_from_json_dict(_sample_json_dict())
    assert isinstance(registry, ShapeLibraryRegistry)
    assert registry.has("W_TEST_600")
    assert registry.has("IPE_TEST_300")


def test_registry_to_json_dict_exports_expected_top_level_keys():
    payload = registry_to_json_dict(registry_from_json_dict(_sample_json_dict()))
    assert {"library_id", "name", "source", "version", "unit_system", "description", "records"}.issubset(payload.keys())


def test_roundtrip_dict_registry_dict_registry_preserves_records():
    first = registry_from_json_dict(_sample_json_dict())
    dumped = registry_to_json_dict(first, library_metadata={"library_id": "roundtrip"})
    second = registry_from_json_dict(dumped)
    assert [x.shape_id for x in first.list_shapes()] == [x.shape_id for x in second.list_shapes()]
    assert second.get("W_TEST_600").Iyy_mm4 == pytest.approx(first.get("W_TEST_600").Iyy_mm4)


def test_file_load_dump_reload_roundtrip(tmp_path):
    source_path = tmp_path / "sample.json"
    source_path.write_text(json.dumps(_sample_json_dict()), encoding="utf-8")

    loaded = load_shape_library_json(source_path)
    out_path = tmp_path / "out.json"
    dump_shape_library_json(loaded, out_path, library_metadata={"library_id": "tmp"})

    reloaded = load_shape_library_json(out_path)
    assert [x.shape_id for x in loaded.list_shapes()] == [x.shape_id for x in reloaded.list_shapes()]
    assert reloaded.get("IPE_TEST_300").area_mm2 == pytest.approx(5300)


def test_units_cm_converted_to_internal_mm_units():
    payload = _sample_json_dict()
    payload["records"][0]["area"] = {"value": 300, "unit": "cm2"}
    payload["records"][0]["Iyy"] = {"value": 180000, "unit": "cm4"}
    payload["records"][0]["Cw"] = {"value": 18, "unit": "cm6"}

    registry = registry_from_json_dict(payload)
    rec = registry.get("W_TEST_600")
    assert rec.area_mm2 == pytest.approx(30000)
    assert rec.Iyy_mm4 == pytest.approx(1_800_000_000)
    assert rec.Cw_mm6 == pytest.approx(18_000_000)


def test_units_cw_cm4_rejected():
    payload = _sample_json_dict()
    payload["records"][0]["Cw"] = {"value": 1, "unit": "cm4"}
    with pytest.raises(InvalidShapeLibraryFileError):
        registry_from_json_dict(payload)


@pytest.mark.parametrize(
    "bad_payload",
    [
        {},
        {"records": "not-a-list"},
        {"records": [{"shape_id": "X"}]},
        {
            "records": [
                {
                    "shape_id": "X",
                    "shape_family": "W",
                    "shape_name": "X",
                    "source": "t",
                    "depth": {"value": 1, "unit": "mm"},
                    "width": {"value": 1, "unit": "mm"},
                    "area": {"value": 1, "unit": "bad"},
                    "Iyy": {"value": 1, "unit": "mm4"},
                    "Izz": {"value": 1, "unit": "mm4"},
                }
            ]
        },
        {
            "records": [
                {
                    "shape_id": "DUP",
                    "shape_family": "W",
                    "shape_name": "DUP",
                    "source": "t",
                    "depth": {"value": 1, "unit": "mm"},
                    "width": {"value": 1, "unit": "mm"},
                    "area": {"value": 1, "unit": "mm2"},
                    "Iyy": {"value": 1, "unit": "mm4"},
                    "Izz": {"value": 1, "unit": "mm4"},
                },
                {
                    "shape_id": "DUP",
                    "shape_family": "W",
                    "shape_name": "DUP2",
                    "source": "t",
                    "depth": {"value": 2, "unit": "mm"},
                    "width": {"value": 2, "unit": "mm"},
                    "area": {"value": 2, "unit": "mm2"},
                    "Iyy": {"value": 2, "unit": "mm4"},
                    "Izz": {"value": 2, "unit": "mm4"},
                },
            ]
        },
    ],
)
def test_invalid_payloads_rejected(bad_payload):
    with pytest.raises(InvalidShapeLibraryFileError):
        registry_from_json_dict(bad_payload)


def test_loaded_registry_to_component_integrates_with_section():
    registry = registry_from_json_dict(_sample_json_dict())
    component = registry.to_component("W_TEST_600", element_id="L1")
    section = Section(section_id="SEC", components=[component])
    props = section.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(30000)
    assert props.Iyy_mm4 == pytest.approx(1_800_000_000)
