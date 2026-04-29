import json
from pathlib import Path

import pytest

from section_core.crane_runway import (
    CraneRunwayCaseErrorFormatter,
    InvalidCraneRunwayCaseError,
    UserFacingValidationMessage,
    UserFacingValidationReport,
)


def test_message_valid_creation() -> None:
    msg = UserFacingValidationMessage(path="$.span.unit", message="Missing required field 'unit'.", severity="error")
    assert msg.path == "$.span.unit"


def test_message_invalid_severity_rejected() -> None:
    with pytest.raises(ValueError):
        UserFacingValidationMessage(path="$", message="bad", severity="fatal")


def test_report_counts_and_to_text_and_to_dict() -> None:
    report = UserFacingValidationReport(
        valid=False,
        messages=[
            UserFacingValidationMessage(path="$", message="err", severity="error", hint="h1"),
            UserFacingValidationMessage(path="$.a", message="warn", severity="warning"),
            UserFacingValidationMessage(path="$.b", message="info", severity="info"),
        ],
    )
    assert report.error_count() == 1
    assert report.warning_count() == 1
    assert report.info_count() == 1
    assert report.has_errors() is True
    text = report.to_text()
    assert "ERROR $: err" in text
    assert "Hint: h1" in text
    payload = report.to_dict()
    json.dumps(payload)


def test_missing_schema_version_hint() -> None:
    report = CraneRunwayCaseErrorFormatter.validate_case_dict_for_user({})
    assert report.has_errors()
    assert any(m.hint and "schema_version" in m.hint for m in report.messages)


def test_quantity_missing_unit_hint() -> None:
    report = CraneRunwayCaseErrorFormatter.validate_case_dict_for_user({"span": {"value": 10}})
    assert any(m.hint and "quantity objects" in m.hint for m in report.messages)


def test_duplicate_wheel_id_hint() -> None:
    data = {
        "schema_version": "1.0",
        "case_id": "x",
        "shape_library_path": "s.json",
        "base_shape_id": "W1",
        "section": {"section_id": "sec", "base_component_id": "base", "base_center_y": {"value": 0, "unit": "mm"}, "base_center_z": {"value": 0, "unit": "mm"}},
        "span": {"value": 5, "unit": "m"},
        "analysis": {"movement_step": {"value": 0.1, "unit": "m"}, "station_step": {"value": 0.1, "unit": "m"}, "E": {"value": 200000, "unit": "MPa"}},
        "crane": {"crane_id": "c", "wheels": [{"wheel_id": "w1", "position_x": {"value": 0, "unit": "m"}, "vertical_force": {"value": 10, "unit": "kN"}}, {"wheel_id": "w1", "position_x": {"value": 1, "unit": "m"}, "vertical_force": {"value": 10, "unit": "kN"}}]},
    }
    report = CraneRunwayCaseErrorFormatter.validate_case_dict_for_user(data)
    assert any(m.hint and "unique wheel_id" in m.hint for m in report.messages)


def test_limit_and_rail_hints() -> None:
    data = {
        "schema_version": "1.0", "case_id": "x", "shape_library_path": "s.json", "base_shape_id": "W1",
        "section": {"section_id": "sec", "base_component_id": "base", "base_center_y": {"value": 0, "unit": "mm"}, "base_center_z": {"value": 0, "unit": "mm"}},
        "span": {"value": 5, "unit": "m"},
        "analysis": {"movement_step": {"value": 0.1, "unit": "m"}, "station_step": {"value": 0.1, "unit": "m"}, "E": {"value": 200000, "unit": "MPa"}},
        "crane": {"crane_id": "c", "wheels": [{"wheel_id": "w1", "position_x": {"value": 0, "unit": "m"}, "vertical_force": {"value": 10, "unit": "kN"}}]},
        "serviceability_limits": [{"limit_id": "d", "type": "bogus"}],
        "stress_limits": [{"limit_id": "s", "type": "bogus"}],
        "rail_eccentricity": {"enabled": True, "model_id": "r", "vertical_eccentricity_y": {"value": 1, "unit": "mm"}, "lateral_load_height_z": {"value": 1, "unit": "mm"}, "include_vertical": False, "include_lateral": False},
    }
    report = CraneRunwayCaseErrorFormatter.validate_case_dict_for_user(data)
    hints = [m.hint for m in report.messages if m.hint]
    assert any("serviceability limit types" in h for h in hints)
    assert any("stress limit types" in h for h in hints)
    assert any("include_vertical or include_lateral" in h for h in hints)


def test_valid_case_file_report() -> None:
    report = CraneRunwayCaseErrorFormatter.validate_case_json_for_user("examples/crane_runway_case_demo.json")
    assert report.valid is True
    assert report.error_count() == 0


def test_json_handling() -> None:
    missing = CraneRunwayCaseErrorFormatter.validate_case_json_for_user("does/not/exist.json")
    assert missing.has_errors()
    assert missing.messages[0].code in {"CASE_JSON_ERROR", "CASE_IO_ERROR"}


def test_malformed_json_and_valid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    report_bad = CraneRunwayCaseErrorFormatter.validate_case_json_for_user(bad)
    assert report_bad.has_errors()
    assert report_bad.messages[0].code == "CASE_JSON_ERROR"

    ok = tmp_path / "ok.json"
    ok.write_text(Path("examples/crane_runway_case_demo.json").read_text(encoding="utf-8"), encoding="utf-8")
    report_ok = CraneRunwayCaseErrorFormatter.validate_case_json_for_user(ok)
    assert report_ok.valid is True


def test_exception_mapping() -> None:
    report1 = CraneRunwayCaseErrorFormatter.from_exception(InvalidCraneRunwayCaseError("bad case"))
    assert report1.messages[0].code in {"CASE_IO_ERROR", "CASE_SCHEMA_ERROR"}

    report2 = CraneRunwayCaseErrorFormatter.from_exception(Exception("boom"))
    assert report2.messages[0].code == "CASE_UNKNOWN_ERROR"
