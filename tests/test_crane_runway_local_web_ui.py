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
    for token in [
        "Crane Runway Local UI",
        "Local beta tool",
        "Load Template",
        "Validate",
        "Run",
        "Clear Output",
        "Format JSON",
        "Clear JSON",
        "Import JSON File",
        "Validate after import",
        "Download JSON Case",
        "Copy JSON Case",
        "Download Summary JSON",
        "Copy Summary JSON",
        "Download HTML Report",
        "Copy Validation Response",
        "Copy Raw Response",
        "Package Export",
        "Download Package Metadata",
        "Download Case JSON",
        "Download Validation Response",
        "Download Run Response",
        "Download Report HTML",
        "Download All Package Files",
        "Validation",
        "Summary",
        "HTML Report",
        "Raw Response",
        "Case Outline",
        "Refresh Case Outline",
        "Copy Error List",
        "Find Path",
        "Result Cards",
        "Help / Workflow",
        "Severity",
        "Path",
        "Message",
        "Hint",
        "No validation messages available.",
        "Path not found in editor.",
        "Cannot build outline: invalid JSON.",
        "Max Moment",
        "Max Shear",
        "Max Deflection",
        "Max Biaxial Stress",
        "Serviceability",
        "Stress",
        "Overall",
        "engineering review",
        "no official CIRSOC/CISC/AISC checks",
        "no fatigue",
        "no torsional/warping stress",
        "no LTB",
        "Cannot download case: invalid JSON.",
        "No summary available. Run a case first.",
        "No HTML report available. Run a case first.",
        "No validation response available. Validate a case first.",
        "No run response available. Run a case first.",
        "Package metadata downloaded.",
        "Downloaded package files:",
        "Unavailable package files:",
        "Cannot export case.json: invalid JSON.",
        "No raw response available.",
        "No JSON file selected.",
        "Imported JSON file:",
        "Could not import JSON file.",
        "/api/validate",
        "/api/run",
        "renderValidation",
        "renderSummary",
        "formatJson",
        "clearOutput",
        "downloadText",
        "copyText",
        "downloadCaseJson",
        "copyCaseJson",
        "downloadSummaryJson",
        "copySummaryJson",
        "downloadHtmlReport",
        "copyValidationResponse",
        "copyRawResponse",
        "buildPackageArtifacts",
        "buildPackageMetadata",
        "downloadPackageMetadata",
        "downloadValidationResponse",
        "downloadRunResponse",
        "downloadAllPackageFiles",
        "type=\"file\"",
        "accept=\".json,application/json\"",
        "FileReader",
        "importJsonFile",
        "validateAfterImport",
        "validate_after_import",
        "renderValidationTable",
        "copyErrorList",
        "findJsonPath",
        "refreshCaseOutline",
        "renderResultCards",
        "renderHelpPanel",
        "Autosave",
        "Autosaved locally.",
        "Restored autosaved JSON.",
        "Saved session cleared.",
        "No saved session",
        "Autosave unavailable.",
        "Autosave is stored only in this browser using localStorage.",
        "Clear Saved Session",
        "localStorage",
        "craneRunway.caseJson",
        "craneRunway.selectedTemplate",
        "craneRunway.lastSavedAt",
        "saveSession",
        "restoreSession",
        "clearSavedSession",
        "updateAutosaveStatus",
        "Common Inputs",
        "Load Form From JSON",
        "Apply Form To JSON",
        "Reset Form",
        "Case ID",
        "Description",
        "Base Shape ID",
        "Cover Plate Enabled",
        "Cover Plate Width",
        "Cover Plate Thickness",
        "Cover Plate Weld Size",
        "Material ID",
        "Fy",
        "Fu",
        "E",
        "Span",
        "Movement Step",
        "Station Step",
        "Crane ID",
        "Vertical Impact Factor",
        "Lateral Force Factor",
        "Wheel 1 Load",
        "Wheel 2 Load",
        "Wheel Spacing",
        "Rail Eccentricity Enabled",
        "Vertical Eccentricity Y",
        "Lateral Load Height Z",
        "Deflection Preset",
        "Stress Preset",
        "Cannot load form: invalid JSON.",
        "Cannot apply form: invalid JSON.",
        "Common inputs applied to JSON.",
        "Common inputs reset.",
        "Common Inputs edits the JSON below.",
        "Advanced fields remain editable directly in JSON.",
        "loadCommonInputsFromJson",
        "applyCommonInputsToJson",
        "Visual Preview",
        "Refresh Visual Preview",
        "Beam Preview",
        "Section Preview",
        "Preview Summary",
        "Preview is schematic only and not to scale.",
        "Cannot refresh visual preview: invalid JSON.",
        "Visual preview refreshed.",
        "case_id",
        "base_shape_id",
        "span",
        "number of wheels",
        "cover plate enabled",
        "material_id",
        "rail eccentricity enabled",
        "criteria presets",
        "refreshVisualPreview",
        "renderBeamPreview",
        "renderSectionPreview",
        "renderPreviewSummary",
        "extractQuantityLabel",
        "getWheelList",
        "getCaseSpan",
        "getBaseShapeId",
        "getCoverPlateInfo",
        "getMaterialInfo",
        "getRailEccentricityInfo",
        "resetCommonInputs",
        "setQuantity",
        "getQuantityValue",
        "setNestedValue",
        "getNestedValue",
        "ensureObjectPath",
    ]:
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
