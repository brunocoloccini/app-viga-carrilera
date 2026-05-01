from __future__ import annotations

import json
import re
import shutil
import subprocess

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
        "Download HTML Report",
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
        "Case Quality Warnings",
        "Refresh Case Quality",
        "Copy Case Quality Warnings",
        "Download Case Quality Warnings JSON",
        "Refresh case quality to see warnings.",
        "Cannot check case quality: invalid JSON.",
        "No case quality warnings found.",
        "No case quality warnings available. Refresh case quality first.",
        "Suggested Action",
        "case_id is missing.",
        "description is missing.",
        "base_shape_id is missing.",
        "Sample CIRSOC profile data must be independently verified.",
        "material block is missing.",
        "material Fy is missing.",
        "material E is missing.",
        "span is missing.",
        "movement_step is missing.",
        "station_step is missing.",
        "crane block is missing.",
        "No crane wheels are defined.",
        "Only one wheel is defined.",
        "Duplicate wheel IDs found.",
        "A wheel is missing position_x.",
        "A wheel is missing vertical_force.",
        "Cover plate is enabled but width is missing.",
        "Cover plate is enabled but thickness is missing.",
        "Cover plate is enabled but weld_size is missing.",
        "No criteria presets or explicit limits are configured.",
        "No deflection criterion is configured.",
        "No stress criterion is configured.",
        "Rail eccentricity is enabled but vertical_eccentricity_y is missing.",
        "Rail eccentricity is enabled but lateral_load_height_z is missing.",
        "warnings list is missing or empty.",
        "Case quality warnings are setup checks only, not design-code checks.",
        "Use engineering review before relying on results.",
        "refreshCaseQuality",
        "buildCaseQualityWarnings",
        "renderCaseQualityWarnings",
        "copyCaseQualityWarnings",
        "downloadCaseQualityWarnings",
        "getCaseQualityRows",
        "addCaseQualityWarning",
        "hasQuantityValue",
        "getRootOrSectionBaseShapeId",

        "Field Help / Glossary",
        "Toggle Help",
        "Search glossary",
        "span",
        "base_shape_id",
        "cover_plate",
        "material Fy",
        "material Fu",
        "material E",
        "crane wheels",
        "vertical impact factor",
        "lateral force factor",
        "rail eccentricity",
        "movement_step",
        "station_step",
        "serviceability limit",
        "stress limit",
        "max vertical moment",
        "max vertical shear",
        "max vertical deflection",
        "max lateral moment",
        "max biaxial stress",
        "max torsional input",
        "serviceability passed",
        "stress criteria passed",
        "overall passed",
        "sample profile data",
        "sample material data",
        "generic criteria",
        "engineering review",
        "Presets are convenience helpers, not design recommendations.",
        "Schematic preview only; not to scale.",
        "Validation checks JSON structure and supported units before calculation.",
        "not a code-compliance verdict",
        "files are not saved to the server",
        "Help shown.",
        "Help hidden.",
        "No glossary matches.",
        "toggleFieldHelp",
        "filterGlossary",

        "Profile / Material Selector",
        "Guided Workflow",
        "Beta Readiness",
        "Troubleshooting",
        "Load Template or Import JSON",
        "Configure Inputs",
        "Refresh Preview",
        "Review Results",
        "Export / Compare",
        "Run Demo Workflow",
        "Check Backend Health",
        "Pending",
        "Done",
        "Needs attention",
        "Demo workflow complete.",
        "Demo workflow failed.",
        "Backend health: OK.",
        "Backend health: FAIL.",
        "UI JavaScript loaded",
        "Backend health",
        "JSON loaded",
        "Validation status",
        "Run status",
        "Autosave available",
        "If buttons do not respond, refresh the page.",
        "If the server is unreachable",
        "If JSON validation fails",
        "If results show FAIL",
        "requires engineering review",
        "updateWorkflowStep",
        "resetGuidedWorkflow",
        "runDemoWorkflow",
        "checkBackendHealth",
        "renderBetaReadiness",
        "updateBetaReadiness",
        "markWorkflowStepDone",
        "markWorkflowStepNeedsAttention",
        "Material Preset",
        "Load Profile/Material From JSON",
        "Apply Profile/Material To JSON",
        "Reset Profile/Material",
        "Profile / Material Errors",
        "CIRSOC_IPN_180",
        "CIRSOC_IPN_200",
        "CIRSOC_IPN_240",
        "CIRSOC_IPN_300",
        "CIRSOC_IPB_200",
        "F24",
        "F36",
        "Custom",
        "Material presets are sample helpers and must be independently verified.",
        "Profile sample data is manually curated and incomplete. Verify before design use.",
        "Cannot load profile/material: invalid JSON.",
        "Profile/material inputs contain errors.",
        "Profile/material applied to JSON.",
        "Profile/material inputs reset.",
        "No profile/material errors.",
        "Base Shape ID is required.",
        "Material ID is required.",
        "Fy must be positive.",
        "Fu must be positive.",
        "E must be positive.",
        "loadProfileMaterialFromJson",
        "applyProfileMaterialToJson",
        "resetProfileMaterial",
        "validateProfileMaterialInputs",
        "renderProfileMaterialErrors",
        "applyMaterialPreset",
        "getSelectedBaseShapeId",
        "setSelectedBaseShapeId",

        "For more than two wheels, use Wheel Table Editor.",
        "Wheel Table Editor",
        "Load Wheels From JSON",
        "Apply Wheels To JSON",
        "Add Wheel",
        "Clear Wheel Table",
        "Wheel ID",
        "Position X",
        "Position Unit",
        "Vertical Force",
        "Force Unit",
        "Remove",
        "Wheel Table Errors",
        "No wheel table errors.",
        "Cannot load wheels: invalid JSON.",
        "No wheels found in JSON.",
        "Wheel table applied to JSON.",
        "Wheel table contains errors.",
        "Wheel table cleared.",
        "Wheel ID is required.",
        "Wheel IDs must be unique.",
        "Wheel position must be numeric.",
        "Wheel vertical force must be positive.",
        "loadWheelsFromJson",
        "applyWheelsToJson",
        "addWheelRow",
        "removeWheelRow",
        "clearWheelTable",
        "validateWheelTable",
        "renderWheelTableErrors",
        "getWheelRows",
        "setWheelRows",
        "Load Form From JSON",
        "Apply Form To JSON",
        "Reset Form",
        "Validate Common Inputs",
        "Common Inputs Errors",
        "No common input errors.",
        "Common inputs are valid.",
        "Common inputs contain errors.",
        "Case ID must not contain spaces.",
        "Span must be positive.",
        "Wheel 1 Load must be positive.",
        "Cover Plate Thickness must be positive.",
        "m",
        "mm",
        "ft",
        "cm",
        "in",
        "kN",
        "N",
        "kip",
        "MPa",
        "ksi",
        "psi",
        "validateCommonInputs",
        "renderCommonInputErrors",
        "getSelectedUnit",
        "setSelectedUnit",
        "isPositiveNumber",
        "isNonNegativeNumber",
        "parseOptionalNumber",
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
        "Result Interpretation",
        "Copy Interpretation",
        "Overall status: PASS based on configured generic criteria.",
        "Overall status: FAIL based on configured generic criteria.",
        "Serviceability: FAIL. Review deflection demand and configured limits.",
        "Stress criteria: FAIL. Review stress demand and configured limits.",
        "Torsional input is present.",
        "torsional/warping stress checks are not performed.",
        "Warnings are present. Review them before using results.",
        "These are generic configured checks, not official CIRSOC/CISC/AISC compliance checks.",
        "Engineering review is required.",
        "Run a case to see result interpretation.",
        "No interpretation available. Run a case first.",
        "interpretation-pass",
        "interpretation-fail",
        "interpretation-warning",
        "interpretation-na",
        "renderResultInterpretation",
        "copyInterpretation",
        "Scenario Comparison",
        "Scenario Name",
        "Save Current Scenario",
        "Refresh Scenario List",
        "Load Scenario",
        "Delete Scenario",
        "Run All Scenarios",
        "Clear All Scenarios",
        "Download Comparison JSON",
        "Copy Comparison JSON",
        "Scenario",
        "Saved At",
        "Actions",
        "Scenario saved.",
        "Scenario loaded.",
        "Scenario deleted.",
        "All scenarios cleared.",
        "No saved scenarios available.",
        "Scenario name is required.",
        "Cannot save scenario: invalid JSON.",
        "Scenario already exists.",
        "Running saved scenarios...",
        "Scenario comparison complete.",
        "No comparison results available. Run scenarios first.",
        "saveCurrentScenario",
        "loadScenarios",
        "renderScenarioList",
        "loadScenario",
        "deleteScenario",
        "clearAllScenarios",
        "runAllScenarios",
        "renderScenarioComparison",
        "downloadScenarioComparison",
        "copyScenarioComparison",
        "getScenarioCaseSummaryFields",
        "craneRunway.scenarios",
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


def test_inline_script_defines_critical_ui_functions() -> None:
    ui = CraneRunwayLocalWebUi()
    html = ui.render_index_html()
    match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    assert match is not None
    script = match.group(1)
    assert "function importJsonFile" in script
    assert "async function validateCase" in script
    assert "async function runCase" in script
    assert "async function loadTemplate" in script


def test_inline_script_node_syntax_check() -> None:
    node_path = shutil.which("node")
    if node_path is None:
        pytest.skip("node is not available in test environment")
    ui = CraneRunwayLocalWebUi()
    html = ui.render_index_html()
    match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    assert match is not None
    script = match.group(1)
    result = subprocess.run([node_path, "--check"], input=script, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_render_index_html_contains_panel_navigation_controls() -> None:
    html = CraneRunwayLocalWebUi().render_index_html()
    for token in [
        'UI Navigation','Start','JSON Editor','Quick Selectors','Common Inputs','Wheel Table','Visual Preview','Case Quality','Validation','Run Results','Report','Scenario Comparison','Export','Help',
        'Expand All Panels','Collapse All Panels','Show Beginner View','Show Advanced View','Reset Panel Layout','Collapse','Expand',
        'All panels expanded.','All panels collapsed.','Beginner view enabled.','Advanced view enabled.','Panel layout saved locally.','Panel layout restored.','Panel layout reset.',
        'craneRunway.panelState','scrollToPanel','togglePanel','expandAllPanels','collapseAllPanels','showBeginnerView','showAdvancedView','savePanelState','restorePanelState','resetPanelLayout','applyPanelState','getDefaultPanelState'
    ]:
        assert token in html
