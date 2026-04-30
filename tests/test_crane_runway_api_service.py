from __future__ import annotations

import json
from pathlib import Path

from section_core.crane_runway import CraneRunwayApiService


def _demo_case_dict() -> dict:
    return json.loads(Path("examples/crane_runway_case_demo.json").read_text(encoding="utf-8"))


def test_validate_case_dict_valid() -> None:
    svc = CraneRunwayApiService()
    result = svc.validate_case_dict(_demo_case_dict())
    assert result.valid is True


def test_validate_case_dict_invalid_missing_schema_version() -> None:
    svc = CraneRunwayApiService()
    bad = _demo_case_dict()
    bad.pop("schema_version", None)
    result = svc.validate_case_dict(bad)
    assert result.valid is False
    assert any("schema_version" in (m.get("path", "") + m.get("message", "") + str(m.get("hint", ""))) for m in result.messages)


def test_validate_case_json_text_valid_and_malformed() -> None:
    svc = CraneRunwayApiService()
    ok = svc.validate_case_json_text(json.dumps(_demo_case_dict()))
    assert ok.valid is True

    bad = svc.validate_case_json_text("{bad json")
    assert bad.valid is False
    assert any("json" in (m.get("code", "") + m.get("message", "")).lower() for m in bad.messages)


def test_execute_case_dict_summary_only() -> None:
    svc = CraneRunwayApiService()
    result = svc.execute_case_dict(_demo_case_dict(), output_formats=["summary"])
    assert result.success is True
    assert isinstance(result.summary, dict)
    assert "max_vertical_moment_Nmm" in result.summary


def test_execute_case_dict_all_reports() -> None:
    svc = CraneRunwayApiService()
    result = svc.execute_case_dict(_demo_case_dict(), output_formats=["summary", "text", "markdown", "html"])
    assert result.success is True
    assert result.summary is not None
    assert "Crane Runway Demand Summary" in (result.text_report or "")
    assert "# Crane Runway Demand Summary" in (result.markdown_report or "")
    assert "<!doctype html>" in (result.html_report or "").lower()


def test_execute_case_dict_invalid_case() -> None:
    svc = CraneRunwayApiService()
    bad = _demo_case_dict()
    bad.pop("schema_version", None)
    result = svc.execute_case_dict(bad)
    assert result.success is False
    assert result.validation is not None
    assert result.validation.valid is False
    assert result.errors


def test_execute_case_json_text_valid_and_malformed() -> None:
    svc = CraneRunwayApiService()
    ok = svc.execute_case_json_text(json.dumps(_demo_case_dict()))
    assert ok.success is True

    bad = svc.execute_case_json_text("{bad json")
    assert bad.success is False


def test_execute_defaults_and_unknown_output() -> None:
    svc = CraneRunwayApiService()
    default = svc.execute_case_dict(_demo_case_dict())
    assert default.success is True
    assert isinstance(default.summary, dict)

    bad_format = svc.execute_case_dict(_demo_case_dict(), output_formats=["pdf"])
    assert bad_format.success is False
    assert any("unsupported output format" in e.get("message", "").lower() for e in bad_format.errors)


def test_serialization() -> None:
    svc = CraneRunwayApiService()
    v = svc.validate_case_dict(_demo_case_dict())
    e = svc.execute_case_dict(_demo_case_dict(), output_formats=["summary"])
    json.dumps(v.to_dict())
    json.dumps(e.to_dict())
