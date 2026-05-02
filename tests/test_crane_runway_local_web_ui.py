from __future__ import annotations

import json
from io import BytesIO
import re
import shutil
import subprocess
import zipfile

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
        "Local UI RC Status",
        "Health check",
        "UI diagnostics",
        "RC acceptance check",
        "Manual QA checklist",
        "Support bundle",
        "Project archive export",
        "Known limitations",
        "Engineering review",
        "Release-candidate status means the local UI workflow is ready for beta testing",
        "Copy RC Checklist Summary",
        "Mark Manual QA Completed",
        "Reset RC Checklist Status",
        "RC checklist summary copied.",
        "Manual QA marked complete.",
        "RC checklist status reset.",
        "craneRunway.rcChecklistStatus",
        "Keyboard Shortcuts",
        "Ctrl+Enter",
        "Ctrl+Shift+Enter",
        "Ctrl+S",
        "Ctrl+Shift+F",
        "Ctrl+Shift+H",
        "Keyboard shortcuts enabled.",
        "JSON saved to browser autosave.",
        "Accessibility support is basic",
        "aria-live",
        "Unexpected UI error",
        "safeUiAction",
        "LOCAL_UI_BETA_VERSION",
        "LOCAL_UI_SCHEMA_VERSION",
        "Local UI beta version",
        "V1-086",
        "copyRcChecklistSummary",
        "markManualQaCompleted",
        "resetRcChecklistStatus",
        "renderRcStatus",
        "setupKeyboardShortcuts",

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
        "Project Workspace",
        "Project Name",
        "Create Project",
        "Refresh Project List",
        "Open Project",
        "Save JSON To Project",
        "Run Project To Outputs",
        "Open Project Outputs Info",
        "Projects are stored locally under the repository projects/ directory.",
        "This is a local-only beta feature. Do not expose the server publicly.",
        "Project created.",
        "Project opened.",
        "Project input_case.json saved.",
        "Cannot save project: invalid JSON.",
        "Project run complete.",
        "Project run failed.",
        "Invalid project name. Use only letters, numbers, dash, and underscore.",
        "refreshProjectList",
        "renderProjectList",
        "createProject",
        "openProject",
        "saveProjectCase",
        "runProject",
        "showProjectOutputsInfo",
        "Project Run History",
        "Project Run Comparison",
        "Refresh Runs For Comparison",
        "Baseline Run",
        "Comparison Runs",
        "Form-First Workflow",
        "Beam & Section",
        "Material",
        "Crane Wheels",
        "Criteria",
        "Rail / Eccentricity",
        "Preview",
        "Not started",
        "In progress",
        "Complete",
        "Needs attention",
        "Home",
        "Setup",
        "Loads",
        "Review",
        "Calculate",
        "Support",
        "Advanced",
        "Beam/section applied to JSON.",
        "Beam/section contains errors.",
        "Material applied to JSON.",
        "Material form contains errors.",
        "Criteria applied to JSON.",
        "Crane factors applied to JSON.",
        "Rail eccentricity applied to JSON.",
        "Apply All Forms To JSON",
        "All forms applied to JSON.",
        "Cannot apply all forms: fix highlighted errors first.",
        "Validate and run complete.",
        "Validate and run stopped: validation failed.",
        "Unsaved changes",
        "Saved",
        "Unsaved changes detected.",
        "Changes marked saved.",
        "renderFormWorkflowStepper",
        "goToWorkflowStep",
        "markWorkflowStepComplete",
        "markWorkflowStepNeedsAttention",
        "updateFormWorkflowState",
        "resetFormWorkflowState",
        "getWorkflowStepStatus",
        "loadBeamSectionFromJson",
        "applyBeamSectionToJson",
        "resetBeamSectionForm",
        "validateBeamSectionForm",
        "loadMaterialFromJson",
        "applyMaterialToJson",
        "resetMaterialForm",
        "validateMaterialForm",
        "loadCriteriaFromJson",
        "applyCriteriaToJson",
        "resetCriteriaForm",
        "loadCraneFactorsFromJson",
        "applyCraneFactorsToJson",
        "resetCraneFactorsForm",
        "loadRailEccentricityFromJson",
        "applyRailEccentricityToJson",
        "resetRailEccentricityForm",
        "applyAllFormsToJson",
        "validateAndRunCase",
        "markUnsavedChanges",
        "markSavedChanges",
        "updateUnsavedChangesIndicator",
        "showNextStepRecommendation",
        "Compare Selected Runs",
        "Clear Run Comparison",
        "Copy Run Comparison JSON",
        "Download Run Comparison JSON",
        "Refresh Run History",
        "Run Project As History Snapshot",
        "Load Run Summary",
        "Load Run HTML Report",
        "Copy Run Summary JSON",
        "Download Run Summary JSON",
        "Download Run HTML Report",
        "Run ID",
        "Created At",
        "Actions",
        "Select a project first.",
        "No project runs available.",
        "Project run comparison complete.",
        "Select a baseline run.",
        "Select at least one comparison run.",
        "Project run comparison cleared.",
        "No project run comparison available. Compare runs first.",
        "Run comparison uses existing summary.json values only.",
        "Project history run complete.",
        "Run summary loaded.",
        "Run HTML report loaded.",
        "No run artifact selected.",
        "refreshRunHistory",
        "renderRunHistory",
        "runProjectHistorySnapshot",
        "loadRunSummary",
        "loadRunHtmlReport",
        "copyRunSummaryJson",
        "downloadRunSummaryJson",
        "downloadRunHtmlReport",
        "refreshRunsForComparison",
        "renderRunComparisonSelectors",
        "compareSelectedRuns",
        "renderProjectRunComparison",
        "clearRunComparison",
        "copyRunComparisonJson",
        "downloadRunComparisonJson",
        "Project Archive Export",
        "Refresh Archive Manifest",
        "Download Project Archive",
        "Copy Archive Manifest JSON",
        "Download Archive Manifest JSON",
        "Project archives are generated locally from the repository projects/ directory.",
        "Archive export is for backup/sharing only and does not prove engineering correctness.",
        "Archive manifest refreshed.",
        "Project archive download started.",
        "No archive manifest available. Refresh archive manifest first.",
        "project_name",
        "generated_at",
        "included_files",
        "archive_format_version",
        "refreshArchiveManifest",
        "renderArchiveManifest",
        "downloadProjectArchive",
        "copyArchiveManifestJson",
        "downloadArchiveManifestJson",

        "About / Beta Status",
        "Refresh About Info",
        "Copy About Info",
        "App Viga Carrilera",
        "Internal beta",
        "Schema version: 1.0",
        "not official CIRSOC/CISC/AISC compliance checks",
        "sample data requires independent verification",
        "engineering review required",
        "Support Bundle",
        "Refresh Support Bundle Preview",
        "Download Support Bundle JSON",
        "Copy Support Bundle JSON",
        "Clear Support Bundle Preview",
        "Support bundles may include the current JSON case",
        "Review before sharing.",
        "bundle_version",
        "current_case_parse_ok",
        "wheel_count",
        "has_validation_response",
        "has_run_response",
        "Support bundle preview refreshed.",
        "Support bundle JSON downloaded.",
        "Support bundle JSON copied.",
        "Support bundle preview cleared.",
        "No support bundle available. Refresh support bundle preview first.",
        "Issue Report Helper",
        "Generate Issue Report Text",
        "Copy Issue Report Text",
        "Local UI Issue Report",
        "Expected behavior",
        "Actual behavior",
        "Attached support bundle",
        "Issue report text generated.",
        "Issue report text copied.",
        "buildAboutInfo",
        "renderAboutInfo",
        "refreshAboutInfo",
        "copyAboutInfo",
        "buildSupportBundle",
        "renderSupportBundlePreview",
        "refreshSupportBundlePreview",
        "downloadSupportBundleJson",
        "copySupportBundleJson",
        "clearSupportBundlePreview",
        "generateIssueReportText",
        "copyIssueReportText",
        "renderIssueReportText",
        "getArchiveProjectName",
        "setArchiveStatus",
        "getSelectedBaselineRunId",
        "getSelectedComparisonRunIds",
        "buildProjectRunComparison",
        "computeSummaryDelta",
        "formatComparisonDelta",
        "setProjectRunComparisonStatus",
        "getSelectedRunId",
        "setRunHistoryStatus",
        "getSelectedProjectName",
        "validateProjectNameClient",
        "setProjectWorkspaceStatus",
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
        "updateDiagnosticsTimestamp",
        "checkDiagnosticsEndpoint",
        "getDiagnosticTemplateCase",
        "setDiagnosticStatus",
        "renderUiDiagnostics",
        "runUiDiagnostics",
        "Use beta health check and manual QA checklist before relying on beta UI output.",
        "Diagnostics check UI/server connectivity only. They do not prove engineering correctness.",
        "UI diagnostics found issues.",
        "UI diagnostics complete.",
        "Last diagnostic run",
        "Autosave status",
        "JavaScript status",
        "Run endpoint",
        "Validate endpoint",
        "Templates endpoint",
        "UI loaded",
        "Run UI Diagnostics",
        "Local UI Diagnostics",
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
        "delta_max_vertical_moment_Nmm",
        "delta_max_vertical_shear_abs_N",
        "delta_max_vertical_deflection_mm",
        "delta_max_biaxial_stress_MPa",
        "serviceability_passed",
        "stress_criteria_passed",
        "overall_passed",
        "Baseline",
        "Compared runs",
        "Overall PASS count",
        "Overall FAIL count",
        "Largest deflection",
        "Largest biaxial stress",
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


def test_project_workspace_routes(tmp_path) -> None:
    ui = CraneRunwayLocalWebUi(projects_root=tmp_path / "projects")
    list_resp = ui.handle_request("GET", "/api/projects")
    assert list_resp.status_code == 200
    assert json.loads(list_resp.body)["projects"] == []

    create_payload = {"project_name": "qa_project", "template_id": "ipn-with-cover", "overwrite": False}
    create_resp = ui.handle_request("POST", "/api/projects/create", body=json.dumps(create_payload).encode())
    assert create_resp.status_code == 200

    projects = json.loads(ui.handle_request("GET", "/api/projects").body)["projects"]
    assert any(item["name"] == "qa_project" for item in projects)

    case_resp = ui.handle_request("GET", "/api/projects/qa_project/case")
    assert case_resp.status_code == 200
    case_payload = json.loads(case_resp.body)
    assert "case_data" in case_payload and "case_json" in case_payload

    save_resp = ui.handle_request(
        "POST", "/api/projects/qa_project/save", body=json.dumps({"case_data": case_payload["case_data"]}).encode()
    )
    assert save_resp.status_code == 200

    run_resp = ui.handle_request("POST", "/api/projects/qa_project/run")
    run_payload = json.loads(run_resp.body)
    assert run_resp.status_code == 200
    assert "summary" in run_payload

    bad_resp = ui.handle_request("POST", "/api/projects/create", body=json.dumps({"project_name": "../bad"}).encode())
    assert bad_resp.status_code == 400

    runs_empty = ui.handle_request("GET", "/api/projects/qa_project/runs")
    assert runs_empty.status_code == 200

    history_resp = ui.handle_request("POST", "/api/projects/qa_project/run-history")
    assert history_resp.status_code == 200
    history_payload = json.loads(history_resp.body)
    run_id = history_payload["run_id"]

    runs_resp = ui.handle_request("GET", "/api/projects/qa_project/runs")
    runs_payload = json.loads(runs_resp.body)
    assert any(item["run_id"] == run_id for item in runs_payload["runs"])

    summary_resp = ui.handle_request("GET", f"/api/projects/qa_project/runs/{run_id}/summary")
    assert summary_resp.status_code == 200
    history_resp_2 = ui.handle_request("POST", "/api/projects/qa_project/run-history")
    assert history_resp_2.status_code == 200
    run_id_2 = json.loads(history_resp_2.body)["run_id"]
    summary_resp_2 = ui.handle_request("GET", f"/api/projects/qa_project/runs/{run_id_2}/summary")
    assert summary_resp_2.status_code == 200

    html_resp = ui.handle_request("GET", f"/api/projects/qa_project/runs/{run_id}/report-html")
    assert html_resp.status_code == 200

    assert ui.handle_request("GET", "/api/projects/../bad/runs").status_code == 400
    assert ui.handle_request("GET", "/api/projects/qa_project/runs/../bad/summary").status_code == 400


def test_project_archive_manifest_and_zip_routes(tmp_path) -> None:
    ui = CraneRunwayLocalWebUi(projects_root=tmp_path / "projects")
    ui.handle_request("POST", "/api/projects/create", body=json.dumps({"project_name": "qa_project", "template_id": "ipn-with-cover"}).encode())
    ui.handle_request("POST", "/api/projects/qa_project/run-history")
    manifest_resp = ui.handle_request("GET", "/api/projects/qa_project/archive-manifest")
    assert manifest_resp.status_code == 200
    manifest = json.loads(manifest_resp.body)
    assert manifest["project_name"] == "qa_project"
    assert "archive_manifest.json" in manifest["included_files"]
    assert "input_case.json" in manifest["included_files"]

    archive_resp = ui.handle_request("GET", "/api/projects/qa_project/archive")
    assert archive_resp.status_code == 200
    assert archive_resp.content_type == "application/zip"
    assert "qa_project_archive.zip" in archive_resp.headers.get("Content-Disposition", "")
    with zipfile.ZipFile(BytesIO(archive_resp.body_bytes()), "r") as archive_zip:
        names = archive_zip.namelist()
        assert "input_case.json" in names
        assert "archive_manifest.json" in names
        assert all(not name.startswith("/") for name in names)
        archive_manifest = json.loads(archive_zip.read("archive_manifest.json").decode("utf-8"))
        assert archive_manifest["archive_format_version"] == "1.0"

    assert ui.handle_request("GET", "/api/projects/qa project/archive").status_code == 400
    assert ui.handle_request("GET", "/api/projects/../bad/archive").status_code == 400
    missing_resp = ui.handle_request("GET", "/api/projects/missing_project/archive")
    assert missing_resp.status_code == 404


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

def test_render_index_html_tabbed_app_shell_v1_089() -> None:
    html = CraneRunwayLocalWebUi().render_index_html()
    required = [
        'App Viga Carrilera','Crane Runway Local UI','Internal Beta',
        'Results require engineering review','No official CIRSOC/CISC/AISC compliance checks are performed',
        'Home','Project','Inputs','Wheels','Preview','Validate & Run','Results','Compare','Export','Support','Advanced JSON',
        'switchMainTab','setActiveTabButton','getActiveTab','restoreActiveTab','saveActiveTab','updateCompactCaseSummary','refreshAppShellStatus','craneRunway.activeTab',
        'Switched to Home.','Switched to Project.','Switched to Inputs.','Switched to Wheels.','Switched to Preview.','Switched to Validate & Run.','Switched to Results.','Switched to Compare.','Switched to Export.','Switched to Support.','Switched to Advanced JSON.',
        'Load Demo','Go to Results',
        'Current case','Current project','Validation status','Run status','Overall status','Autosave status',
        'Project Workspace','Common Inputs','Wheel Table Editor','Visual Preview','Case Quality Warnings','Validation','Result Cards','Result Interpretation','HTML Report','Scenario Comparison','Package Export','Support Bundle','Issue Report Helper','Local UI Diagnostics','JSON Editor','Raw Response',
    ]
    for token in required:
        assert token in html


def test_local_ui_asset_css_endpoint() -> None:
    ui = CraneRunwayLocalWebUi()
    response = ui.handle_request("GET", "/assets/local_ui.css")
    assert response.status_code == 200
    assert "text/css" in response.content_type
    body = response.body if isinstance(response.body, str) else response.body.decode("utf-8")
    for token in ["--color-bg", ".app-shell", ".app-card", ".tab-button", ".primary-action"]:
        assert token in body


def test_local_ui_asset_js_endpoint() -> None:
    ui = CraneRunwayLocalWebUi()
    response = ui.handle_request("GET", "/assets/local_ui.js")
    assert response.status_code == 200
    assert "application/javascript" in response.content_type
    body = response.body if isinstance(response.body, str) else response.body.decode("utf-8")
    for token in ["LOCAL_UI_BETA_VERSION", "initializeLocalUi", "setupActionHandlers", "handleUiAction", "validateCase", "runCase"]:
        assert token in body


def test_render_index_html_references_asset_endpoints() -> None:
    html = CraneRunwayLocalWebUi().render_index_html()
    for token in ["/assets/local_ui.css", "/assets/local_ui.js", "App Viga Carrilera", "Crane Runway Local UI"]:
        assert token in html


def test_frontend_contract_endpoint_and_self_test_markers() -> None:
    ui=CraneRunwayLocalWebUi(); r=ui.handle_request("GET","/assets/frontend_contract.json"); assert r.status_code==200; c=json.loads(r.body); assert "Home" in c["required_tabs"]; assert "initializeLocalUi" in c["required_functions"]; h=ui.render_index_html();
    for t in ["Frontend Self-Test","Run Frontend Self-Test","Copy Frontend Self-Test JSON","Download Frontend Self-Test JSON","Frontend self-test checks UI wiring only. It does not prove engineering correctness.","Frontend self-test complete.","Frontend self-test found issues.","No frontend self-test result available. Run self-test first.","Frontend self-test JSON copied.","Frontend self-test JSON downloaded."]:
        assert t in h
    j=ui.handle_request("GET","/assets/local_ui.js").body
    for n in ["runFrontendSelfTest","buildFrontendSelfTestResult","renderFrontendSelfTest","copyFrontendSelfTestJson","downloadFrontendSelfTestJson","checkRequiredFunctions","checkRequiredTabs","checkRequiredPanels","checkRequiredActions","checkLocalStorageAvailability","Unknown UI action.","setupActionHandlers","handleUiAction"]: assert n in j


def test_v1093_beginner_dashboard_and_wizard_tokens() -> None:
    html=CraneRunwayLocalWebUi().render_index_html()
    for t in ["Beginner Dashboard","Start New Case","Open Project","Continue Autosaved Case","Run Demo","Validate Current Case","Run Current Case","Review Results","Export / Share","Ready","Needs input","Complete","Not available","Case Wizard","Start Case Wizard","Previous Wizard Step","Next Wizard Step","Save Wizard Step","Reset Case Wizard","Finish Wizard","Case wizard started.","Wizard step saved.","Wizard advanced.","Wizard moved back.","Case wizard reset.","Case wizard complete.","Wizard step needs attention.","craneRunway.caseWizardState","Wizard Beam Step","Wizard Material Step","Wizard Wheels Step","Wizard Criteria Step","Wizard Rail Step","Wizard Review Step","Wizard Calculate Step","Wizard Results Step","Wizard Export Step","Material sample values require independent verification.","These are generic configured checks, not official CIRSOC/CISC/AISC compliance checks.","Current workflow reports torsional input but does not perform torsional/warping stress checks.","Case Readiness","Not ready","Needs review","Ready to validate","Ready to run","Results available","Wizard Change Summary","Updated base profile.","Updated span.","Updated material.","Updated wheel table.","Updated criteria.","Updated rail eccentricity.","Open Advanced JSON","openAdvancedJson"]: assert t in html
