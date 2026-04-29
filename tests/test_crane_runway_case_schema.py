from __future__ import annotations

import json
from pathlib import Path

import pytest

from section_core.crane_runway import (
    CASE_SCHEMA_VERSION,
    InvalidCraneRunwayCaseError,
    assert_valid_crane_runway_case_dict,
    get_crane_runway_case_schema_v1,
    load_crane_runway_case_json,
    run_crane_runway_case_dict,
    run_crane_runway_case_json,
    validate_crane_runway_case_dict,
    write_crane_runway_case_schema_v1,
)


def _demo_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "crane_runway_case_demo.json"


def _demo() -> dict:
    return load_crane_runway_case_json(_demo_path())


def test_schema_export(tmp_path: Path):
    schema = get_crane_runway_case_schema_v1()
    assert isinstance(schema, dict)
    assert schema["x-schema-version"] == CASE_SCHEMA_VERSION

    out = tmp_path / "schema.json"
    write_crane_runway_case_schema_v1(out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["x-schema-version"] == CASE_SCHEMA_VERSION


def test_demo_schema_valid_strict():
    demo = _demo()
    assert demo["schema_version"] == CASE_SCHEMA_VERSION
    result = validate_crane_runway_case_dict(demo, strict=True)
    assert result.valid
    assert_valid_crane_runway_case_dict(demo, strict=True)


def test_validation_basics():
    assert not validate_crane_runway_case_dict([], strict=True).valid

    demo = _demo()
    bad = dict(demo)
    bad.pop("schema_version")
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = dict(demo)
    bad["schema_version"] = "9.9"
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    for k in ["case_id", "shape_library_path", "span"]:
        bad = dict(demo)
        bad.pop(k)
        assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["span"] = {"value": 1.0}
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["analysis"].pop("movement_step")
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["crane"].pop("wheels")
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["crane"]["wheels"] = []
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["crane"]["wheels"][1]["wheel_id"] = bad["crane"]["wheels"][0]["wheel_id"]
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["serviceability_limits"] = [{"limit_id": "x", "type": "unknown"}]
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["stress_limits"] = [{"limit_id": "x", "type": "unknown"}]
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _demo()
    bad["rail_eccentricity"]["include_vertical"] = False
    bad["rail_eccentricity"]["include_lateral"] = False
    assert not validate_crane_runway_case_dict(bad, strict=True).valid


def test_case_io_integration_and_backward_compatibility():
    demo = _demo()
    assert run_crane_runway_case_dict(demo).case_id == "demo_case"
    assert run_crane_runway_case_json(_demo_path()).case_id == "demo_case"

    bad = dict(demo)
    bad.pop("schema_version")
    res = validate_crane_runway_case_dict(bad, strict=False)
    assert res.valid
    assert res.warning_count() > 0

    with pytest.raises(InvalidCraneRunwayCaseError):
        run_crane_runway_case_dict(bad)
