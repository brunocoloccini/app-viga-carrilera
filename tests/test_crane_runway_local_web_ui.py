from __future__ import annotations

import json

import pytest

from section_core.crane_runway.local_web_ui import (
    CraneRunwayLocalWebUi,
    InvalidLocalWebUiRequestError,
    LocalWebUiResponse,
)


def test_local_web_ui_response_valid_and_body_bytes() -> None:
    response = LocalWebUiResponse(status_code=200, content_type="application/json", body="ok")
    assert response.status_code == 200
    assert response.body_bytes() == b"ok"


def test_local_web_ui_response_invalid_status_rejected() -> None:
    with pytest.raises(InvalidLocalWebUiRequestError):
        LocalWebUiResponse(status_code=0, content_type="application/json", body="ok")


def test_local_web_ui_response_missing_content_type_rejected() -> None:
    with pytest.raises(InvalidLocalWebUiRequestError):
        LocalWebUiResponse(status_code=200, content_type="", body="ok")


def test_render_index_html_contains_expected_controls() -> None:
    ui = CraneRunwayLocalWebUi()
    html = ui.render_index_html()
    for token in ["Crane Runway", "textarea", "Validate", "Run", "/api/validate", "/api/run"]:
        assert token in html


def test_templates_and_template_case_data() -> None:
    ui = CraneRunwayLocalWebUi()
    response = ui.handle_templates_request()
    payload = json.loads(response.body)
    assert response.status_code == 200
    assert any(item["template_id"] == "ipn-with-cover" for item in payload["templates"])

    case = ui.template_case_data("ipn-with-cover")
    assert case["schema_version"] == "1.0"

    with pytest.raises(InvalidLocalWebUiRequestError):
        ui.template_case_data("unknown-template")


def test_health_validate_and_run_requests() -> None:
    ui = CraneRunwayLocalWebUi()
    health = json.loads(ui.handle_health_request().body)
    assert health["ok"] is True

    case = ui.template_case_data("ipn-with-cover")
    valid = json.loads(ui.handle_validate_request({"case_data": case}).body)
    assert valid["valid"] is True

    malformed = ui.handle_validate_request({"case_json": "{"})
    malformed_payload = json.loads(malformed.body)
    assert malformed_payload["valid"] is False

    run_ok = json.loads(ui.handle_run_request({"case_data": case, "output_formats": ["summary", "html"]}).body)
    assert run_ok["success"] is True
    assert run_ok["summary"] is not None
    assert run_ok["html_report"] is not None

    bad_case = {"schema_version": "1.0", "case_id": "bad"}
    run_bad = json.loads(ui.handle_run_request({"case_data": bad_case}).body)
    assert run_bad["success"] is False


def test_handle_request_routes() -> None:
    ui = CraneRunwayLocalWebUi()
    assert ui.handle_request("GET", "/").status_code == 200
    assert json.loads(ui.handle_request("GET", "/api/health").body)["ok"] is True
    assert ui.handle_request("GET", "/api/templates").status_code == 200
    assert ui.handle_request("GET", "/api/template/ipn-with-cover").status_code == 200

    validate_resp = ui.handle_request("POST", "/api/validate", body=json.dumps({"case_data": ui.template_case_data()}).encode())
    assert validate_resp.status_code == 200

    run_resp = ui.handle_request(
        "POST", "/api/run", body=json.dumps({"case_data": ui.template_case_data(), "output_formats": ["summary", "html"]}).encode()
    )
    assert run_resp.status_code == 200

    assert ui.handle_request("GET", "/missing").status_code == 404
