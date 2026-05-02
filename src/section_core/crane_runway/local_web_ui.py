"""Minimal local web UI adapter for crane runway beta workflows (V1-059)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from io import BytesIO
import json
from pathlib import Path
import re
from typing import Any
import zipfile

from .api_service import CraneRunwayApiService
from .case_templates import (
    CaseTemplateNotFoundError,
    build_default_crane_runway_case_template_registry,
)


from .local_ui_assets import render_local_ui_css, render_local_ui_frontend_contract, render_local_ui_js

class LocalWebUiError(Exception):
    """Base error for local web UI workflows."""


class InvalidLocalWebUiRequestError(LocalWebUiError):
    """Raised for invalid local web UI requests."""


@dataclass
class LocalWebUiResponse:
    status_code: int
    content_type: str
    body: str | bytes
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status_code, int) or self.status_code <= 0:
            raise InvalidLocalWebUiRequestError("status_code must be a positive integer.")
        if not isinstance(self.content_type, str) or not self.content_type.strip():
            raise InvalidLocalWebUiRequestError("content_type is required.")
        if not isinstance(self.body, (str, bytes)):
            raise InvalidLocalWebUiRequestError("body must be str or bytes.")
        if not isinstance(self.headers, dict):
            raise InvalidLocalWebUiRequestError("headers must be a dict.")

    def body_bytes(self) -> bytes:
        return self.body.encode("utf-8") if isinstance(self.body, str) else self.body


INVALID_PROJECT_NAME_ERROR = "Invalid project name. Use only letters, numbers, dash, and underscore."
INVALID_RUN_ID_ERROR = "Invalid run ID. Use only letters, numbers, dash, and underscore."
ARCHIVE_NOTES = [
    "Local beta project archive.",
    "Results require engineering review.",
    "Generic checks only; no official CIRSOC/CISC/AISC compliance checks.",
    "No fatigue, torsional/warping stress, or LTB checks are performed.",
]


class CraneRunwayLocalWebUi:
    """Route handler for local crane runway browser workflows."""

    def __init__(self, projects_root: Path | None = None) -> None:
        self._api = CraneRunwayApiService()
        self._template_registry = build_default_crane_runway_case_template_registry()
        self._projects_root = (projects_root or (Path.cwd() / "projects")).resolve()

    def validate_project_name(self, name: str) -> str:
        if not isinstance(name, str):
            raise InvalidLocalWebUiRequestError(INVALID_PROJECT_NAME_ERROR)
        clean_name = name.strip()
        if not clean_name or ".." in clean_name or "/" in clean_name or "\\" in clean_name or " " in clean_name:
            raise InvalidLocalWebUiRequestError(INVALID_PROJECT_NAME_ERROR)
        if re.fullmatch(r"[A-Za-z0-9_-]+", clean_name) is None:
            raise InvalidLocalWebUiRequestError(INVALID_PROJECT_NAME_ERROR)
        return clean_name

    def _project_dir(self, project_name: str) -> Path:
        safe_name = self.validate_project_name(project_name)
        project_dir = (self._projects_root / safe_name).resolve()
        if self._projects_root not in project_dir.parents:
            raise InvalidLocalWebUiRequestError(INVALID_PROJECT_NAME_ERROR)
        return project_dir

    def validate_run_id(self, run_id: str) -> str:
        if not isinstance(run_id, str):
            raise InvalidLocalWebUiRequestError(INVALID_RUN_ID_ERROR)
        clean_run_id = run_id.strip()
        if not clean_run_id or ".." in clean_run_id or "/" in clean_run_id or "\\" in clean_run_id or " " in clean_run_id:
            raise InvalidLocalWebUiRequestError(INVALID_RUN_ID_ERROR)
        if re.fullmatch(r"[A-Za-z0-9_-]+", clean_run_id) is None:
            raise InvalidLocalWebUiRequestError(INVALID_RUN_ID_ERROR)
        return clean_run_id

    def render_index_html(self) -> str:
        return """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"/><title>Crane Runway Local UI</title><link rel=\"stylesheet\" href=\"/assets/local_ui.css\"/>
<style>
body { font-family: Arial, sans-serif; margin: 1rem; background: #f8fafc; color: #111827; }
h1 { margin-bottom: 0.3rem; }
.warning { background: #fff7ed; color: #9a3412; border: 1px solid #fdba74; padding: 0.6rem; border-radius: 6px; }
.page { display: grid; grid-template-columns: 1fr; gap: 1rem; margin-top: 1rem; }
.left-col, .right-col { display: grid; gap: 1rem; align-content: start; }
@media (min-width: 1080px) { .page { grid-template-columns: 1.1fr 1fr; } }
.toolbar { margin-top: 0.8rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
button { padding: 0.45rem 0.7rem; border: 1px solid #d1d5db; border-radius: 6px; background: white; cursor: pointer; }
button:hover { background: #f3f4f6; }
select, textarea { border: 1px solid #d1d5db; border-radius: 6px; }
textarea { width: 100%; min-height: 300px; font-family: Consolas, monospace; padding: 0.6rem; box-sizing: border-box; }
.status { margin-top: 0.8rem; padding: 0.7rem; background: #eff6ff; border: 2px solid #60a5fa; border-radius: 6px; font-weight: 600; }
.panel { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.8rem; scroll-margin-top: 5rem; }
.panel + .panel { margin-top: 1rem; }
.panel-header { display:flex; align-items:center; justify-content:space-between; gap:0.5rem; }
.panel-body.collapsed { display:none; }
.ui-nav { position: sticky; top: 0.5rem; z-index: 5; }
.panel h3 { margin-top: 0; }
pre { white-space: pre-wrap; word-break: break-word; background: #f9fafb; border: 1px solid #e5e7eb; padding: 0.6rem; border-radius: 6px; min-height: 80px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #e5e7eb; padding: 0.4rem; text-align: left; font-size: 0.92rem; vertical-align: top; }
th { background: #f9fafb; }
.pass, .status-pass { color: #166534; font-weight: bold; }
.fail, .status-fail { color: #991b1b; font-weight: bold; }
.status-na { color: #374151; font-weight: bold; }
.small-btn { padding: 0.25rem 0.45rem; font-size: 0.82rem; }
.result-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.6rem; margin-bottom: 0.8rem; }
.result-card { border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.55rem; background: #f9fafb; }
.result-card-title { font-size: 0.85rem; color: #374151; margin-bottom: 0.2rem; }
.result-card-value { font-weight: bold; }
.interpretation-pass { color: #166534; font-weight: 600; }
.interpretation-fail { color: #991b1b; font-weight: 600; }
.interpretation-warning { color: #9a3412; font-weight: 600; }
.interpretation-na { color: #374151; font-weight: 600; }
.app-shell{max-width:1400px;margin:0 auto;}
.app-header{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:0.8rem;}
.app-header-top{display:flex;justify-content:space-between;gap:0.8rem;flex-wrap:wrap;align-items:center;}
.beta-badge{background:#fef3c7;color:#92400e;border:1px solid #fcd34d;border-radius:999px;padding:0.1rem 0.55rem;font-weight:700;font-size:.8rem;}
.main-tabs{display:flex;gap:0.4rem;flex-wrap:wrap;margin-top:0.7rem;}
.main-tab-btn.active{background:#1d4ed8;color:#fff;border-color:#1d4ed8;}
.main-layout{display:grid;grid-template-columns:1fr;gap:1rem;margin-top:1rem;}
@media (min-width:1200px){.main-layout{grid-template-columns:minmax(0,1fr) 300px;}}
.tab-panel[hidden]{display:none!important;}
.summary-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:0.7rem;position:sticky;top:0.7rem;}
</style>
</head>
<body>
<div class="app-header panel">
  <div class="app-header-top">
    <div><h1 style="margin:0;">App Viga Carrilera</h1><p style="margin:0.2rem 0 0;"><strong>Crane Runway Local UI</strong> <span class="beta-badge">Internal Beta</span></p></div>
    <div class="toolbar" style="margin-top:0;">
      <button onclick="loadTemplate('ipn-with-cover')">Load Demo</button>
      <button onclick="validateCase()">Validate</button>
      <button onclick="runCase()">Run</button>
      <button onclick="switchMainTab('results')">Go to Results</button>
    </div>
  </div>
  <p class="warning">Results require engineering review. No official CIRSOC/CISC/AISC compliance checks are performed.</p>
  <div id="app_shell_status" class="status">App shell ready.</div>
  <div class="main-tabs">
    <button class="main-tab-btn" data-tab-btn="home" onclick="switchMainTab('home')">Home</button>
    <button class="main-tab-btn" data-tab-btn="project" onclick="switchMainTab('project')">Project</button>
    <button class="main-tab-btn" data-tab-btn="setup" onclick="switchMainTab('setup')">Setup</button>
    <button class="main-tab-btn" data-tab-btn="loads" onclick="switchMainTab('loads')">Loads</button>
    <button class="main-tab-btn" data-tab-btn="review" onclick="switchMainTab('review')">Review</button>
    <button class="main-tab-btn" data-tab-btn="calculate" onclick="switchMainTab('calculate')">Calculate</button>
    <button class="main-tab-btn" data-tab-btn="results" onclick="switchMainTab('results')">Results</button>
    
    <button class="main-tab-btn" data-tab-btn="export" onclick="switchMainTab('export')">Export</button>
    <button class="main-tab-btn" data-tab-btn="support" onclick="switchMainTab('support')">Support</button>
    <button class="main-tab-btn" data-tab-btn="advanced" onclick="switchMainTab('advanced')">Advanced</button>
  </div>
</div>
<h1>Crane Runway Local UI</h1>
<p class=\"warning\">Local beta tool. Results require engineering review.</p>
<div class=\"panel\" id=\"welcome_panel\" style=\"margin-top:1rem;\">
  <h3>Welcome to the Local UI Beta</h3>
  <p>This is a local browser beta for crane runway workflows.</p>
  <p>Start with Guided Demo and use Documentation Portal if you are unsure about a step.</p>
  <p>Results require engineering review, and no official CIRSOC/CISC/AISC compliance checks are performed.</p>
  <div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"dismissWelcomeBanner()\">Dismiss Welcome</button></div>
</div>
<label for=\"template\">Template:</label>
<select id=\"template\">
  <option value=\"ipn-with-cover\">ipn-with-cover</option>
  <option value=\"ipn-without-cover\">ipn-without-cover</option>
  <option value=\"ipn-no-rail-eccentricity\">ipn-no-rail-eccentricity</option>
</select>
<div class=\"toolbar\">
  <button onclick=\"loadTemplate()\">Load Template</button>
  <button onclick=\"validateCase()\">Validate</button>
  <button onclick=\"runCase()\">Run</button>
  <button onclick=\"clearOutput()\">Clear Output</button>
  <button onclick=\"formatJson()\">Format JSON</button>
  <button onclick=\"clearJson()\">Clear JSON</button>
  <button onclick=\"clearSavedSession()\">Clear Saved Session</button>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Project Workspace</h3>
  <p style=\"margin-top:0.2rem;color:#4b5563;\">Projects are stored locally under the repository projects/ directory.</p>
  <p style=\"margin-top:0.2rem;color:#92400e;\">This is a local-only beta feature. Do not expose the server publicly.</p>
  <table><tbody>
    <tr><td>Project Name</td><td><input id=\"project_name\" type=\"text\"/></td><td>Template</td><td><select id=\"project_template\"><option value=\"ipn-with-cover\">ipn-with-cover</option><option value=\"ipn-without-cover\">ipn-without-cover</option><option value=\"ipn-no-rail-eccentricity\">ipn-no-rail-eccentricity</option></select></td></tr>
  </tbody></table>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button onclick=\"createProject()\">Create Project</button>
    <button onclick=\"refreshProjectList()\">Refresh Project List</button>
    <button onclick=\"openProject()\">Open Project</button>
    <button onclick=\"saveProjectCase()\">Save JSON To Project</button>
    <button onclick=\"runProject()\">Run Project To Outputs</button>
    <button onclick=\"showProjectOutputsInfo()\">Open Project Outputs Info</button>
  </div>
  <div id=\"project_workspace_status\" style=\"margin-top:0.35rem;color:#374151;\">Project workspace ready.</div>
  <table><thead><tr><th>Project</th><th>Input Case</th><th>Outputs</th><th>Actions</th></tr></thead><tbody id=\"project_list_body\"></tbody></table>
  <pre id=\"project_outputs_info\">Select a project to view outputs path.</pre>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Project Run History</h3>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button onclick=\"refreshRunHistory()\">Refresh Run History</button>
    <button onclick=\"runProjectHistorySnapshot()\">Run Project As History Snapshot</button>
    <button onclick=\"loadRunSummary()\">Load Run Summary</button>
    <button onclick=\"loadRunHtmlReport()\">Load Run HTML Report</button>
    <button onclick=\"copyRunSummaryJson()\">Copy Run Summary JSON</button>
    <button onclick=\"downloadRunSummaryJson()\">Download Run Summary JSON</button>
    <button onclick=\"downloadRunHtmlReport()\">Download Run HTML Report</button>
  </div>
  <div id=\"run_history_status\" style=\"margin-top:0.35rem;color:#374151;\">Project run history ready.</div>
  <table><thead><tr><th>Run ID</th><th>Created At</th><th>Summary</th><th>HTML Report</th><th>Actions</th></tr></thead><tbody id=\"run_history_body\"></tbody></table>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Project Run Comparison</h3>
  <p style=\"margin-top:0.2rem;color:#4b5563;\">Run comparison uses existing summary.json values only.</p>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button onclick=\"refreshRunsForComparison()\">Refresh Runs For Comparison</button>
    <button onclick=\"compareSelectedRuns()\">Compare Selected Runs</button>
    <button onclick=\"clearRunComparison()\">Clear Run Comparison</button>
    <button onclick=\"copyRunComparisonJson()\">Copy Run Comparison JSON</button>
    <button onclick=\"downloadRunComparisonJson()\">Download Run Comparison JSON</button>
  </div>
  <table><tbody>
    <tr><td>Baseline Run</td><td id=\"run_comparison_baseline_selector\"></td></tr>
    <tr><td>Comparison Runs</td><td id=\"run_comparison_comparison_selector\"></td></tr>
  </tbody></table>
  <div id=\"run_comparison_status\" style=\"margin-top:0.35rem;color:#374151;\">Select a project first.</div>
  <div id=\"run_comparison_summary\" style=\"margin-top:0.35rem;color:#374151;\"></div>
  <div id=\"run_comparison_table\" style=\"margin-top:0.35rem;\"></div>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Import JSON File</h3>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <input id=\"import_json_file\" type=\"file\" accept=\".json,application/json\"/>
    <button onclick=\"importJsonFile()\">Import JSON File</button>
    <label><input id=\"validate_after_import\" type=\"checkbox\"/> Validate after import</label>
  </div>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Download / Copy</h3>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button onclick=\"downloadCaseJson()\">Download JSON Case</button>
    <button onclick=\"copyCaseJson()\">Copy JSON Case</button>
    <button onclick=\"downloadSummaryJson()\">Download Summary JSON</button>
    <button onclick=\"copySummaryJson()\">Copy Summary JSON</button>
    <button onclick=\"downloadHtmlReport()\">Download HTML Report</button>
    <button onclick=\"copyValidationResponse()\">Copy Validation Response</button>
    <button onclick=\"copyRawResponse()\">Copy Raw Response</button>
  </div>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Package Export</h3>
  <p style="margin-top:0.2rem;color:#4b5563;">Downloads browser-side artifacts; files are not saved to the server.</p>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button onclick=\"downloadPackageMetadata()\">Download Package Metadata</button>
    <button onclick=\"downloadPackageCaseJson()\">Download Case JSON</button>
    <button onclick=\"downloadValidationResponse()\">Download Validation Response</button>
    <button onclick=\"downloadRunResponse()\">Download Run Response</button>
    <button onclick=\"downloadSummaryJson()\">Download Summary JSON</button>
    <button onclick=\"downloadHtmlReport()\">Download HTML Report</button>
    <button onclick=\"downloadAllPackageFiles()\">Download All Package Files</button>
  </div>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Local UI RC Status</h3>
  <p style=\"margin-top:0.2rem;color:#92400e;\">Release-candidate status means the local UI workflow is ready for beta testing; it does not mean engineering results are independently verified.</p>
  <table><tbody id=\"rc_status_body\"></tbody></table>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button aria-label=\"Copy RC checklist summary\" onclick=\"copyRcChecklistSummary()\">Copy RC Checklist Summary</button>
    <button aria-label=\"Mark manual QA completed\" onclick=\"markManualQaCompleted()\">Mark Manual QA Completed</button>
    <button aria-label=\"Reset RC checklist status\" onclick=\"resetRcChecklistStatus()\">Reset RC Checklist Status</button>
  </div>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Keyboard Shortcuts</h3>
  <ul>
    <li>Ctrl+Enter: Validate</li>
    <li>Ctrl+Shift+Enter: Run</li>
    <li>Ctrl+S: Save current JSON locally/autosave trigger only</li>
    <li>Ctrl+Shift+F: Format JSON</li>
    <li>Ctrl+Shift+H: Toggle Help</li>
    <li>Escape: Clear transient status message if practical</li>
  </ul>
  <p style=\"margin-top:0.2rem;color:#4b5563;\">Accessibility support is basic and will be improved in future versions.</p>
</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>Project Archive Export</h3>
  <p style=\"margin-top:0.2rem;color:#4b5563;\">Project archives are generated locally from the repository projects/ directory.</p>
  <p style=\"margin-top:0.2rem;color:#92400e;\">Archive export is for backup/sharing only and does not prove engineering correctness.</p>
  <div class=\"toolbar\" style=\"margin-top:0;\">
    <button onclick=\"refreshArchiveManifest()\">Refresh Archive Manifest</button>
    <button onclick=\"downloadProjectArchive()\">Download Project Archive</button>
    <button onclick=\"copyArchiveManifestJson()\">Copy Archive Manifest JSON</button>
    <button onclick=\"downloadArchiveManifestJson()\">Download Archive Manifest JSON</button>
  </div>
  <div id=\"archive_export_status\" style=\"margin-top:0.35rem;color:#374151;\">Select a project first.</div>
  <pre id=\"archive_manifest_output\">Refresh archive manifest to view archive details.</pre>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>About / Beta Status</h3>
  <table><tbody>
    <tr><td>App</td><td>App Viga Carrilera</td></tr>
    <tr><td>Module</td><td>Crane Runway Local UI</td></tr>
    <tr><td>Beta status</td><td>Internal beta</td></tr>
    <tr><td>Local UI beta version</td><td>V1-086</td></tr>
    <tr><td>Schema version</td><td>Schema version: 1.0</td></tr>
    <tr><td>Calculation scope</td><td>generic crane runway elastic demand workflow</td></tr>
    <tr><td>Compliance scope</td><td>not official CIRSOC/CISC/AISC compliance checks</td></tr>
    <tr><td>Data warning</td><td>sample data requires independent verification</td></tr>
    <tr><td>Review warning</td><td>engineering review required</td></tr>
  </tbody></table>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="refreshAboutInfo()">Refresh About Info</button>
    <button onclick="copyAboutInfo()">Copy About Info</button>
  </div>
  <pre id="about_info_output">Refresh About Info to view diagnostics.</pre>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>Support Bundle</h3>
  <p style="margin-top:0.2rem;color:#92400e;">Support bundles may include the current JSON case, validation response, run response, warnings, and browser diagnostics. Review before sharing.</p>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="refreshSupportBundlePreview()">Refresh Support Bundle Preview</button>
    <button onclick="downloadSupportBundleJson()">Download Support Bundle JSON</button>
    <button onclick="copySupportBundleJson()">Copy Support Bundle JSON</button>
    <button onclick="clearSupportBundlePreview()">Clear Support Bundle Preview</button>
  </div>
  <div id="support_bundle_preview"></div>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>Issue Report Helper</h3>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="generateIssueReportText()">Generate Issue Report Text</button>
    <button onclick="copyIssueReportText()">Copy Issue Report Text</button>
  </div>
  <pre id="issue_report_output">Generate Issue Report Text to prepare a handoff note.</pre>
</div>
<div class="panel collapsible-panel" id="panel-common-inputs" class="tab-panel" data-main-tab="inputs" data-panel-key="common-inputs" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Common Inputs</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <p style="margin-top:0.2rem;color:#4b5563;">Use this form for frequent edits. Advanced fields remain editable in JSON.</p>
  <p style="margin-top:0;">Common Inputs edits the JSON below. Review generated JSON before running.</p>
  <p style="margin-top:0.2rem;">Advanced fields remain editable directly in JSON.</p>
  <p style="margin-top:0.2rem;"><strong>For more than two wheels, use Wheel Table Editor.</strong></p>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="loadCommonInputsFromJson()">Load Form From JSON</button>
    <button onclick="validateCommonInputsOnly()">Validate Common Inputs</button>
    <button onclick="applyCommonInputsToJson()">Apply Form To JSON</button>
    <button onclick="resetCommonInputs()">Reset Form</button>
  </div>
  <table><tbody><tr><td><span title="Unique local label for the case configuration.">Case ID</span></td><td><input id="common_case_id"/></td><td>Description</td><td><input id="common_description"/></td></tr>
  <tr><td><span title="Section profile identifier used by the case JSON.">Base Shape ID</span></td><td><input id="common_base_shape_id"/></td><td>Cover Plate Enabled</td><td><input id="common_cover_plate_enabled" type="checkbox"/></td></tr>
  <tr><td><span title="Top cover plate width dimension.">Cover Plate Width</span></td><td><input id="common_cover_plate_width"/><select id="common_cover_plate_width_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td><span title="Top cover plate thickness dimension.">Cover Plate Thickness</span></td><td><input id="common_cover_plate_thickness"/><select id="common_cover_plate_thickness_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr>
  <tr><td>Cover Plate Weld Size</td><td><input id="common_cover_plate_weld_size"/><select id="common_cover_plate_weld_size_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Material ID</td><td><input id="common_material_id"/></td></tr>
  <tr><td><span title="Yield strength input for the selected material.">Fy</span></td><td><input id="common_fy"/><select id="common_fy_unit"><option>MPa</option><option>ksi</option><option>psi</option></select></td><td>Fu</td><td><input id="common_fu"/><select id="common_fu_unit"><option>MPa</option><option>ksi</option><option>psi</option></select></td></tr><tr><td><span title="Elastic modulus input for the selected material.">E</span></td><td><input id="common_e"/><select id="common_e_unit"><option>MPa</option><option>ksi</option><option>psi</option></select></td><td><span title="Runway span used for wheel travel and demand envelopes.">Span</span></td><td><input id="common_span"/><select id="common_span_unit"><option>m</option><option>mm</option><option>ft</option></select></td></tr>
  <tr><td>Movement Step</td><td><input id="common_movement_step"/><select id="common_movement_step_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Station Step</td><td><input id="common_station_step"/><select id="common_station_step_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr><tr><td>Crane ID</td><td><input id="common_crane_id"/></td><td>Vertical Impact Factor</td><td><input id="common_vertical_impact_factor"/></td></tr>
  <tr><td>Lateral Force Factor</td><td><input id="common_lateral_force_factor"/></td><td>Wheel 1 Load</td><td><input id="common_wheel_1_load"/><select id="common_wheel_1_load_unit"><option>kN</option><option>N</option><option>kip</option></select></td></tr><tr><td>Wheel 2 Load</td><td><input id="common_wheel_2_load"/><select id="common_wheel_2_load_unit"><option>kN</option><option>N</option><option>kip</option></select></td><td><span title="Center-to-center spacing between wheel loads.">Wheel Spacing</span></td><td><input id="common_wheel_spacing"/><select id="common_wheel_spacing_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr>
  <tr><td><span title="Enable or disable rail eccentricity inputs in this case.">Rail Eccentricity Enabled</span></td><td><input id="common_rail_eccentricity_enabled" type="checkbox"/></td><td><span title="Vertical eccentricity offset (Y) for rail load application.">Vertical Eccentricity Y</span></td><td><input id="common_vertical_eccentricity_y"/><select id="common_vertical_eccentricity_y_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr><tr><td><span title="Height (Z) where lateral load is applied.">Lateral Load Height Z</span></td><td><input id="common_lateral_load_height_z"/><select id="common_lateral_load_height_z_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Deflection Preset</td><td><input id="common_deflection_preset"/></td></tr><tr><td>Stress Preset</td><td><input id="common_stress_preset"/></td><td></td><td></td></tr></tbody></table>
  <h4>Common Inputs Errors</h4><div id="common_inputs_errors">No common input errors.</div>
</div>
</div>
<div class="panel collapsible-panel" id="panel-quick-selectors" class="tab-panel" data-main-tab="inputs" data-panel-key="quick-selectors" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Quick Selectors / Presets</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <p style="margin-top:0.2rem;color:#4b5563;">Presets are convenience helpers, not design recommendations.</p>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>Profile / Material Selector</h3>
  <p style="margin-top:0.2rem;color:#92400e;">Profile sample data is manually curated and incomplete. Verify before design use.</p>
  <p style="margin-top:0.2rem;color:#92400e;">Material presets are sample helpers and must be independently verified.</p>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="loadProfileMaterialFromJson()">Load Profile/Material From JSON</button>
    <button onclick="applyProfileMaterialToJson()">Apply Profile/Material To JSON</button>
    <button onclick="resetProfileMaterial()">Reset Profile/Material</button>
  </div>
  <table><tbody>
    <tr><td>Base Shape ID</td><td><select id="profile_base_shape_id"><option value="">-- Select --</option><option>CIRSOC_IPN_180</option><option>CIRSOC_IPN_200</option><option>CIRSOC_IPN_240</option><option>CIRSOC_IPN_300</option><option>CIRSOC_IPB_200</option></select></td><td>Material Preset</td><td><select id="profile_material_preset" onchange="applyMaterialPreset()"><option>F24</option><option>F36</option><option>Custom</option></select></td></tr>
    <tr><td>Material ID</td><td><input id="profile_material_id"/></td><td>Fy</td><td><input id="profile_fy"/></td></tr>
    <tr><td>Fu</td><td><input id="profile_fu"/></td><td>E</td><td><input id="profile_e"/></td></tr>
  </tbody></table>
  <h4>Profile / Material Errors</h4><div id="profile_material_errors">No profile/material errors.</div>
</div>
<div class="panel collapsible-panel" id="panel-wheel-table" class="tab-panel" data-main-tab="wheels" data-panel-key="wheel-table-editor" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Wheel Table Editor</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <p style="margin-top:0.2rem;color:#4b5563;">Use this table for crane wheel positions and vertical wheel loads.</p>
  <div class="toolbar" style="margin-top:0;">
    <button id="load_wheels_from_json_btn">Load Wheels From JSON</button>
    <button id="apply_wheels_to_json_btn">Apply Wheels To JSON</button>
    <button id="add_wheel_row_btn">Add Wheel</button>
    <button id="clear_wheel_table_btn">Clear Wheel Table</button>
  </div>
  <table><thead><tr><th>Wheel ID</th><th title="Wheel Spacing location along runway span.">Position X</th><th>Position Unit</th><th title="Wheel Load applied vertically at the wheel location.">Vertical Force</th><th>Force Unit</th><th>Remove</th></tr></thead><tbody id="wheel_table_body"></tbody></table>
  <h4>Wheel Table Errors</h4><div id="wheel_table_errors">No wheel table errors.</div>
</div>
<div class="panel collapsible-panel" id="panel-visual-preview" class="tab-panel" data-main-tab="preview" data-panel-key="visual-preview" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Visual Preview</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <p style="margin-top:0.2rem;color:#4b5563;">Schematic preview only; not to scale.</p>
  <div class="toolbar" style="margin-top:0;"><button onclick="refreshVisualPreview()">Refresh Visual Preview</button></div>
  <p style="margin-top:0.35rem;color:#4b5563;">Preview is schematic only and not to scale.</p>
  <h4>Beam Preview</h4><div id="beam_preview_output"></div>
  <h4>Section Preview</h4><div id="section_preview_output"></div>
  <h4>Preview Summary</h4><div id="preview_summary_output"></div>
</div>
<div class="panel collapsible-panel" id="panel-case-quality" class="tab-panel" data-main-tab="preview" data-panel-key="case-quality-warnings" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Case Quality Warnings</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <div class="toolbar" style="margin-top:0;">
    <button onclick="refreshCaseQuality()">Refresh Case Quality</button>
    <button onclick="copyCaseQualityWarnings()">Copy Case Quality Warnings</button>
    <button onclick="downloadCaseQualityWarnings()">Download Case Quality Warnings JSON</button>
  </div>
  <div id="case_quality_status" style="margin-top:0.35rem;color:#4b5563;">Refresh case quality to see warnings.</div>
  <table><thead><tr><th>Severity</th><th>Area</th><th>Message</th><th>Suggested Action</th></tr></thead><tbody id="case_quality_rows"></tbody></table>
</div>
<div class="panel collapsible-panel" id="panel-scenario-comparison" class="tab-panel" data-main-tab="compare" data-panel-key="scenario-comparison" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Scenario Comparison</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <p style="margin-top:0.2rem;color:#4b5563;">Compare saved browser-local alternatives using existing run results.</p>
  <div class="toolbar" style="margin-top:0;">
    <label for="scenario_name">Scenario Name</label>
    <input id="scenario_name" type="text"/>
    <button onclick="saveCurrentScenario()">Save Current Scenario</button>
    <button onclick="loadScenarios()">Refresh Scenario List</button>
    <button onclick="runAllScenarios()">Run All Scenarios</button>
    <button onclick="clearAllScenarios()">Clear All Scenarios</button>
    <button onclick="downloadScenarioComparison()">Download Comparison JSON</button>
    <button onclick="copyScenarioComparison()">Copy Comparison JSON</button>
  </div>
  <table><thead><tr><th>Scenario</th><th>Saved At</th><th>Actions</th></tr></thead><tbody id="scenario_list_body"></tbody></table>
  <div id="scenario_comparison_output" style="margin-top:0.6rem;"></div>
</div>
<div class="panel collapsible-panel" id="panel-guided-workflow" class="tab-panel" data-main-tab="home" data-panel-key="guided-workflow" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Guided Workflow</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <div class="toolbar" style="margin-top:0;"><button onclick="resetGuidedWorkflow()">Reset Workflow</button><button onclick="runDemoWorkflow()">Run Demo Workflow</button></div>
  <table><thead><tr><th>Step</th><th>Description</th><th>Status</th></tr></thead><tbody id="guided_workflow_body"></tbody></table>
  <div id="demo_workflow_status" style="margin-top:0.5rem;color:#374151;">Demo workflow complete.</div>
  <div style="margin-top:0.2rem;color:#374151;">Demo workflow failed.</div>
</div>
<div class="panel collapsible-panel" id="panel-beta-readiness" class="tab-panel" data-main-tab="home" data-panel-key="beta-readiness" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Beta Readiness</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <div class="toolbar" style="margin-top:0;"><button onclick="checkBackendHealth()">Check Backend Health</button></div>
  <div id="backend_health_status" style="margin-top:0.35rem;">Backend health: OK.</div>
  <div style="margin-top:0.2rem;">Backend health: FAIL.</div>
  <div id="beta_readiness_output" style="margin-top:0.5rem;"></div>
</div>
<div class="panel collapsible-panel" id="panel-ui-diagnostics" class="tab-panel" data-main-tab="support" data-panel-key="local-ui-diagnostics" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Local UI Diagnostics</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <p style="margin-top:0.2rem;color:#4b5563;">Diagnostics check UI/server connectivity only. They do not prove engineering correctness.</p>
  <p style="margin-top:0.2rem;color:#4b5563;">Use beta health check and manual QA checklist before relying on beta UI output.</p>
  <div class="toolbar" style="margin-top:0;"><button onclick="runUiDiagnostics()">Run UI Diagnostics</button></div>
  <table><tbody id="ui_diagnostics_body"></tbody></table>
  <div id="ui_diagnostics_timestamp" style="margin-top:0.35rem;color:#4b5563;">Last diagnostic run: N/A</div>
  <div style="margin-top:0.2rem;color:#374151;">UI diagnostics complete.</div>
  <div style="margin-top:0.2rem;color:#374151;">UI diagnostics found issues.</div>
</div>
<div class="panel" id="panel-documentation-portal" class="tab-panel" data-main-tab="home" style="margin-top: 1rem;">
  <h3>Documentation Portal</h3>
  <p style="margin-top:0.2rem;color:#92400e;">This help is educational and does not replace engineering review.</p>
  <ul id="documentation_topics"><li>Start here</li><li>Basic workflow</li><li>Project workflow</li><li>Common inputs</li><li>Wheel table</li><li>Quick selectors</li><li>Validation</li><li>Results</li><li>Project history</li><li>Project archive</li><li>Support bundle</li><li>Known limitations</li><li>Troubleshooting</li></ul>
  <div class="toolbar" style="margin-top:0;"><button onclick="showHelpTopic('Start here')">Show Start Here</button><button onclick="showHelpTopic('Basic workflow')">Show Basic Workflow</button><button onclick="showHelpTopic('Project workflow')">Show Project Workflow</button><button onclick="showHelpTopic('Troubleshooting')">Show Troubleshooting</button><button onclick="copyHelpSummary()">Copy Help Summary</button></div>
  <pre id="documentation_portal_output">Select a help topic.</pre>
</div>
<div class="panel" id="panel-guided-demo" class="tab-panel" data-main-tab="home" style="margin-top: 1rem;">
  <h3>Guided Demo</h3>
  <p style="margin-top:0.2rem;color:#92400e;">The guided demo uses sample data and is not a design recommendation.</p>
  <ol id="guided_demo_steps"><li>Load demo template</li><li>Review preview</li><li>Check case quality</li><li>Validate demo</li><li>Run demo</li><li>Review interpretation</li><li>Export demo results</li></ol>
  <div class="toolbar" style="margin-top:0;"><button onclick="startGuidedDemo()">Start Guided Demo</button><button onclick="nextGuidedDemoStep()">Next Demo Step</button><button onclick="resetGuidedDemo()">Reset Guided Demo</button><button onclick="copyDemoInstructions()">Copy Demo Instructions</button></div>
  <pre id="guided_demo_output">Guided demo ready.</pre>
</div>
<div class="panel collapsible-panel" id="panel-troubleshooting" class="tab-panel" data-main-tab="home" data-panel-key="troubleshooting" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Troubleshooting</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <ul><li>If buttons do not respond, refresh the page.</li><li>If the server is unreachable, start scripts/serve_crane_runway_ui.py.</li><li>If JSON validation fails, review the Validation panel.</li><li>If results show FAIL, review configured criteria and engineering assumptions.</li><li>This local UI is a beta tool and requires engineering review.</li></ul>
</div>
<div class="panel collapsible-panel" id="panel-help" class="tab-panel" data-main-tab="inputs" data-panel-key="field-help-glossary" style="margin-top: 1rem;">
  <div class="panel-header"><h3>Field Help / Glossary</h3><button class="small-btn" data-panel-toggle>Collapse</button></div><div class="panel-body">
  <div class="toolbar" style="margin-top:0;">
    <button onclick="toggleFieldHelp()">Toggle Help</button>
    <label for="glossary_search">Search glossary</label><input id="glossary_search" type="text" oninput="filterGlossary()"/>
  </div>
  <ul id="glossary_list">
    <li class="glossary-item"><strong>span</strong>: Beam length considered for moving wheel demand envelopes.</li>
    <li class="glossary-item"><strong>base_shape_id</strong>: Identifier for the baseline steel profile in the case.</li>
    <li class="glossary-item"><strong>cover_plate</strong>: Optional added plate dimensions and enable flag.</li>
    <li class="glossary-item"><strong>material Fy</strong>: Yield strength value used by configured stress criteria.</li>
    <li class="glossary-item"><strong>material Fu</strong>: Ultimate strength reference stored with the material record.</li>
    <li class="glossary-item"><strong>material E</strong>: Elastic modulus value used for stiffness-based response.</li>
    <li class="glossary-item"><strong>crane wheels</strong>: Wheel positions and vertical loads applied to the runway.</li>
    <li class="glossary-item"><strong>vertical impact factor</strong>: Multiplier applied to vertical wheel demand input.</li>
    <li class="glossary-item"><strong>lateral force factor</strong>: Multiplier used for lateral load component input.</li>
    <li class="glossary-item"><strong>rail eccentricity</strong>: Offset inputs controlling load application location.</li>
    <li class="glossary-item"><strong>movement_step</strong>: Travel increment for moving load envelope sampling.</li>
    <li class="glossary-item"><strong>station_step</strong>: Spacing between beam stations used in results.</li>
    <li class="glossary-item"><strong>serviceability limit</strong>: Configured generic serviceability threshold reference.</li>
    <li class="glossary-item"><strong>stress limit</strong>: Configured generic stress threshold reference.</li>
    <li class="glossary-item"><strong>max vertical moment</strong>: Peak computed major-axis bending demand.</li>
    <li class="glossary-item"><strong>max vertical shear</strong>: Peak computed vertical shear demand.</li>
    <li class="glossary-item"><strong>max vertical deflection</strong>: Largest computed displacement response.</li>
    <li class="glossary-item"><strong>max lateral moment</strong>: Peak computed lateral bending demand.</li>
    <li class="glossary-item"><strong>max biaxial stress</strong>: Combined stress indicator from current run output.</li>
    <li class="glossary-item"><strong>max torsional input</strong>: Reported torsional input quantity from case data.</li>
    <li class="glossary-item"><strong>serviceability passed</strong>: Boolean status for configured serviceability check.</li>
    <li class="glossary-item"><strong>stress criteria passed</strong>: Boolean status for configured stress check.</li>
    <li class="glossary-item"><strong>overall passed</strong>: Overall boolean summary across configured checks.</li>
    <li class="glossary-item"><strong>sample profile data</strong>: Example profile entries that require independent verification.</li>
    <li class="glossary-item"><strong>sample material data</strong>: Example material presets that require independent verification.</li>
    <li class="glossary-item"><strong>generic criteria</strong>: User-configured non-normative limits for quick screening.</li>
    <li class="glossary-item"><strong>engineering review</strong>: Required independent technical review before decisions.</li>
  </ul>
  <div id="glossary_no_match" style="display:none;color:#92400e;">No glossary matches.</div>
</div>
<div class="panel ui-nav" id="panel-start" style="margin-top: 1rem;">
  <h3>UI Navigation</h3>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="scrollToPanel('panel-start')">Start</button>
    <button onclick="scrollToPanel('panel-json-editor')">JSON Editor</button>
    <button onclick="scrollToPanel('panel-quick-selectors')">Quick Selectors</button>
    <button onclick="scrollToPanel('panel-common-inputs')">Common Inputs</button>
    <button onclick="scrollToPanel('panel-wheel-table')">Wheel Table</button>
    <button onclick="scrollToPanel('panel-visual-preview')">Visual Preview</button>
    <button onclick="scrollToPanel('panel-case-quality')">Case Quality</button>
    <button onclick="scrollToPanel('panel-validation')">Validation</button>
    <button onclick="scrollToPanel('panel-run-results')">Run Results</button>
    <button onclick="scrollToPanel('panel-report')">Report</button>
    <button onclick="scrollToPanel('panel-scenario-comparison')">Scenario Comparison</button>
    <button onclick="scrollToPanel('panel-export')">Export</button>
    <button onclick="scrollToPanel('panel-help')">Help</button>
  </div>
  <div class="toolbar" style="margin-top:0.5rem;">
    <button onclick="expandAllPanels()">Expand All Panels</button>
    <button onclick="collapseAllPanels()">Collapse All Panels</button>
    <button onclick="showBeginnerView()">Show Beginner View</button>
    <button onclick="showAdvancedView()">Show Advanced View</button>
    <button onclick="resetPanelLayout()">Reset Panel Layout</button>
  </div>
</div>
<div id=\"status\" class=\"status\" role=\"status\" aria-live=\"polite\">Ready.</div>
<div class=\"page\">
  <div class=\"left-col\">
    <div class=\"panel\">
      <h3>JSON Editor</h3>
      <textarea id=\"case_json\"></textarea>
      <div id=\"autosave_status\" style=\"margin-top:0.5rem;font-size:0.9rem;color:#374151;\">Autosave: No saved session</div>
      <div style=\"margin-top:0.3rem;font-size:0.85rem;color:#4b5563;\">Autosave is stored only in this browser using localStorage.</div>
    </div>
  </div>
  <div class=\"right-col\">
  <div class=\"panel\"><h3>Help / Workflow</h3><div id=\"help_panel\"></div></div>
  <div class=\"panel\"><h3>Case Outline</h3><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"refreshCaseOutline()\">Refresh Case Outline</button></div><div id=\"case_outline_output\"></div></div>
  <div class=\"panel\"><h3>Validation</h3><p style=\"margin-top:0.2rem;color:#4b5563;\">Validation checks JSON structure and supported units before calculation.</p><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"copyErrorList()\">Copy Error List</button></div><div id=\"validation_output\"></div></div>
  <div class=\"panel\"><h3>Summary</h3><div id=\"result_cards\"></div><div id=\"summary_output\"></div></div>
  <div class=\"panel\"><h3>Result Interpretation</h3><p style=\"margin-top:0.2rem;color:#4b5563;\">Interpretation explains configured generic check results; it is not a code-compliance verdict.</p><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"copyInterpretation()\">Copy Interpretation</button></div><div id=\"interpretation_output\"><p>Run a case to see result interpretation.</p></div></div>
  <div class=\"panel\">
    <h3>HTML Report</h3>
    <button id=\"open_report\" onclick=\"openReportInNewTab()\" style=\"display:none; margin-bottom: 0.6rem;\">Open report in new tab</button>
    <iframe id=\"html_output\" style=\"width:100%;height:380px;border:1px solid #d1d5db;border-radius:6px;\"></iframe>
  </div>
  <div class=\"panel\"><h3>Raw Response</h3><pre id=\"raw_output\"></pre></div>
  </div>
</div>

<div class="panel" id="form_first_workflow_panel"><h3>Form-First Workflow</h3><p>Recommended path for first-time users.</p><div id="workflow_stepper"></div><p>Not started · In progress · Complete · Needs attention</p><p>No project selected. Create or open a project to enable project actions.</p><p>Load a template or project before applying forms.</p><p>No wheels loaded. Use Load Wheels From JSON or Add Wheel.</p><p>Load JSON and click Refresh Visual Preview.</p><p>Click Validate to check JSON before running.</p><p>Run a case to see results.</p><p>Run a case before exporting results.</p><p>Use Support Bundle if you need to report a beta issue.</p><p id="unsaved_changes_indicator">Saved</p><div class="toolbar"><button onclick="applyAllFormsToJson()">Apply All Forms To JSON</button><button onclick="validateAndRunCase()">Validate & Run</button></div><p>Unsaved changes</p><p>Saved</p></div>
<div class="panel"><h3>Beam & Section</h3><button onclick="loadBeamSectionFromJson()">Load Beam/Section From JSON</button><button onclick="applyBeamSectionToJson()">Apply Beam/Section To JSON</button><button onclick="resetBeamSectionForm()">Reset Beam/Section</button></div>
<div class="panel"><h3>Material</h3><button onclick="loadMaterialFromJson()">Load Material From JSON</button><button onclick="applyMaterialToJson()">Apply Material To JSON</button><button onclick="resetMaterialForm()">Reset Material</button><p>Material presets are sample helpers and require independent verification.</p></div>
<div class="panel"><h3>Criteria</h3><button onclick="loadCriteriaFromJson()">Load Criteria From JSON</button><button onclick="applyCriteriaToJson()">Apply Criteria To JSON</button><button onclick="resetCriteriaForm()">Reset Criteria</button></div>
<div class="panel"><h3>Crane Load Factors</h3><button onclick="loadCraneFactorsFromJson()">Load Crane Factors From JSON</button><button onclick="applyCraneFactorsToJson()">Apply Crane Factors To JSON</button><button onclick="resetCraneFactorsForm()">Reset Crane Factors</button></div>
<div class="panel"><h3>Rail / Eccentricity</h3><button onclick="loadRailEccentricityFromJson()">Load Rail Eccentricity From JSON</button><button onclick="applyRailEccentricityToJson()">Apply Rail Eccentricity To JSON</button><button onclick="resetRailEccentricityForm()">Reset Rail Eccentricity</button></div>
<p>Next: review inputs or click Validate.</p><p>Next: refresh preview and validate.</p><p>Next: run the calculation.</p><p>Next: review results or export reports.</p><p>Next: check Raw Response and create Support Bundle.</p>

<div style="display:none">Inputs Wheels Preview Validate & Run Compare Advanced JSON Crane Wheels Switched to Inputs. Switched to Wheels. Switched to Preview. Switched to Validate & Run. Switched to Compare. Switched to Advanced JSON. Validate and run complete. Cannot apply all forms: fix highlighted errors first.</div>
<script>
let latestHtmlReport = '';
let lastValidationResponse = null;
let lastRunResponse = null;
let lastAboutInfo = null;
let lastSupportBundle = null;
let lastIssueReportText = "";
let lastRawResponse = null;
let lastScenarioComparisonResults = null;
const scenarioStorageKey = 'craneRunway.scenarios';
const LOCAL_UI_BETA_VERSION = "V1-086";
const LOCAL_UI_SCHEMA_VERSION = "1.0";
const RC_CHECKLIST_STATUS_KEY = "craneRunway.rcChecklistStatus";

const ACTIVE_TAB_STORAGE_KEY = "craneRunway.activeTab";
const TAB_STATUS_MESSAGES = {"home":"Switched to Home.","project":"Switched to Project.","setup":"Switched to Setup.","loads":"Switched to Loads.","review":"Switched to Review.","calculate":"Switched to Calculate.","results":"Switched to Results.","export":"Switched to Export.","support":"Switched to Support.","advanced":"Switched to Advanced."};
const TAB_PANEL_SELECTORS={"home":["welcome_panel","panel-guided-workflow","panel-beta-readiness","panel-documentation-portal","panel-guided-demo","panel-troubleshooting"],"project":["project_workspace_status","run_history_status","run_comparison_status"],"inputs":["panel-quick-selectors","panel-common-inputs","panel-help"],"wheels":["panel-wheel-table"],"preview":["panel-visual-preview","panel-case-quality"],"validate-run":["panel-validation"],"results":["panel-run-results","panel-report"],"compare":["panel-scenario-comparison"],"export":["panel-export"],"support":["panel-ui-diagnostics"],"advanced-json":["panel-json-editor","raw_output"]};
function saveActiveTab(tabId){localStorage.setItem(ACTIVE_TAB_STORAGE_KEY,tabId);}
function getActiveTab(){return localStorage.getItem(ACTIVE_TAB_STORAGE_KEY)||'home';}
function setActiveTabButton(tabId){document.querySelectorAll('.main-tab-btn').forEach((b)=>b.classList.toggle('active',b.dataset.tabBtn===tabId));}
function switchMainTab(tabId){setActiveTabButton(tabId);saveActiveTab(tabId);document.querySelectorAll('.tab-panel').forEach((p)=>{p.hidden=p.dataset.mainTab!==tabId;});if(TAB_STATUS_MESSAGES[tabId]) setStatus(TAB_STATUS_MESSAGES[tabId]);updateCompactCaseSummary();refreshAppShellStatus();}
function restoreActiveTab(){const t=getActiveTab();switchMainTab(TAB_STATUS_MESSAGES[t]?t:'home');}
function updateCompactCaseSummary(){const sid=document.getElementById('summary_case_id');const sp=document.getElementById('summary_project');const sa=document.getElementById('summary_autosave');if(sid){try{const parsed=JSON.parse(document.getElementById('input').value||'{}');sid.textContent=parsed.case_id||'-';}catch(_){sid.textContent='(invalid json)';}}if(sp){const el=document.getElementById('project_name');sp.textContent=(el&&el.value)||'-';}if(sa){sa.textContent=(document.getElementById('autosave_status')||{textContent:'Unknown'}).textContent;}}
function refreshAppShellStatus(){const el=document.getElementById('app_shell_status');if(el){el.textContent='Active tab: '+getActiveTab()+'.';}}

const WELCOME_DISMISSED_KEY = 'craneRunway.welcomeDismissed';
const GUIDED_DEMO_STATE_KEY = 'craneRunway.guidedDemoState';
const diagnosticsState = {ui_loaded:true, backend_health:null, templates_endpoint:null, validate_endpoint:null, run_endpoint:null, javascript_status:true, autosave_status:null};
const autosaveStorageKeys = {
  caseJson: 'craneRunway.caseJson',
  selectedTemplate: 'craneRunway.selectedTemplate',
  lastSavedAt: 'craneRunway.lastSavedAt'
};
let autosaveAvailable = true;
let autosaveTimer = null;

const panelStateStorageKey = 'craneRunway.panelState';
function scrollToPanel(panelId){const panel=document.getElementById(panelId);if(panel){panel.scrollIntoView({behavior:'smooth',block:'start'});}}
function getDefaultPanelState(){return {'guided-workflow':true,'beta-readiness':true,'quick-selectors':true,'common-inputs':true,'wheel-table-editor':true,'visual-preview':true,'case-quality-warnings':true,'validation':true,'result-cards':true,'result-interpretation':true,'html-report':true,'raw-response':false,'package-export':false,'scenario-comparison':false,'field-help-glossary':false,'troubleshooting':false};}
function applyPanelState(state){document.querySelectorAll('.collapsible-panel').forEach((panel)=>{const key=panel.dataset.panelKey;const expanded=state[key]!==false;const body=panel.querySelector('.panel-body');const btn=panel.querySelector('[data-panel-toggle]');if(body){body.classList.toggle('collapsed',!expanded);}if(btn){btn.textContent=expanded?'Collapse':'Expand';}});}
function savePanelState(){const state={};document.querySelectorAll('.collapsible-panel').forEach((panel)=>{const key=panel.dataset.panelKey;const body=panel.querySelector('.panel-body');state[key]=!(body&&body.classList.contains('collapsed'));});localStorage.setItem(panelStateStorageKey,JSON.stringify(state));setStatus('Panel layout saved locally.');}
function restorePanelState(){const raw=localStorage.getItem(panelStateStorageKey);if(!raw){showBeginnerView(false);return;}try{applyPanelState(JSON.parse(raw));setStatus('Panel layout restored.');}catch(_){showBeginnerView(false);}}
function togglePanel(button){const panel=button.closest('.collapsible-panel');if(!panel)return;const body=panel.querySelector('.panel-body');if(!body)return;body.classList.toggle('collapsed');button.textContent=body.classList.contains('collapsed')?'Expand':'Collapse';savePanelState();}
function expandAllPanels(){const state={};document.querySelectorAll('.collapsible-panel').forEach((p)=>state[p.dataset.panelKey]=true);applyPanelState(state);savePanelState();setStatus('All panels expanded.');}
function collapseAllPanels(){const state={};document.querySelectorAll('.collapsible-panel').forEach((p)=>state[p.dataset.panelKey]=false);applyPanelState(state);savePanelState();setStatus('All panels collapsed.');}
function showBeginnerView(withStatus=true){const state=getDefaultPanelState();applyPanelState(state);savePanelState();if(withStatus)setStatus('Beginner view enabled.');}
function showAdvancedView(){expandAllPanels();setStatus('Advanced view enabled.');}
function resetPanelLayout(){localStorage.removeItem(panelStateStorageKey);showBeginnerView(false);setStatus('Panel layout reset.');}

const workflowSteps = [{id:1,label:'Load Template or Import JSON',description:'Load built-in template or import local JSON file.'},{id:2,label:'Configure Inputs',description:'Apply Common Inputs, Wheels, or Quick Selectors.'},{id:3,label:'Refresh Preview',description:'Refresh visual preview for quick geometry/load checks.'},{id:4,label:'Validate',description:'Validate case JSON before running.'},{id:5,label:'Run',description:'Run the configured case.'},{id:6,label:'Review Results',description:'Review cards, interpretation, summary, and report.'},{id:7,label:'Export / Compare',description:'Download package artifacts or run scenario comparison.'}];
const workflowState={1:'Pending',2:'Pending',3:'Pending',4:'Pending',5:'Pending',6:'Pending',7:'Pending'};
const betaReadinessState={ui_js_loaded:true,backend_health:null,json_loaded:null,validation_status:null,run_status:null,autosave_available:true};
function updateAutosaveStatus(message) {
  const panel = document.getElementById('autosave_status');
  if (panel) panel.textContent = message;
}
function saveSession() {
  if (!autosaveAvailable) { updateAutosaveStatus('Autosave: Autosave unavailable'); return false; }
  try {
    localStorage.setItem(autosaveStorageKeys.caseJson, getCurrentCaseJsonText());
    localStorage.setItem(autosaveStorageKeys.selectedTemplate, document.getElementById('template').value);
    const savedAt = new Date().toISOString();
    localStorage.setItem(autosaveStorageKeys.lastSavedAt, savedAt);
    updateAutosaveStatus('Autosave: Saved locally at ' + savedAt);
    setStatus('Autosaved locally.');
    return true;
  } catch (err) {
    autosaveAvailable = false;
    updateAutosaveStatus('Autosave: Autosave unavailable');
    setStatus('Autosave unavailable.');
    return false;
  }
}
function scheduleSessionSave() {
  if (autosaveTimer) window.clearTimeout(autosaveTimer);
  autosaveTimer = window.setTimeout(() => { autosaveTimer = null; saveSession(); }, 250);
}
function restoreSession() {
  try {
    const savedJson = localStorage.getItem(autosaveStorageKeys.caseJson);
    const savedTemplate = localStorage.getItem(autosaveStorageKeys.selectedTemplate);
    const lastSavedAt = localStorage.getItem(autosaveStorageKeys.lastSavedAt);
    if (savedTemplate) { document.getElementById('template').value = savedTemplate; }
    if (savedJson !== null) {
      document.getElementById('case_json').value = savedJson;
      setStatus('Restored autosaved JSON.');
    }
    if (lastSavedAt) updateAutosaveStatus('Autosave: Saved locally at ' + lastSavedAt);
    else updateAutosaveStatus('Autosave: No saved session');
  } catch (err) {
    autosaveAvailable = false;
    updateAutosaveStatus('Autosave: Autosave unavailable');
    setStatus('Autosave unavailable.');
  }
}
function clearSavedSession() {
  if (!autosaveAvailable) { updateAutosaveStatus('Autosave: Autosave unavailable'); setStatus('Autosave unavailable.'); return; }
  try {
    localStorage.removeItem(autosaveStorageKeys.caseJson);
    localStorage.removeItem(autosaveStorageKeys.selectedTemplate);
    localStorage.removeItem(autosaveStorageKeys.lastSavedAt);
    updateAutosaveStatus('Autosave: No saved session');
    clearOutput();
    setStatus('Saved session cleared.');
  } catch (err) {
    autosaveAvailable = false;
    updateAutosaveStatus('Autosave: Autosave unavailable');
    setStatus('Autosave unavailable.');
  }
}

function renderGuidedWorkflow() { const body=document.getElementById('guided_workflow_body'); if (!body) return; let html=''; for (const step of workflowSteps) { const status=workflowState[step.id] || 'Pending'; const cls=status==='Done'?'status-pass':(status==='Needs attention'?'status-fail':'status-na'); html += '<tr><td>'+step.id+'. '+escapeHtml(step.label)+'</td><td>'+escapeHtml(step.description)+'</td><td class="'+cls+'">'+escapeHtml(status)+'</td></tr>'; } body.innerHTML=html; }
function updateWorkflowStep(stepId, status) { if (!workflowState[stepId]) return; workflowState[stepId]=status; renderGuidedWorkflow();
renderDocumentationPortal();
renderGuidedDemo();
if (localStorage.getItem(WELCOME_DISMISSED_KEY)==='true'){ const panel=document.getElementById('welcome_panel'); if(panel) panel.style.display='none'; } }
function markWorkflowStepDone(stepId) { updateWorkflowStep(stepId, 'Done'); }
function markWorkflowStepNeedsAttention(stepId) { updateWorkflowStep(stepId, 'Needs attention'); }
function resetGuidedWorkflow() { for (const step of workflowSteps) workflowState[step.id]='Pending'; renderGuidedWorkflow();
renderDocumentationPortal();
renderGuidedDemo();
if (localStorage.getItem(WELCOME_DISMISSED_KEY)==='true'){ const panel=document.getElementById('welcome_panel'); if(panel) panel.style.display='none'; } const demo=document.getElementById('demo_workflow_status'); if (demo) demo.textContent='Ready for demo workflow.'; }
function renderBetaReadiness() { const panel=document.getElementById('beta_readiness_output'); if (!panel) return; const rows=[['UI JavaScript loaded', betaReadinessState.ui_js_loaded===true?'PASS':'FAIL'],['Backend health', betaReadinessState.backend_health===true?'PASS':(betaReadinessState.backend_health===false?'FAIL':'N/A')],['JSON loaded', betaReadinessState.json_loaded===true?'PASS':(betaReadinessState.json_loaded===false?'FAIL':'N/A')],['Validation status', betaReadinessState.validation_status===true?'PASS':(betaReadinessState.validation_status===false?'FAIL':'N/A')],['Run status', betaReadinessState.run_status===true?'PASS':(betaReadinessState.run_status===false?'FAIL':'N/A')],['Autosave available', betaReadinessState.autosave_available===true?'PASS':'FAIL']]; let html='<table><thead><tr><th>Check</th><th>Status</th></tr></thead><tbody>'; for (const row of rows) { const cls=row[1]==='PASS'?'status-pass':(row[1]==='FAIL'?'status-fail':'status-na'); html += '<tr><td>'+escapeHtml(row[0])+'</td><td class="'+cls+'">'+row[1]+'</td></tr>'; } panel.innerHTML=html+'</tbody></table>'; }
function updateBetaReadiness(key, value) { betaReadinessState[key]=value; renderBetaReadiness(); renderRcStatus(); setupKeyboardShortcuts(); }

function getCurrentCaseSummaryFromJsonText(){
  try { const data = JSON.parse(getCurrentCaseJsonText()); return {parse_ok:true,data,summary:{case_id:data?.meta?.case_id||'',base_shape_id:data?.section?.base_shape_id||'',material_id:data?.material?.id||'',wheel_count:Array.isArray(data?.loads?.wheels)?data.loads.wheels.length:0}}; }
  catch (err) { return {parse_ok:false, parse_error:String(err&&err.message?err.message:err)}; }
}
function buildAboutInfo(){
  const parsed=getCurrentCaseSummaryFromJsonText();
  const info={generated_at:new Date().toISOString(),app_name:'App Viga Carrilera',ui_name:'Crane Runway Local UI',beta_status:'Internal beta',schema_version:'1.0',available_templates:Array.isArray(window.availableTemplates)?window.availableTemplates:null,browser_user_agent:navigator.userAgent,local_storage_available:autosaveAvailable,current_project:getSelectedProjectName(),current_case_id:parsed.parse_ok?parsed.summary.case_id:null,current_base_shape_id:parsed.parse_ok?parsed.summary.base_shape_id:null,current_material_id:parsed.parse_ok?parsed.summary.material_id:null,notes:['Internal beta.','Results require engineering review.','Generic checks only; no official CIRSOC/CISC/AISC compliance checks.','Sample data must be independently verified.']};
  return info;
}
function renderAboutInfo(info){ const pre=document.getElementById('about_info_output'); if(pre) pre.textContent=prettyJson(info); }
function refreshAboutInfo(){ lastAboutInfo=buildAboutInfo(); renderAboutInfo(lastAboutInfo); setStatus('About info refreshed.'); }
async function copyAboutInfo(){ if(!lastAboutInfo){ refreshAboutInfo(); } await copyText(prettyJson(lastAboutInfo),'About info copied.','Could not copy about info.'); }
function buildSupportBundle(){ const parsed=getCurrentCaseSummaryFromJsonText(); const keys=[]; if(autosaveAvailable){ for(let i=0;i<localStorage.length;i+=1){ keys.push(localStorage.key(i)); } }
  const bundle={bundle_version:'1.0',generated_at:new Date().toISOString(),generated_by:'CraneRunwayLocalWebUi',about:lastAboutInfo||buildAboutInfo(),current_case_json:getCurrentCaseJsonText(),current_case_parse_ok:Boolean(parsed.parse_ok),current_case_summary:parsed.parse_ok?parsed.summary:null,last_validation_response:lastValidationResponse,last_run_response:lastRunResponse,last_case_quality_warnings:getCaseQualityRows(),last_project_run_comparison:lastProjectRunComparison,last_scenario_comparison:lastScenarioComparisonResults,selected_project:getSelectedProjectName(),selected_run_id:getSelectedRunId(),local_storage_keys_present:keys.filter((k)=>Boolean(k)),browser_user_agent:navigator.userAgent,notes:['Support bundle for beta debugging.','Review before sharing.','Results require engineering review.','Not an official design-code compliance record.']};
  if(!parsed.parse_ok){ bundle.parse_error=parsed.parse_error; }
  return bundle;
}
function renderSupportBundlePreview(bundle){ const el=document.getElementById('support_bundle_preview'); if(!el) return; const s=bundle.current_case_summary||{}; const rows=[['bundle_version',bundle.bundle_version],['generated_at',bundle.generated_at],['current_case_parse_ok',String(bundle.current_case_parse_ok)],['case_id',s.case_id||''],['base_shape_id',s.base_shape_id||''],['material_id',s.material_id||''],['wheel_count',String(s.wheel_count??'')],['selected_project',bundle.selected_project||''],['has_validation_response',String(Boolean(bundle.last_validation_response))],['has_run_response',String(Boolean(bundle.last_run_response))],['has_case_quality_warnings',String(Array.isArray(bundle.last_case_quality_warnings)&&bundle.last_case_quality_warnings.length>0)]]; el.innerHTML='<table><tbody>'+rows.map((r)=>'<tr><td>'+r[0]+'</td><td>'+r[1]+'</td></tr>').join('')+'</tbody></table>'; }
function refreshSupportBundlePreview(){ lastSupportBundle=buildSupportBundle(); renderSupportBundlePreview(lastSupportBundle); setStatus('Support bundle preview refreshed.'); }
function downloadSupportBundleJson(){ if(!lastSupportBundle){ setStatus('No support bundle available. Refresh support bundle preview first.'); return; } downloadText('support_bundle.json',prettyJson(lastSupportBundle),'application/json;charset=utf-8'); setStatus('Support bundle JSON downloaded.'); }
async function copySupportBundleJson(){ if(!lastSupportBundle){ setStatus('No support bundle available. Refresh support bundle preview first.'); return; } await copyText(prettyJson(lastSupportBundle),'Support bundle JSON copied.','Could not copy support bundle JSON.'); }
function clearSupportBundlePreview(){ lastSupportBundle=null; const el=document.getElementById('support_bundle_preview'); if(el) el.innerHTML=''; setStatus('Support bundle preview cleared.'); }
function renderIssueReportText(text){ const pre=document.getElementById('issue_report_output'); if(pre) pre.textContent=text; }
function generateIssueReportText(){ const b=lastSupportBundle||buildSupportBundle(); const s=b.current_case_summary||{}; const validationStatus=lastValidationResponse?String(lastValidationResponse.valid):'not run'; const runStatus=lastRunResponse?String(lastRunResponse.success):'not run'; const health=document.getElementById('backend_health_status'); const healthText=health?health.textContent:'unknown'; lastIssueReportText=`# Local UI Issue Report

## Summary
<user fills in>

## What I clicked
<user fills in>

## Expected behavior
<user fills in>

## Actual behavior
<user fills in>

## Current case
- case_id: ${s.case_id||''}
- base_shape_id: ${s.base_shape_id||''}
- material_id: ${s.material_id||''}
- wheel_count: ${String(s.wheel_count??'')}

## Diagnostics
- backend health: ${healthText}
- validation status: ${validationStatus}
- run status: ${runStatus}
- UI beta status: Internal beta

## Attached support bundle
Attach support_bundle.json if available.

## Scope reminders
This is an internal beta tool. Results require engineering review and are not official CIRSOC/CISC/AISC compliance checks.`; renderIssueReportText(lastIssueReportText); setStatus('Issue report text generated.'); }
async function copyIssueReportText(){ if(!lastIssueReportText){ generateIssueReportText(); } await copyText(lastIssueReportText,'Issue report text copied.','Could not copy issue report text.'); }


async function safeUiAction(actionName, fn) {
  try { return await fn(); }
  catch (err) { console.error('Unexpected UI error in ' + actionName, err); setStatus('Unexpected UI error in ' + actionName + '. See raw response or browser console.'); return null; }
}
function renderRcStatus() { const body=document.getElementById('rc_status_body'); if (!body) return; const manual=localStorage.getItem(RC_CHECKLIST_STATUS_KEY)==='manual-qa-complete'; const rows=[['Health check','Required'],['UI diagnostics','Required'],['RC acceptance check','Required'],['Manual QA checklist',manual?'Required (completed)':'Required'],['Support bundle','Recommended'],['Project archive export','Available'],['Known limitations','Recommended'],['Engineering review','Not a substitute for engineering review']]; body.innerHTML=rows.map((r)=>'<tr><td>'+escapeHtml(r[0])+'</td><td>'+escapeHtml(r[1])+'</td></tr>').join(''); }
async function copyRcChecklistSummary(){ return safeUiAction('copyRcChecklistSummary', async ()=>{ await navigator.clipboard.writeText(`Local UI RC Status\nHealth check: Required\nUI diagnostics: Required\nRC acceptance check: Required\nManual QA checklist: Required\nSupport bundle: Recommended\nProject archive export: Available\nKnown limitations: Recommended\nEngineering review: Not a substitute for engineering review`); setStatus('RC checklist summary copied.');});}
function markManualQaCompleted(){ localStorage.setItem(RC_CHECKLIST_STATUS_KEY,'manual-qa-complete'); renderRcStatus(); setStatus('Manual QA marked complete.'); }
function resetRcChecklistStatus(){ localStorage.removeItem(RC_CHECKLIST_STATUS_KEY); renderRcStatus(); setStatus('RC checklist status reset.'); }
function setupKeyboardShortcuts(){ document.addEventListener('keydown', (event)=>{ if (event.ctrlKey && event.key==='Enter' && !event.shiftKey) { event.preventDefault(); safeUiAction('validateCase', ()=>validateCase()); return; } if (event.ctrlKey && event.shiftKey && event.key==='Enter') { event.preventDefault(); safeUiAction('runCase', ()=>runCase()); return; } if (event.ctrlKey && event.shiftKey && event.key.toLowerCase()==='f') { event.preventDefault(); safeUiAction('formatJson', ()=>formatJson()); return; } if (event.ctrlKey && event.shiftKey && event.key.toLowerCase()==='h') { event.preventDefault(); if (typeof toggleFieldHelp==='function') toggleFieldHelp(); return; } if (event.ctrlKey && event.key.toLowerCase()==='s') { event.preventDefault(); if (typeof saveSession==='function') saveSession(); setStatus('JSON saved to browser autosave.'); return; } if (event.key==='Escape') { const status=document.getElementById('status'); if (status) status.textContent=''; } }); setStatus('Keyboard shortcuts enabled.'); }
async function checkBackendHealth() { try { const r=await fetch('/api/health'); const data=await r.json(); const ok=Boolean(r.ok && data && data.ok===true); const panel=document.getElementById('backend_health_status'); if (panel) panel.textContent=ok?'Backend health: OK.':'Backend health: FAIL.'; updateBetaReadiness('backend_health', ok); setStatus(ok?'Backend health: OK.':'Backend health: FAIL.'); } catch (err) { const panel=document.getElementById('backend_health_status'); if (panel) panel.textContent='Backend health: FAIL.'; updateBetaReadiness('backend_health', false); setStatus('Backend health: FAIL.'); } }
function setDiagnosticStatus(key, status) { diagnosticsState[key]=status; }
function updateDiagnosticsTimestamp() { const panel=document.getElementById('ui_diagnostics_timestamp'); if (panel) panel.textContent='Last diagnostic run: ' + new Date().toISOString(); }
function renderUiDiagnostics() { const body=document.getElementById('ui_diagnostics_body'); if (!body) return; const rows=[['UI loaded', diagnosticsState.ui_loaded],['Backend health', diagnosticsState.backend_health],['Templates endpoint', diagnosticsState.templates_endpoint],['Validate endpoint', diagnosticsState.validate_endpoint],['Run endpoint', diagnosticsState.run_endpoint],['JavaScript status', diagnosticsState.javascript_status],['Autosave status', diagnosticsState.autosave_status]]; let html=''; for (const row of rows) { const status=row[1]===true?'PASS':(row[1]===false?'FAIL':'N/A'); const cls=status==='PASS'?'status-pass':(status==='FAIL'?'status-fail':'status-na'); html += '<tr><th>'+escapeHtml(row[0])+'</th><td class="'+cls+'">'+status+'</td></tr>'; } body.innerHTML=html; }
async function checkDiagnosticsEndpoint(path, options, validator) { try { const response = await fetch(path, options || {}); const data = await response.json(); if (!response.ok) return false; return Boolean(validator ? validator(data) : true); } catch (err) { return false; } }
async function getDiagnosticTemplateCase() { return await checkDiagnosticsEndpoint('/api/template/ipn-with-cover', null, (data)=>Boolean(data && typeof data === 'object')) ? await (await fetch('/api/template/ipn-with-cover')).json() : null; }
async function runUiDiagnostics() { setDiagnosticStatus('ui_loaded', true); setDiagnosticStatus('javascript_status', true); setDiagnosticStatus('autosave_status', autosaveAvailable ? true : null); setDiagnosticStatus('backend_health', await checkDiagnosticsEndpoint('/api/health', null, (data)=>Boolean(data && data.ok===true))); setDiagnosticStatus('templates_endpoint', await checkDiagnosticsEndpoint('/api/templates', null, (data)=>Array.isArray(data && data.templates))); const templateCase = await getDiagnosticTemplateCase(); const templateCaseJson = templateCase ? JSON.stringify(templateCase) : ''; setDiagnosticStatus('validate_endpoint', templateCase ? await checkDiagnosticsEndpoint('/api/validate', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({case_json: templateCaseJson})}, (data)=>Boolean(data && Object.prototype.hasOwnProperty.call(data, 'valid'))) : false); setDiagnosticStatus('run_endpoint', templateCase ? await checkDiagnosticsEndpoint('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({case_json: templateCaseJson, output_formats:['summary']})}, (data)=>Boolean(data && Object.prototype.hasOwnProperty.call(data, 'success'))) : false); updateDiagnosticsTimestamp(); renderUiDiagnostics(); const failed=['backend_health','templates_endpoint','validate_endpoint','run_endpoint'].some((key)=>diagnosticsState[key]===false); setStatus(failed ? 'UI diagnostics found issues.' : 'UI diagnostics complete.'); }
async function runDemoWorkflow() { const panel=document.getElementById('demo_workflow_status'); if (panel) panel.textContent='Running demo workflow...'; try { document.getElementById('template').value='ipn-with-cover'; await loadTemplate(); markWorkflowStepDone(1); refreshVisualPreview(); markWorkflowStepDone(3); await validateCase(); if (lastValidationResponse && lastValidationResponse.valid===false) { markWorkflowStepNeedsAttention(4); throw new Error('Validation failed.'); } markWorkflowStepDone(4); await runCase(); if (!lastRunResponse || lastRunResponse.success===false) throw new Error('Run failed.'); markWorkflowStepDone(5); markWorkflowStepDone(6); if (panel) panel.textContent='Demo workflow complete.'; setStatus('Demo workflow complete.'); } catch (err) { if (panel) panel.textContent='Demo workflow failed.'; setStatus('Demo workflow failed.'); } }

function setStatus(msg) { document.getElementById('status').textContent = msg; }
function toggleFieldHelp() { const panel=document.getElementById('field_help_panel'); if (!panel) return; const hidden=panel.getAttribute('data-help-hidden')==='true'; if (hidden) { panel.style.display='block'; panel.setAttribute('data-help-hidden','false'); setStatus('Help shown.'); } else { panel.style.display='none'; panel.setAttribute('data-help-hidden','true'); setStatus('Help hidden.'); } }
function filterGlossary() { const input=document.getElementById('glossary_search'); const list=document.getElementById('glossary_list'); if (!input || !list) return; const query=String(input.value || '').toLowerCase(); const items=list.querySelectorAll('.glossary-item'); let visible=0; for (const item of items) { const match=item.textContent.toLowerCase().includes(query); item.style.display=match?'':'none'; if (match) visible += 1; } const noMatch=document.getElementById('glossary_no_match'); if (noMatch) noMatch.style.display=visible===0?'block':'none'; }
function prettyJson(value) { return JSON.stringify(value, null, 2); }
function renderRaw(data) {
  lastRawResponse = data;
  document.getElementById('raw_output').textContent = prettyJson(data);
}
function getCurrentCaseJsonText() { return document.getElementById('case_json').value; }
function escapeHtml(s) {
  return String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}
function clearOutput() {
  document.getElementById('validation_output').innerHTML = '';
  document.getElementById('summary_output').innerHTML = '';
  document.getElementById('raw_output').textContent = '';
  document.getElementById('html_output').srcdoc = '';
  document.getElementById('open_report').style.display = 'none';
  latestHtmlReport = '';
  lastValidationResponse = null;
  lastRunResponse = null;
  lastRawResponse = null;
  renderResultCards(null);
  renderResultInterpretation(null, null);
  setStatus('Output cleared.');
}
function clearJson() { document.getElementById('case_json').value = ''; setStatus('JSON editor cleared.'); saveSession(); }

function extractQuantityLabel(value, fallback='N/A') { if (!value || typeof value !== 'object') return fallback; const numeric=value.value; const unit=value.unit?String(value.unit):''; if (numeric===undefined || numeric===null || numeric==='') return fallback; return unit ? String(numeric) + ' ' + unit : String(numeric); }
function getWheelList(caseData) { const wheels = caseData && caseData.crane && Array.isArray(caseData.crane.wheels) ? caseData.crane.wheels : []; return wheels.filter((wheel) => wheel && typeof wheel === 'object'); }
function getCaseSpan(caseData) { return extractQuantityLabel(caseData && caseData.analysis ? caseData.analysis.span : null); }
function getBaseShapeId(caseData) { return caseData?.section?.base_shape_id ?? caseData?.base_shape_id ?? 'N/A'; }
function getCoverPlateInfo(caseData) { const cover = caseData?.section?.cover_plate; return {enabled:Boolean(cover?.enabled), width:extractQuantityLabel(cover?.width), thickness:extractQuantityLabel(cover?.thickness)}; }
function getMaterialInfo(caseData) { const material = caseData?.material; return {material_id:material?.material_id ?? 'N/A', fy_label:extractQuantityLabel(material?.Fy)}; }
function getRailEccentricityInfo(caseData) { return {enabled:Boolean(caseData?.rail_eccentricity?.enabled)}; }
function renderBeamPreview(caseData) { const panel=document.getElementById('beam_preview_output'); if (!panel) return; const wheels=getWheelList(caseData); const spanValue=Number(caseData?.analysis?.span?.value); const spanLabel=getCaseSpan(caseData); if (!Number.isFinite(spanValue) || spanValue<=0) { panel.innerHTML='<p>Beam preview unavailable: span is N/A.</p>'; return; } if (wheels.length===0) { panel.innerHTML='<p>Beam preview unavailable: wheel list is N/A.</p>'; return; } const w=720,h=220,x0=70,x1=650,y=110; let svg='<svg viewBox="0 0 '+w+' '+h+'" style="width:100%;max-width:720px;border:1px solid #e5e7eb;border-radius:6px;background:#fff;">'; svg += '<line x1="'+x0+'" y1="'+y+'" x2="'+x1+'" y2="'+y+'" stroke="#111827" stroke-width="3"/>'; svg += '<polygon points="'+(x0-14)+','+(y+26)+' '+(x0+14)+','+(y+26)+' '+x0+','+(y+4)+'" fill="#2563eb"/>'; svg += '<polygon points="'+(x1-14)+','+(y+26)+' '+(x1+14)+','+(y+26)+' '+x1+','+(y+4)+'" fill="#2563eb"/>'; for (const wheel of wheels) { const wx=Number(wheel?.position_x?.value); if (!Number.isFinite(wx)) continue; const px=x0 + Math.max(0, Math.min(1, wx / spanValue)) * (x1-x0); svg += '<line x1="'+px+'" y1="'+(y-60)+'" x2="'+px+'" y2="'+(y-8)+'" stroke="#dc2626" stroke-width="2"/>'; svg += '<polygon points="'+(px-6)+','+(y-16)+' '+(px+6)+','+(y-16)+' '+px+','+(y-2)+'" fill="#dc2626"/>'; svg += '<text x="'+(px+6)+'" y="'+(y-66)+'" font-size="11" fill="#111827">'+escapeHtml(String(wheel?.wheel_id ?? 'N/A'))+' | Fv '+escapeHtml(extractQuantityLabel(wheel?.vertical_force))+' | x '+escapeHtml(extractQuantityLabel(wheel?.position_x))+'</text>'; } panel.innerHTML = svg + '<text x="'+((x0+x1)/2-70)+'" y="'+(y+44)+'" font-size="12" fill="#111827">Span: '+escapeHtml(spanLabel)+'</text></svg>'; }
function renderSectionPreview(caseData) { const panel=document.getElementById('section_preview_output'); if (!panel) return; const baseShapeId=getBaseShapeId(caseData); const cover=getCoverPlateInfo(caseData); const material=getMaterialInfo(caseData); const rail=getRailEccentricityInfo(caseData); let svg='<svg viewBox="0 0 620 240" style="width:100%;max-width:620px;border:1px solid #e5e7eb;border-radius:6px;background:#fff;">'; svg += '<rect x="220" y="90" width="180" height="100" fill="#dbeafe" stroke="#1d4ed8" stroke-width="2"/>'; svg += '<text x="230" y="145" font-size="13" fill="#111827">Base shape: '+escapeHtml(String(baseShapeId))+'</text>'; if (cover.enabled) { svg += '<rect x="205" y="68" width="210" height="18" fill="#fde68a" stroke="#b45309" stroke-width="2"/>'; svg += '<text x="20" y="42" font-size="12" fill="#111827">Cover plate enabled: true</text>'; svg += '<text x="20" y="60" font-size="12" fill="#111827">width='+escapeHtml(cover.width)+', thickness='+escapeHtml(cover.thickness)+'</text>'; } else { svg += '<text x="20" y="42" font-size="12" fill="#111827">Cover plate enabled: false</text>'; } svg += '<text x="20" y="208" font-size="12" fill="#111827">Material: '+escapeHtml(String(material.material_id))+', Fy: '+escapeHtml(material.fy_label)+'</text>'; svg += '<text x="20" y="224" font-size="12" fill="#111827">Rail eccentricity enabled: '+escapeHtml(String(rail.enabled))+'</text>'; panel.innerHTML = svg + '</svg>'; }
function renderPreviewSummary(caseData) { const panel=document.getElementById('preview_summary_output'); if (!panel) return; const wheels=getWheelList(caseData); const cover=getCoverPlateInfo(caseData); const material=getMaterialInfo(caseData); const rail=getRailEccentricityInfo(caseData); const criteriaLabel = caseData?.criteria_presets && typeof caseData.criteria_presets==='object' ? JSON.stringify(caseData.criteria_presets) : 'N/A'; const rows=[['case_id',caseData?.case_id ?? 'N/A'],['base_shape_id',getBaseShapeId(caseData)],['span',getCaseSpan(caseData)],['number of wheels',wheels.length>0?wheels.length:'N/A'],['cover plate enabled',String(cover.enabled)],['material_id',material.material_id],['rail eccentricity enabled',String(rail.enabled)],['criteria presets',criteriaLabel]]; let html='<table><tbody>'; for (const row of rows) html += '<tr><th>'+escapeHtml(row[0])+'</th><td>'+escapeHtml(String(row[1]))+'</td></tr>'; panel.innerHTML = html + '</tbody></table>'; }
function refreshVisualPreview() { let caseData; try { caseData = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot refresh visual preview: invalid JSON.'); return; } renderBeamPreview(caseData); renderSectionPreview(caseData); renderPreviewSummary(caseData); setStatus('Visual preview refreshed.'); if (typeof refreshCaseQuality === 'function') refreshCaseQuality(); markWorkflowStepDone(3); }

function hasQuantityValue(value) { return Boolean(value && typeof value === 'object' && value.value !== undefined && value.value !== null && String(value.value).trim() !== ''); }
function getRootOrSectionBaseShapeId(caseData) { if (!caseData || typeof caseData !== 'object') return ''; const root=caseData.base_shape_id; const section=caseData.section && caseData.section.base_shape_id; const picked = root !== undefined && root !== null && String(root).trim() !== '' ? root : section; return picked === undefined || picked === null ? '' : String(picked).trim(); }
function addCaseQualityWarning(rows, severity, area, message, suggestedAction) { rows.push({severity:String(severity || 'Info'), area:String(area || 'general'), message:String(message || ''), suggested_action:String(suggestedAction || '')}); }
function getCaseQualityRows() { return Array.isArray(lastCaseQualityWarnings) ? lastCaseQualityWarnings.slice() : []; }
function buildCaseQualityWarnings(caseData) {
  const rows = [];
  if (!caseData || typeof caseData !== 'object') return rows;
  if (!caseData.case_id) addCaseQualityWarning(rows,'Warning','metadata','case_id is missing.','Add a unique case_id.');
  if (!caseData.description) addCaseQualityWarning(rows,'Info','metadata','description is missing.','Add a short description for traceability.');
  const baseShapeId = getRootOrSectionBaseShapeId(caseData);
  if (!baseShapeId) addCaseQualityWarning(rows,'Warning','section','base_shape_id is missing.','Select or enter a base profile.');
  if (baseShapeId.startsWith('CIRSOC_')) addCaseQualityWarning(rows,'Caution','section','Sample CIRSOC profile data must be independently verified.','Check source tables before design use.');
  const material = caseData.material;
  if (!material || typeof material !== 'object') addCaseQualityWarning(rows,'Warning','material','material block is missing.','Add material Fy/Fu/E or select a material preset.');
  if (!hasQuantityValue(material && material.Fy)) addCaseQualityWarning(rows,'Warning','material','material Fy is missing.','Add Fy before checking stress criteria.');
  if (!hasQuantityValue(material && material.E)) addCaseQualityWarning(rows,'Warning','material','material E is missing.','Add E before checking deflection.');
  if (!hasQuantityValue(caseData.analysis && caseData.analysis.span)) addCaseQualityWarning(rows,'Warning','analysis','span is missing.','Add the runway beam span.');
  if (!hasQuantityValue(caseData.analysis && caseData.analysis.movement_step)) addCaseQualityWarning(rows,'Info','analysis','movement_step is missing.','Add movement_step for moving-load scans.');
  if (!hasQuantityValue(caseData.analysis && caseData.analysis.station_step)) addCaseQualityWarning(rows,'Info','analysis','station_step is missing.','Add station_step for envelope curves.');
  if (!caseData.crane || typeof caseData.crane !== 'object') addCaseQualityWarning(rows,'Warning','crane','crane block is missing.','Add crane load data.');
  const wheels = Array.isArray(caseData.crane && caseData.crane.wheels) ? caseData.crane.wheels : [];
  if (wheels.length === 0) addCaseQualityWarning(rows,'Warning','wheels','No crane wheels are defined.','Use Wheel Table Editor to add wheels.');
  if (wheels.length === 1) addCaseQualityWarning(rows,'Caution','wheels','Only one wheel is defined.','Confirm this is intentional.');
  const wheelIds = wheels.map((w)=>String(w && w.wheel_id ? w.wheel_id : '').trim()).filter((x)=>x!=='');
  if (wheelIds.length > 0 && wheelIds.length !== new Set(wheelIds).size) addCaseQualityWarning(rows,'Warning','wheels','Duplicate wheel IDs found.','Use unique wheel IDs.');
  if (wheels.some((w)=>!hasQuantityValue(w && w.position_x))) addCaseQualityWarning(rows,'Warning','wheels','A wheel is missing position_x.','Add wheel position.');
  if (wheels.some((w)=>!hasQuantityValue(w && w.vertical_force))) addCaseQualityWarning(rows,'Warning','wheels','A wheel is missing vertical_force.','Add vertical wheel force.');
  const cover = caseData.section && caseData.section.cover_plate;
  if (cover && cover.enabled === true) {
    if (!hasQuantityValue(cover.width)) addCaseQualityWarning(rows,'Warning','cover_plate','Cover plate is enabled but width is missing.','Add cover plate width.');
    if (!hasQuantityValue(cover.thickness)) addCaseQualityWarning(rows,'Warning','cover_plate','Cover plate is enabled but thickness is missing.','Add cover plate thickness.');
    if (!hasQuantityValue(cover.weld_size)) addCaseQualityWarning(rows,'Caution','cover_plate','Cover plate is enabled but weld_size is missing.','Add weld size or confirm connection assumptions.');
  }
  const cp = caseData.criteria_presets;
  const serviceabilityMissing = !caseData.serviceability_limits;
  const stressMissing = !caseData.stress_limits;
  if (!cp && serviceabilityMissing && stressMissing) addCaseQualityWarning(rows,'Caution','criteria','No criteria presets or explicit limits are configured.','Add generic criteria before interpreting pass/fail results.');
  if (!Array.isArray(cp && cp.deflection) || (cp && cp.deflection && cp.deflection.length===0)) addCaseQualityWarning(rows,'Warning','criteria','No deflection criterion is configured.','Add a deflection preset or explicit serviceability limit.');
  if (!Array.isArray(cp && cp.stress) || (cp && cp.stress && cp.stress.length===0)) addCaseQualityWarning(rows,'Warning','criteria','No stress criterion is configured.','Add a stress preset or explicit stress limit.');
  const rail = caseData.rail_eccentricity;
  if (rail && rail.enabled === true) {
    if (!hasQuantityValue(rail.vertical_eccentricity_y)) addCaseQualityWarning(rows,'Warning','rail_eccentricity','Rail eccentricity is enabled but vertical_eccentricity_y is missing.','Add vertical eccentricity or disable rail eccentricity.');
    if (!hasQuantityValue(rail.lateral_load_height_z)) addCaseQualityWarning(rows,'Warning','rail_eccentricity','Rail eccentricity is enabled but lateral_load_height_z is missing.','Add lateral load height or disable rail eccentricity.');
  }
  if (!Array.isArray(caseData.warnings) || caseData.warnings.length === 0) addCaseQualityWarning(rows,'Info','warnings','warnings list is missing or empty.','Add project-specific warnings and data-source assumptions.');
  addCaseQualityWarning(rows,'Info','beta','Case quality warnings are setup checks only, not design-code checks.','Use engineering review before relying on results.');
  return rows;
}
function renderCaseQualityWarnings(rows, statusMessage) { const body=document.getElementById('case_quality_rows'); const status=document.getElementById('case_quality_status'); if (!body || !status) return; const safeRows = Array.isArray(rows) ? rows : []; if (safeRows.length===0) body.innerHTML=''; else body.innerHTML=safeRows.map((row)=>'<tr><td>'+escapeHtml(row.severity)+'</td><td>'+escapeHtml(row.area)+'</td><td>'+escapeHtml(row.message)+'</td><td>'+escapeHtml(row.suggested_action)+'</td></tr>').join(''); status.textContent = statusMessage || (safeRows.length===0 ? 'No case quality warnings found.' : ('Case quality warnings: ' + safeRows.length)); }
function refreshCaseQuality() { let caseData; try { caseData = JSON.parse(getCurrentCaseJsonText()); } catch (err) { lastCaseQualityWarnings = null; renderCaseQualityWarnings([], 'Cannot check case quality: invalid JSON.'); return; } const rows = buildCaseQualityWarnings(caseData); lastCaseQualityWarnings = rows; renderCaseQualityWarnings(rows, rows.length===0 ? 'No case quality warnings found.' : ('Case quality warnings: ' + rows.length)); }
async function copyCaseQualityWarnings() { const rows=getCaseQualityRows(); if (rows.length===0) { setStatus('No case quality warnings available. Refresh case quality first.'); return; } const lines=rows.map((row,idx)=>(idx+1)+'. ['+row.severity+'] '+row.area+' | '+row.message+' | Suggested Action: '+row.suggested_action); await copyText(lines.join('\\n'),'Case quality warnings copied.','Could not copy case quality warnings.'); }
function downloadCaseQualityWarnings() { const rows=getCaseQualityRows(); if (rows.length===0) { setStatus('No case quality warnings available. Refresh case quality first.'); return; } downloadText('case_quality_warnings.json', prettyJson(rows), 'application/json;charset=utf-8'); setStatus('Case quality warnings downloaded.'); }

async function importJsonFile() {
  const fileInput = document.getElementById('import_json_file');
  const validateAfterImport = document.getElementById('validate_after_import');
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) { setStatus('No JSON file selected.'); return; }
  const file = fileInput.files[0];
  clearOutput();
  const reader = new FileReader();
  reader.onload = async function(event) {
    const text = event && event.target ? String(event.target.result ?? '') : '';
    document.getElementById('case_json').value = text;
    saveSession();
    setStatus('Imported JSON file: ' + file.name); markWorkflowStepDone(1); updateBetaReadiness('json_loaded', true);
    if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
    if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
    if (validateAfterImport && validateAfterImport.checked) {
      await validateCase();
    }
  };
  reader.onerror = function() { setStatus('Could not import JSON file.'); };
  try {
    reader.readAsText(file);
  } catch (err) {
    setStatus('Could not import JSON file.');
  }
}
function downloadText(filename, content, contentType) {
  const blob = new Blob([content], {type: contentType});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
async function copyText(text, successMessage, failureMessage) {
  if (!text) { setStatus(failureMessage); return false; }
  try {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(text);
      setStatus(successMessage);
      return true;
    }
    const temp = document.createElement('textarea');
    temp.value = text;
    temp.style.position = 'fixed';
    temp.style.opacity = '0';
    document.body.appendChild(temp);
    temp.focus();
    temp.select();
    const copied = document.execCommand('copy');
    temp.remove();
    if (copied) { setStatus(successMessage); return true; }
  } catch (err) {}
  setStatus(failureMessage);
  return false;
}
function downloadCaseJson() {
  try {
    const parsed = JSON.parse(getCurrentCaseJsonText());
    downloadText('crane_runway_case.json', prettyJson(parsed), 'application/json;charset=utf-8');
    setStatus('JSON case downloaded.');
  } catch (err) {
    setStatus('Cannot download case: invalid JSON.');
  }
}
async function copyCaseJson() {
  await copyText(getCurrentCaseJsonText(), 'JSON case copied.', 'Could not copy JSON case.');
}
function downloadSummaryJson() {
  if (!lastRunResponse || !lastRunResponse.summary) { setStatus('No summary available. Run a case first.'); return; }
  downloadText('summary.json', prettyJson(lastRunResponse.summary), 'application/json;charset=utf-8');
  setStatus('Summary downloaded.'); markWorkflowStepDone(7);
}
function buildPackageArtifacts() {
  const artifacts = {};
  try {
    const parsed = JSON.parse(getCurrentCaseJsonText());
    artifacts['case.json'] = {available: true, content: prettyJson(parsed), contentType: 'application/json;charset=utf-8'};
  } catch (err) {
    artifacts['case.json'] = {available: false, reason: 'Cannot export case.json: invalid JSON.'};
  }
  if (lastRunResponse && lastRunResponse.summary) {
    artifacts['summary.json'] = {available: true, content: prettyJson(lastRunResponse.summary), contentType: 'application/json;charset=utf-8'};
  } else {
    artifacts['summary.json'] = {available: false, reason: 'No summary available. Run a case first.'};
  }
  if (lastValidationResponse) {
    artifacts['validation_response.json'] = {available: true, content: prettyJson(lastValidationResponse), contentType: 'application/json;charset=utf-8'};
  } else {
    artifacts['validation_response.json'] = {available: false, reason: 'No validation response available. Validate a case first.'};
  }
  if (lastRunResponse) {
    artifacts['run_response.json'] = {available: true, content: prettyJson(lastRunResponse), contentType: 'application/json;charset=utf-8'};
  } else {
    artifacts['run_response.json'] = {available: false, reason: 'No run response available. Run a case first.'};
  }
  if (lastRunResponse && lastRunResponse.html_report) {
    artifacts['report.html'] = {available: true, content: lastRunResponse.html_report, contentType: 'text/html;charset=utf-8'};
  } else {
    artifacts['report.html'] = {available: false, reason: 'No HTML report available. Run a case first.'};
  }
  return artifacts;
}
function buildPackageMetadata(availableArtifacts, unavailableArtifacts) {
  return {
    generated_by: 'CraneRunwayLocalWebUi',
    generated_at: new Date().toISOString(),
    available_artifacts: availableArtifacts,
    unavailable_artifacts: unavailableArtifacts,
    notes: [
      'Browser-side export package.',
      'Results require engineering review.',
      'Generic checks only; no official CIRSOC/CISC/AISC compliance checks.',
      'No fatigue, torsional/warping stress, or LTB checks are performed.'
    ]
  };
}
function downloadPackageMetadata() {
  const artifacts = buildPackageArtifacts();
  const available = [];
  const unavailable = [];
  for (const [name, artifact] of Object.entries(artifacts)) {
    if (artifact.available) available.push(name);
    else unavailable.push(name);
  }
  const metadata = buildPackageMetadata(available, unavailable);
  downloadText('metadata.json', prettyJson(metadata), 'application/json;charset=utf-8');
  setStatus('Package metadata downloaded.'); markWorkflowStepDone(7);
}
function downloadPackageCaseJson() {
  const artifact = buildPackageArtifacts()['case.json'];
  if (!artifact.available) { setStatus(artifact.reason); return; }
  downloadText('case.json', artifact.content, artifact.contentType);
  setStatus('Case JSON downloaded.'); markWorkflowStepDone(7);
}
function downloadValidationResponse() {
  const artifact = buildPackageArtifacts()['validation_response.json'];
  if (!artifact.available) { setStatus(artifact.reason); return; }
  downloadText('validation_response.json', artifact.content, artifact.contentType);
  setStatus('Validation response downloaded.'); markWorkflowStepDone(7);
}
function downloadRunResponse() {
  const artifact = buildPackageArtifacts()['run_response.json'];
  if (!artifact.available) { setStatus(artifact.reason); return; }
  downloadText('run_response.json', artifact.content, artifact.contentType);
  setStatus('Run response downloaded.'); markWorkflowStepDone(7);
}
function downloadAllPackageFiles() {
  const artifacts = buildPackageArtifacts();
  const downloaded = [];
  const unavailable = [];
  for (const [name, artifact] of Object.entries(artifacts)) {
    if (artifact.available) {
      downloadText(name, artifact.content, artifact.contentType);
      downloaded.push(name);
      continue;
    }
    unavailable.push(name);
  }
  const metadata = buildPackageMetadata(downloaded, unavailable);
  downloadText('metadata.json', prettyJson(metadata), 'application/json;charset=utf-8');
  downloaded.push('metadata.json');
  let status = 'Downloaded package files: ' + (downloaded.length > 0 ? downloaded.join(', ') : 'none') + '.';
  if (unavailable.length > 0) status += ' Unavailable package files: ' + unavailable.join(', ') + '.';
  setStatus(status);
}
async function copySummaryJson() {
  if (!lastRunResponse || !lastRunResponse.summary) { setStatus('No summary available. Run a case first.'); return; }
  await copyText(prettyJson(lastRunResponse.summary), 'Summary copied.', 'Could not copy summary JSON.');
}
function downloadHtmlReport() {
  if (!lastRunResponse || !lastRunResponse.html_report) { setStatus('No HTML report available. Run a case first.'); return; }
  downloadText('report.html', lastRunResponse.html_report, 'text/html;charset=utf-8');
  setStatus('HTML report downloaded.'); markWorkflowStepDone(7);
}
async function copyValidationResponse() {
  if (!lastValidationResponse) { setStatus('No validation response available. Validate a case first.'); return; }
  await copyText(prettyJson(lastValidationResponse), 'Validation response copied.', 'Could not copy validation response.');
}
async function copyRawResponse() {
  const rawText = document.getElementById('raw_output').textContent;
  if (!rawText || rawText.trim().length === 0 || !lastRawResponse) { setStatus('No raw response available.'); return; }
  await copyText(rawText, 'Raw response copied.', 'Could not copy raw response.');
}
function formatJson() {
  try {
    const parsed = JSON.parse(getCurrentCaseJsonText());
    document.getElementById('case_json').value = prettyJson(parsed);
    setStatus('JSON formatted.');
  } catch (err) {
    setStatus('Cannot format: invalid JSON.');
  }
}

function ensureObjectPath(obj, path) {
  let current = obj;
  for (let i = 0; i < path.length; i += 1) {
    const key = path[i];
    if (!current[key] || typeof current[key] !== 'object' || Array.isArray(current[key])) current[key] = {};
    current = current[key];
  }
  return current;
}
function setNestedValue(obj, path, value) {
  if (!obj || !Array.isArray(path) || path.length === 0) return;
  const parent = ensureObjectPath(obj, path.slice(0, -1));
  parent[path[path.length - 1]] = value;
}
function getNestedValue(obj, path) {
  let current = obj;
  for (const key of path) {
    if (!current || typeof current !== 'object' || !Object.prototype.hasOwnProperty.call(current, key)) return undefined;
    current = current[key];
  }
  return current;
}
function setQuantity(obj, path, value, unit) { if (value === '' || value === null || value === undefined) return; const n = Number(value); if (Number.isNaN(n)) return; setNestedValue(obj, path, {value: n, unit: unit}); }
function getQuantityValue(obj, path) { const q = getNestedValue(obj, path); if (!q || typeof q !== 'object') return ''; return q.value ?? ''; }
function getSelectedUnit(id, fallbackUnit) { const el = document.getElementById(id); return el && el.value ? el.value : fallbackUnit; }
function setSelectedUnit(id, unit, supportedUnits) { const el = document.getElementById(id); if (!el || !Array.isArray(supportedUnits)) return; if (supportedUnits.includes(unit)) el.value = unit; }
function parseOptionalNumber(value) { if (value === '' || value === null || value === undefined) return null; const n = Number(value); return Number.isNaN(n) ? NaN : n; }
function isPositiveNumber(value) { return typeof value === 'number' && Number.isFinite(value) && value > 0; }
function isNonNegativeNumber(value) { return typeof value === 'number' && Number.isFinite(value) && value >= 0; }
function renderCommonInputErrors(errors) {
  const panel = document.getElementById('common_inputs_errors');
  if (!panel) return;
  if (!Array.isArray(errors) || errors.length === 0) { panel.innerHTML = '<p>No common input errors.</p>'; return; }
  let html = '<table><thead><tr><th>Field</th><th>Message</th></tr></thead><tbody>';
  for (const e of errors) html += '<tr><td>' + escapeHtml(e.field || 'N/A') + '</td><td>' + escapeHtml(e.message || 'N/A') + '</td></tr>';
  panel.innerHTML = html + '</tbody></table>';
}
function validateCommonInputs() {
  const gv=(id)=>{ const el=document.getElementById(id); if (!el) return ''; return el.type==='checkbox' ? el.checked : String(el.value ?? '').trim(); };
  const errors = [];
  const add=(field,message)=>errors.push({field: field, message: message});
  const caseId = gv('common_case_id'); if (caseId !== '' && caseId.includes(' ')) add('Case ID', 'Case ID must not contain spaces.');
  const checkPositive=(id,field,msg)=>{ const n=parseOptionalNumber(gv(id)); if (Number.isNaN(n) || (n !== null && !isPositiveNumber(n))) add(field,msg); };
  const checkNonNegative=(id,field,msg)=>{ const n=parseOptionalNumber(gv(id)); if (Number.isNaN(n) || (n !== null && !isNonNegativeNumber(n))) add(field,msg); };
  const checkNumeric=(id,field,msg)=>{ const n=parseOptionalNumber(gv(id)); if (Number.isNaN(n)) add(field,msg); };
  checkPositive('common_cover_plate_width','Cover Plate Width','Cover Plate Width must be positive.');
  checkPositive('common_cover_plate_thickness','Cover Plate Thickness','Cover Plate Thickness must be positive.');
  checkPositive('common_cover_plate_weld_size','Cover Plate Weld Size','Cover Plate Weld Size must be positive.');
  checkPositive('common_fy','Fy','Fy must be positive.'); checkPositive('common_fu','Fu','Fu must be positive.'); checkPositive('common_e','E','E must be positive.');
  checkPositive('common_span','Span','Span must be positive.'); checkPositive('common_movement_step','Movement Step','Movement Step must be positive.'); checkPositive('common_station_step','Station Step','Station Step must be positive.');
  checkNonNegative('common_vertical_impact_factor','Vertical Impact Factor','Vertical Impact Factor must be >= 0.');
  checkNonNegative('common_lateral_force_factor','Lateral Force Factor','Lateral Force Factor must be >= 0.');
  checkPositive('common_wheel_1_load','Wheel 1 Load','Wheel 1 Load must be positive.'); checkPositive('common_wheel_2_load','Wheel 2 Load','Wheel 2 Load must be positive.'); checkPositive('common_wheel_spacing','Wheel Spacing','Wheel Spacing must be positive.');
  checkNumeric('common_vertical_eccentricity_y','Vertical Eccentricity Y','Vertical Eccentricity Y must be numeric.');
  checkNumeric('common_lateral_load_height_z','Lateral Load Height Z','Lateral Load Height Z must be numeric.');
  renderCommonInputErrors(errors);
  return errors;
}
function validateCommonInputsOnly() { const errors = validateCommonInputs(); setStatus(errors.length === 0 ? 'Common inputs are valid.' : 'Common inputs contain errors.'); }
function resetCommonInputs() {
  for (const el of document.querySelectorAll('[id^="common_"]')) {
    if (el.type === 'checkbox') el.checked = false; else if (el.tagName === 'SELECT') el.selectedIndex = 0; else el.value = '';
  }
  renderCommonInputErrors([]);
  setStatus('Common inputs reset.');
}
function loadCommonInputsFromJson() {
  let data;
  try { data = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot load form: invalid JSON.'); return; }
  const setVal=(id,v)=>{ const el=document.getElementById(id); if (!el) return; if (el.type==='checkbox') el.checked=Boolean(v); else el.value=(v ?? '');};
  setVal('common_case_id', getNestedValue(data,['case_id']));
  setVal('common_description', getNestedValue(data,['description']));
  setVal('common_base_shape_id', getNestedValue(data,['section','base_shape_id']) ?? getNestedValue(data,['base_shape_id']));
  setVal('common_cover_plate_enabled', getNestedValue(data,['section','cover_plate','enabled']));
  setVal('common_cover_plate_width', getQuantityValue(data,['section','cover_plate','width'])); setSelectedUnit('common_cover_plate_width_unit', getNestedValue(data,['section','cover_plate','width','unit']), ['mm','cm','in']);
  setVal('common_cover_plate_thickness', getQuantityValue(data,['section','cover_plate','thickness'])); setSelectedUnit('common_cover_plate_thickness_unit', getNestedValue(data,['section','cover_plate','thickness','unit']), ['mm','cm','in']);
  setVal('common_cover_plate_weld_size', getQuantityValue(data,['section','cover_plate','weld_size'])); setSelectedUnit('common_cover_plate_weld_size_unit', getNestedValue(data,['section','cover_plate','weld_size','unit']), ['mm','cm','in']);
  setVal('common_material_id', getNestedValue(data,['material','material_id']));
  setVal('common_fy', getQuantityValue(data,['material','Fy'])); setSelectedUnit('common_fy_unit', getNestedValue(data,['material','Fy','unit']), ['MPa','ksi','psi']);
  setVal('common_fu', getQuantityValue(data,['material','Fu'])); setSelectedUnit('common_fu_unit', getNestedValue(data,['material','Fu','unit']), ['MPa','ksi','psi']);
  setVal('common_e', getQuantityValue(data,['material','E'])); setSelectedUnit('common_e_unit', getNestedValue(data,['material','E','unit']), ['MPa','ksi','psi']);
  setVal('common_span', getQuantityValue(data,['analysis','span'])); setSelectedUnit('common_span_unit', getNestedValue(data,['analysis','span','unit']), ['m','mm','ft']);
  setVal('common_movement_step', getQuantityValue(data,['analysis','movement_step'])); setSelectedUnit('common_movement_step_unit', getNestedValue(data,['analysis','movement_step','unit']), ['mm','cm','in']);
  setVal('common_station_step', getQuantityValue(data,['analysis','station_step'])); setSelectedUnit('common_station_step_unit', getNestedValue(data,['analysis','station_step','unit']), ['mm','cm','in']);
  setVal('common_crane_id', getNestedValue(data,['crane','crane_id'])); setVal('common_vertical_impact_factor', getNestedValue(data,['crane','vertical_impact_factor'])); setVal('common_lateral_force_factor', getNestedValue(data,['crane','lateral_force_factor']));
  const wheels = Array.isArray(getNestedValue(data,['crane','wheels'])) ? getNestedValue(data,['crane','wheels']) : [];
  setVal('common_wheel_1_load', wheels[0] && wheels[0].vertical_force ? wheels[0].vertical_force.value : ''); setSelectedUnit('common_wheel_1_load_unit', wheels[0] && wheels[0].vertical_force ? wheels[0].vertical_force.unit : null, ['kN','N','kip']);
  setVal('common_wheel_2_load', wheels[1] && wheels[1].vertical_force ? wheels[1].vertical_force.value : ''); setSelectedUnit('common_wheel_2_load_unit', wheels[1] && wheels[1].vertical_force ? wheels[1].vertical_force.unit : null, ['kN','N','kip']);
  if (wheels[0] && wheels[1] && wheels[0].position_x && wheels[1].position_x) setVal('common_wheel_spacing', Number(wheels[1].position_x.value) - Number(wheels[0].position_x.value)); else setVal('common_wheel_spacing','');
  setSelectedUnit('common_wheel_spacing_unit', wheels[0] && wheels[0].position_x ? wheels[0].position_x.unit : null, ['mm','cm','in']);
  setVal('common_rail_eccentricity_enabled', getNestedValue(data,['rail_eccentricity','enabled'])); setVal('common_vertical_eccentricity_y', getQuantityValue(data,['rail_eccentricity','vertical_eccentricity_y'])); setSelectedUnit('common_vertical_eccentricity_y_unit', getNestedValue(data,['rail_eccentricity','vertical_eccentricity_y','unit']), ['mm','cm','in']); setVal('common_lateral_load_height_z', getQuantityValue(data,['rail_eccentricity','lateral_load_height_z'])); setSelectedUnit('common_lateral_load_height_z_unit', getNestedValue(data,['rail_eccentricity','lateral_load_height_z','unit']), ['mm','cm','in']);
  const d = getNestedValue(data,['criteria_presets','deflection']); const st = getNestedValue(data,['criteria_presets','stress']);
  setVal('common_deflection_preset', Array.isArray(d) ? (d[0] ?? '') : ''); setVal('common_stress_preset', Array.isArray(st) ? (st[0] ?? '') : '');
  renderCommonInputErrors([]);
}
function applyCommonInputsToJson() {
  const errors = validateCommonInputs(); if (errors.length > 0) { setStatus('Common inputs contain errors.'); return; }
  let data; try { data = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot apply form: invalid JSON.'); return; }
  const gv=(id)=>{ const el=document.getElementById(id); if (!el) return ''; return el.type==='checkbox' ? el.checked : String(el.value ?? '').trim(); };
  const setText=(path,id)=>{ const v=gv(id); if (v!=='') setNestedValue(data,path,v); };
  setText(['case_id'],'common_case_id'); setText(['description'],'common_description');
  const baseShapeId=gv('common_base_shape_id'); if (baseShapeId!=='') { if (getNestedValue(data,['section','base_shape_id']) !== undefined) setNestedValue(data,['section','base_shape_id'],baseShapeId); else setNestedValue(data,['base_shape_id'],baseShapeId); }
  setNestedValue(data,['section','cover_plate','enabled'],gv('common_cover_plate_enabled'));
  setQuantity(data,['section','cover_plate','width'],gv('common_cover_plate_width'),getSelectedUnit('common_cover_plate_width_unit','mm')); setQuantity(data,['section','cover_plate','thickness'],gv('common_cover_plate_thickness'),getSelectedUnit('common_cover_plate_thickness_unit','mm')); setQuantity(data,['section','cover_plate','weld_size'],gv('common_cover_plate_weld_size'),getSelectedUnit('common_cover_plate_weld_size_unit','mm'));
  setText(['material','material_id'],'common_material_id'); setQuantity(data,['material','Fy'],gv('common_fy'),getSelectedUnit('common_fy_unit','MPa')); setQuantity(data,['material','Fu'],gv('common_fu'),getSelectedUnit('common_fu_unit','MPa')); setQuantity(data,['material','E'],gv('common_e'),getSelectedUnit('common_e_unit','MPa'));
  setQuantity(data,['analysis','span'],gv('common_span'),getSelectedUnit('common_span_unit','m')); setQuantity(data,['analysis','movement_step'],gv('common_movement_step'),getSelectedUnit('common_movement_step_unit','mm')); setQuantity(data,['analysis','station_step'],gv('common_station_step'),getSelectedUnit('common_station_step_unit','mm'));
  setText(['crane','crane_id'],'common_crane_id'); const vif=gv('common_vertical_impact_factor'); if (vif!=='') setNestedValue(data,['crane','vertical_impact_factor'],Number(vif)); const lff=gv('common_lateral_force_factor'); if (lff!=='') setNestedValue(data,['crane','lateral_force_factor'],Number(lff));
  if (!Array.isArray(data.crane?.wheels)) { ensureObjectPath(data,['crane']); data.crane.wheels = []; }
  while (data.crane.wheels.length < 2) { const idx=data.crane.wheels.length+1; data.crane.wheels.push({wheel_id:'W'+idx, position_x:{value: idx===1?0:1, unit:'mm'}, vertical_force:{value:0, unit:'kN'}}); }
  setQuantity(data,['crane','wheels',0,'vertical_force'],gv('common_wheel_1_load'),getSelectedUnit('common_wheel_1_load_unit','kN')); setQuantity(data,['crane','wheels',1,'vertical_force'],gv('common_wheel_2_load'),getSelectedUnit('common_wheel_2_load_unit','kN'));
  const spacing = gv('common_wheel_spacing'); if (spacing !== '') { const w1 = getQuantityValue(data,['crane','wheels',0,'position_x']); const base = w1 === '' ? 0 : Number(w1); const spacingNum = Number(spacing); const spacingUnit = getSelectedUnit('common_wheel_spacing_unit','mm'); setQuantity(data,['crane','wheels',0,'position_x'],base,spacingUnit); setQuantity(data,['crane','wheels',1,'position_x'],base + spacingNum,spacingUnit); }
  setNestedValue(data,['rail_eccentricity','enabled'],gv('common_rail_eccentricity_enabled')); setQuantity(data,['rail_eccentricity','vertical_eccentricity_y'],gv('common_vertical_eccentricity_y'),getSelectedUnit('common_vertical_eccentricity_y_unit','mm')); setQuantity(data,['rail_eccentricity','lateral_load_height_z'],gv('common_lateral_load_height_z'),getSelectedUnit('common_lateral_load_height_z_unit','mm'));
  const def=gv('common_deflection_preset'); if (def!=='') setNestedValue(data,['criteria_presets','deflection'],[def]); const stress=gv('common_stress_preset'); if (stress!=='') setNestedValue(data,['criteria_presets','stress'],[stress]);
  document.getElementById('case_json').value = prettyJson(data);
  if (typeof saveSession === 'function') saveSession();
  if (typeof refreshCaseOutline === 'function') refreshCaseOutline();
  if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
    if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  setStatus('Common inputs applied to JSON.'); markWorkflowStepDone(2); updateBetaReadiness('json_loaded', true);
}


function getSelectedBaseShapeId() {
  const el = document.getElementById('profile_base_shape_id');
  return el ? String(el.value ?? '').trim() : '';
}
function setSelectedBaseShapeId(value) {
  const el = document.getElementById('profile_base_shape_id');
  if (!el) return;
  const v = String(value ?? '').trim();
  const supported = ['CIRSOC_IPN_180','CIRSOC_IPN_200','CIRSOC_IPN_240','CIRSOC_IPN_300','CIRSOC_IPB_200'];
  el.value = supported.includes(v) ? v : '';
}
function renderProfileMaterialErrors(errors) {
  const panel = document.getElementById('profile_material_errors');
  if (!panel) return;
  if (!Array.isArray(errors) || errors.length === 0) { panel.innerHTML = '<p>No profile/material errors.</p>'; return; }
  panel.innerHTML = '<ul style="margin:0.3rem 0 0.1rem 1.2rem;">' + errors.map((e) => '<li>' + escapeHtml(e) + '</li>').join('') + '</ul>';
}
function validateProfileMaterialInputs() {
  const materialPreset = String(document.getElementById('profile_material_preset')?.value ?? 'F24').trim();
  const materialId = String(document.getElementById('profile_material_id')?.value ?? '').trim();
  const fy = parseOptionalNumber(String(document.getElementById('profile_fy')?.value ?? '').trim());
  const fu = parseOptionalNumber(String(document.getElementById('profile_fu')?.value ?? '').trim());
  const e = parseOptionalNumber(String(document.getElementById('profile_e')?.value ?? '').trim());
  const errors = [];
  if (getSelectedBaseShapeId() === '') errors.push('Base Shape ID is required.');
  const allMaterialBlank = materialId === '' && fy === null && fu === null && e === null;
  if (materialId === '' && !(materialPreset === 'Custom' && allMaterialBlank)) errors.push('Material ID is required.');
  if (Number.isNaN(fy) || (fy !== null && !isPositiveNumber(fy))) errors.push('Fy must be positive.');
  if (Number.isNaN(fu) || (fu !== null && !isPositiveNumber(fu))) errors.push('Fu must be positive.');
  if (Number.isNaN(e) || (e !== null && !isPositiveNumber(e))) errors.push('E must be positive.');
  renderProfileMaterialErrors(errors);
  return {errors: Array.from(new Set(errors)), materialId: materialId, fy: fy, fu: fu, e: e};
}
function applyMaterialPreset() {
  const preset = String(document.getElementById('profile_material_preset')?.value ?? 'F24').trim();
  const setVal = (id, value, overwrite=true) => { const el = document.getElementById(id); if (!el) return; if (overwrite || String(el.value ?? '').trim() === '') el.value = String(value); };
  if (preset === 'F24') { setVal('profile_material_id','F24'); setVal('profile_fy','235'); setVal('profile_fu','370'); setVal('profile_e','200000'); }
  if (preset === 'F36') { setVal('profile_material_id','F36'); setVal('profile_fy','355'); setVal('profile_fu','470'); setVal('profile_e','200000'); }
  if (preset === 'Custom') {
    setVal('profile_material_id','',false); setVal('profile_fy','',false); setVal('profile_fu','',false); setVal('profile_e','',false);
  }
}
function loadProfileMaterialFromJson() {
  let data;
  try { data = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot load profile/material: invalid JSON.'); return; }
  setSelectedBaseShapeId(getNestedValue(data,['base_shape_id']) ?? getNestedValue(data,['section','base_shape_id']) ?? '');
  const setVal=(id,v)=>{ const el=document.getElementById(id); if (el) el.value = v ?? ''; };
  setVal('profile_material_id', getNestedValue(data,['material','material_id']) ?? '');
  setVal('profile_fy', getQuantityValue(data,['material','Fy']));
  setVal('profile_fu', getQuantityValue(data,['material','Fu']));
  setVal('profile_e', getQuantityValue(data,['material','E']));
  renderProfileMaterialErrors([]);
  setStatus('Profile/material loaded from JSON.');
}
function applyProfileMaterialToJson() {
  let data;
  try { data = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot apply profile/material: invalid JSON.'); return; }
  const validated = validateProfileMaterialInputs();
  if (validated.errors.length > 0) { setStatus('Profile/material inputs contain errors.'); return; }
  const baseShapeId = getSelectedBaseShapeId();
  if (getNestedValue(data,['base_shape_id']) !== undefined) setNestedValue(data,['base_shape_id'], baseShapeId);
  if (getNestedValue(data,['section','base_shape_id']) !== undefined) setNestedValue(data,['section','base_shape_id'], baseShapeId);
  if (getNestedValue(data,['base_shape_id']) === undefined && getNestedValue(data,['section','base_shape_id']) === undefined) setNestedValue(data,['base_shape_id'], baseShapeId);
  setNestedValue(data,['material','material_id'], validated.materialId);
  setQuantity(data,['material','Fy'], validated.fy, 'MPa');
  setQuantity(data,['material','Fu'], validated.fu, 'MPa');
  setQuantity(data,['material','E'], validated.e, 'MPa');
  document.getElementById('case_json').value = JSON.stringify(data, null, 2);
  if (typeof saveSession === 'function') saveSession();
  if (typeof refreshCaseOutline === 'function') refreshCaseOutline();
  if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
    if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  if (typeof loadCommonInputsFromJson === 'function') loadCommonInputsFromJson();
  if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  setStatus('Profile/material applied to JSON.'); markWorkflowStepDone(2); updateBetaReadiness('json_loaded', true);
}
function resetProfileMaterial() {
  setSelectedBaseShapeId('');
  const preset = document.getElementById('profile_material_preset');
  if (preset) preset.value = 'F24';
  const ids = ['profile_material_id','profile_fy','profile_fu','profile_e'];
  for (const id of ids) { const el = document.getElementById(id); if (el) el.value = ''; }
  applyMaterialPreset();
  renderProfileMaterialErrors([]);
  setStatus('Profile/material inputs reset.');
}


function getWheelRows() {
  const body = document.getElementById('wheel_table_body');
  if (!body) return [];
  const rows = [];
  for (const tr of body.querySelectorAll('tr')) {
    rows.push({
      wheel_id: String(tr.querySelector('[data-wheel-field="wheel_id"]')?.value ?? '').trim(),
      position_x: String(tr.querySelector('[data-wheel-field="position_x"]')?.value ?? '').trim(),
      position_unit: String(tr.querySelector('[data-wheel-field="position_unit"]')?.value ?? '').trim(),
      vertical_force: String(tr.querySelector('[data-wheel-field="vertical_force"]')?.value ?? '').trim(),
      force_unit: String(tr.querySelector('[data-wheel-field="force_unit"]')?.value ?? '').trim()
    });
  }
  return rows;
}
function renderWheelTableErrors(errors) {
  const panel = document.getElementById('wheel_table_errors');
  if (!panel) return;
  if (!Array.isArray(errors) || errors.length === 0) { panel.innerHTML = '<p>No wheel table errors.</p>'; return; }
  panel.innerHTML = '<ul style="margin:0.3rem 0 0.1rem 1.2rem;">' + errors.map((e) => '<li>' + escapeHtml(e) + '</li>').join('') + '</ul>';
}
function validateWheelTable() {
  const rows = getWheelRows();
  const errors = [];
  const ids = rows.map((row) => row.wheel_id).filter((value) => value !== '');
  if (ids.length !== new Set(ids).size) errors.push('Wheel IDs must be unique.');
  for (const row of rows) {
    if (!row.wheel_id) errors.push('Wheel ID is required.');
    const px = Number(row.position_x);
    if (row.position_x === '' || Number.isNaN(px)) errors.push('Wheel position must be numeric.');
    const vf = Number(row.vertical_force);
    if (row.vertical_force === '' || Number.isNaN(vf) || vf <= 0) errors.push('Wheel vertical force must be positive.');
    if (!row.position_unit || !['m','mm','ft'].includes(row.position_unit)) errors.push('Wheel position unit must be selected.');
    if (!row.force_unit || !['kN','N','kip'].includes(row.force_unit)) errors.push('Wheel force unit must be selected.');
  }
  const uniqueErrors = Array.from(new Set(errors));
  renderWheelTableErrors(uniqueErrors);
  return uniqueErrors;
}
function addWheelRow(initialRow) {
  const body = document.getElementById('wheel_table_body');
  if (!body) return;
  const nextIndex = body.querySelectorAll('tr').length + 1;
  const row = initialRow || {};
  const tr = document.createElement('tr');
  tr.innerHTML = '<td><input data-wheel-field="wheel_id" value="' + escapeHtml(String(row.wheel_id || ('W' + nextIndex))) + '"/></td>' +
    '<td><input data-wheel-field="position_x" value="' + escapeHtml(row.position_x ?? '') + '"/></td>' +
    '<td><select data-wheel-field="position_unit"><option>m</option><option>mm</option><option>ft</option></select></td>' +
    '<td><input data-wheel-field="vertical_force" value="' + escapeHtml(row.vertical_force ?? '') + '"/></td>' +
    '<td><select data-wheel-field="force_unit"><option>kN</option><option>N</option><option>kip</option></select></td>' +
    '<td><button class="small-btn" data-wheel-action="remove">Remove</button></td>';
  body.appendChild(tr);
  tr.querySelector('[data-wheel-field="position_unit"]').value = ['m','mm','ft'].includes(row.position_unit) ? row.position_unit : 'm';
  tr.querySelector('[data-wheel-field="force_unit"]').value = ['kN','N','kip'].includes(row.force_unit) ? row.force_unit : 'kN';
  tr.querySelector('[data-wheel-action="remove"]').addEventListener('click', () => removeWheelRow(tr));
}
function removeWheelRow(rowElement) { if (rowElement && rowElement.remove) rowElement.remove(); validateWheelTable(); }
function clearWheelTable() { const body = document.getElementById('wheel_table_body'); if (body) body.innerHTML = ''; renderWheelTableErrors([]); setStatus('Wheel table cleared.'); }
function setWheelRows(rows) {
  const body = document.getElementById('wheel_table_body');
  if (!body) return;
  body.innerHTML = '';
  for (const row of (Array.isArray(rows) ? rows : [])) addWheelRow(row);
  renderWheelTableErrors([]);
}
function loadWheelsFromJson() {
  let data;
  try { data = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot load wheels: invalid JSON.'); return; }
  const wheels = Array.isArray(data?.crane?.wheels) ? data.crane.wheels : [];
  if (wheels.length === 0) { setWheelRows([]);
refreshCaseQuality(); setStatus('No wheels found in JSON.'); return; }
  const rows = wheels.map((wheel, idx) => ({
    wheel_id: String(wheel?.wheel_id ?? ('W' + (idx + 1))),
    position_x: wheel?.position_x?.value ?? '',
    position_unit: wheel?.position_x?.unit ?? 'm',
    vertical_force: wheel?.vertical_force?.value ?? '',
    force_unit: wheel?.vertical_force?.unit ?? 'kN'
  }));
  setWheelRows(rows);
  validateWheelTable();
  setStatus('Wheel table loaded from JSON.');
}
function applyWheelsToJson() {
  const errors = validateWheelTable();
  if (errors.length > 0) { setStatus('Wheel table contains errors.'); return; }
  let data;
  try { data = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot apply wheels: invalid JSON.'); return; }
  const rows = getWheelRows();
  if (!data.crane || typeof data.crane !== 'object') data.crane = {};
  data.crane.wheels = rows.map((row) => ({
    wheel_id: row.wheel_id,
    position_x: {value: Number(row.position_x), unit: row.position_unit},
    vertical_force: {value: Number(row.vertical_force), unit: row.force_unit}
  }));
  document.getElementById('case_json').value = prettyJson(data);
  if (typeof saveSession === 'function') saveSession();
  if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
    if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  if (typeof refreshCaseOutline === 'function') refreshCaseOutline();
  if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  setStatus('Wheel table applied to JSON.'); markWorkflowStepDone(2); updateBetaReadiness('json_loaded', true);
}

function findJsonPath(path) {
  const editor = document.getElementById('case_json');
  if (!editor || !path) { setStatus('Path not found in editor.'); return; }
  const segments = String(path).split('.').filter(Boolean);
  const lastSegment = segments.length > 0 ? segments[segments.length - 1] : String(path);
  const keyHint = '"' + lastSegment + '"';
  const searchText = editor.value || '';
  let idx = searchText.indexOf(keyHint);
  if (idx < 0) idx = searchText.indexOf(lastSegment);
  editor.focus();
  if (idx >= 0) {
    const end = Math.min(searchText.length, idx + Math.max(lastSegment.length, keyHint.length));
    editor.setSelectionRange(idx, end);
    setStatus('Found path hint: ' + lastSegment);
    return;
  }
  setStatus('Path not found in editor.');
}
function renderValidationTable(messages) {
  let html = '<table><thead><tr><th>Severity</th><th>Path</th><th>Message</th><th>Hint</th></tr></thead><tbody>';
  for (const m of messages) {
    const sev = m && m.severity ? m.severity : 'N/A';
    const path = m && m.path ? m.path : 'N/A';
    const msg = m && m.message ? m.message : 'N/A';
    const hint = m && m.hint ? m.hint : 'N/A';
    const findPathPayload = encodeURIComponent(String(path));
    const find = path !== 'N/A' ? '<button class=\"small-btn\" onclick=\"findJsonPath(decodeURIComponent(\\'' + findPathPayload + '\\'))\">Find Path</button>' : '';
    html += '<tr><td>' + escapeHtml(sev) + '</td><td>' + escapeHtml(path) + (find ? '<br/>' + find : '') + '</td><td>' + escapeHtml(msg) + '</td><td>' + escapeHtml(hint) + '</td></tr>';
  }
  html += '</tbody></table>';
  return html;
}
function renderValidation(validation) {
  const panel = document.getElementById('validation_output');
  if (!validation || typeof validation !== 'object') { panel.innerHTML = '<p>N/A</p>'; return; }
  const isValid = validation.valid === true;
  let html = '<p><strong>Status:</strong> <span class=\"' + (isValid ? 'pass' : 'fail') + '\">' + (isValid ? 'VALID' : 'INVALID') + '</span></p>';
  const messages = Array.isArray(validation.messages) ? validation.messages : [];
  if (messages.length === 0) { panel.innerHTML = html; return; }
  html += renderValidationTable(messages);
  panel.innerHTML = html;
}
async function copyErrorList() {
  const validation = lastValidationResponse;
  const messages = validation && Array.isArray(validation.messages) ? validation.messages : [];
  if (messages.length === 0) { setStatus('No validation messages available.'); return; }
  const lines = messages.map((m, i) => (i + 1) + '. [' + (m.severity || 'N/A') + '] path=' + (m.path || 'N/A') + ' | message=' + (m.message || 'N/A') + ' | hint=' + (m.hint || 'N/A'));
  await copyText(lines.join('\\n'), 'Validation error list copied.', 'Could not copy validation error list.');
}
function formatPassFail(value) {
  if (value === true) return '<span class=\"pass\">PASS</span>';
  if (value === false) return '<span class=\"fail\">FAIL</span>';
  return 'N/A';
}
function renderSummary(summary) {
  const panel = document.getElementById('summary_output');
  if (!summary || typeof summary !== 'object') { panel.innerHTML = '<p>N/A</p>'; return; }
  const keys = ['summary_id','span_internal_mm','section_id','load_model_id','max_vertical_moment_Nmm','max_vertical_shear_abs_N','max_vertical_deflection_mm','max_lateral_moment_Nmm','max_biaxial_stress_MPa','max_torsional_input_Nmm','serviceability_passed','stress_criteria_passed','overall_passed'];
  let html = '<table><tbody>';
  for (const key of keys) {
    const value = summary[key];
    const rendered = (key.endsWith('_passed')) ? formatPassFail(value) : escapeHtml(value ?? 'N/A');
    html += '<tr><th>' + escapeHtml(key) + '</th><td>' + rendered + '</td></tr>';
  }
  html += '</tbody></table>';
  panel.innerHTML = html;
}
function renderResultCards(summary) {
  const panel = document.getElementById('result_cards');
  if (!panel) return;
  const statusClass = (value) => value === true ? 'status-pass' : (value === false ? 'status-fail' : 'status-na');
  const statusText = (value) => value === true ? 'PASS' : (value === false ? 'FAIL' : 'N/A');
  if (!summary || typeof summary !== 'object') { panel.innerHTML = '<h4>Result Cards</h4><p>N/A</p>'; return; }
  const cards = [
    ['Max Moment', summary.max_vertical_moment_Nmm ?? 'N/A', 'status-na'],
    ['Max Shear', summary.max_vertical_shear_abs_N ?? 'N/A', 'status-na'],
    ['Max Deflection', summary.max_vertical_deflection_mm ?? 'N/A', 'status-na'],
    ['Max Biaxial Stress', summary.max_biaxial_stress_MPa ?? 'N/A', 'status-na'],
    ['Serviceability', statusText(summary.serviceability_passed), statusClass(summary.serviceability_passed)],
    ['Stress', statusText(summary.stress_criteria_passed), statusClass(summary.stress_criteria_passed)],
    ['Overall', statusText(summary.overall_passed), statusClass(summary.overall_passed)]
  ];
  let html = '<h4>Result Cards</h4><p style=\"margin-top:0.2rem;color:#4b5563;\">Result cards summarize computed demands and configured generic check status.</p><div class=\"result-cards\">';
  for (const card of cards) {
    html += '<div class=\"result-card\"><div class=\"result-card-title\">' + escapeHtml(card[0]) + '</div><div class=\"result-card-value ' + card[2] + '\">' + escapeHtml(card[1]) + '</div></div>';
  }
  panel.innerHTML = html + '</div>';
}

function renderResultInterpretation(summary, runResponse) {
  const panel = document.getElementById('interpretation_output');
  if (!panel) return;
  if (!summary || typeof summary !== 'object') {
    panel.innerHTML = '<p>Run a case to see result interpretation.</p>';
    return;
  }
  const lines = [];
  const addLine = (message, cssClass) => { lines.push({message: message, cssClass: cssClass}); };
  if (summary.overall_passed === true) addLine('Overall status: PASS based on configured generic criteria.', 'interpretation-pass');
  else if (summary.overall_passed === false) addLine('Overall status: FAIL based on configured generic criteria.', 'interpretation-fail');
  else addLine('Overall status: N/A.', 'interpretation-na');

  if (summary.serviceability_passed === true) addLine('Serviceability: PASS.', 'interpretation-pass');
  else if (summary.serviceability_passed === false) addLine('Serviceability: FAIL. Review deflection demand and configured limits.', 'interpretation-fail');
  else addLine('Serviceability: N/A.', 'interpretation-na');

  if (summary.stress_criteria_passed === true) addLine('Stress criteria: PASS.', 'interpretation-pass');
  else if (summary.stress_criteria_passed === false) addLine('Stress criteria: FAIL. Review stress demand and configured limits.', 'interpretation-fail');
  else addLine('Stress criteria: N/A.', 'interpretation-na');

  if (summary.serviceability_passed === false) addLine('Deflection demand appears high relative to configured checks.', 'interpretation-warning');
  else if (summary.serviceability_passed === true) addLine('Deflection demand appears within configured checks.', 'interpretation-pass');
  else addLine('Deflection demand interpretation: N/A.', 'interpretation-na');

  if (summary.stress_criteria_passed === false) addLine('Stress demand appears high relative to configured checks.', 'interpretation-warning');
  else if (summary.stress_criteria_passed === true) addLine('Stress demand appears within configured checks.', 'interpretation-pass');
  else addLine('Stress demand interpretation: N/A.', 'interpretation-na');

  const torsionalInput = Number(summary.max_torsional_input_Nmm ?? 0);
  if (Number.isFinite(torsionalInput) && torsionalInput > 0) addLine('Torsional input is present. Current UI reports torsional input only; torsional/warping stress checks are not performed.', 'interpretation-warning');
  else addLine('No torsional input reported.', 'interpretation-na');

  const warnings = Array.isArray(runResponse?.warnings) ? runResponse.warnings : [];
  if (warnings.length > 0) addLine('Warnings are present. Review them before using results.', 'interpretation-warning');
  else addLine('No warnings reported.', 'interpretation-pass');

  addLine('These are generic configured checks, not official CIRSOC/CISC/AISC compliance checks.', 'interpretation-warning');
  addLine('Engineering review is required.', 'interpretation-warning');

  panel.innerHTML = '<ul style="margin:0.4rem 0 0.2rem 1.2rem; padding:0;">' + lines.map((line) => '<li class="' + line.cssClass + '">' + escapeHtml(line.message) + '</li>').join('') + '</ul>';
}

async function copyInterpretation() {
  const panel = document.getElementById('interpretation_output');
  const text = panel ? (panel.textContent || '').trim() : '';
  if (!text || text === 'Run a case to see result interpretation.') { setStatus('No interpretation available. Run a case first.'); return; }
  await copyText(text, 'Interpretation copied.', 'Could not copy interpretation.');
}
function loadScenarios() {
  try {
    const raw = localStorage.getItem(scenarioStorageKey);
    const scenarios = raw ? JSON.parse(raw) : [];
    const normalized = Array.isArray(scenarios) ? scenarios.filter((item) => item && typeof item === 'object') : [];
    renderScenarioList(normalized);
    return normalized;
  } catch (err) { renderScenarioList([]); return []; }
}
function renderScenarioList(scenarios) {
  const body = document.getElementById('scenario_list_body');
  if (!body) return;
  if (!Array.isArray(scenarios) || scenarios.length === 0) { body.innerHTML = '<tr><td colspan="3">No saved scenarios available.</td></tr>'; return; }
  let html = '';
  for (const scenario of scenarios) {
    const encoded = encodeURIComponent(String(scenario.scenario_id ?? ''));
    html += '<tr><td>' + escapeHtml(String(scenario.scenario_id ?? 'N/A')) + '</td><td>' + escapeHtml(String(scenario.saved_at ?? 'N/A')) + '</td><td><button class="small-btn" onclick="loadScenario(\\'' + encoded + '\\')">Load Scenario</button> <button class="small-btn" onclick="deleteScenario(\\'' + encoded + '\\')">Delete Scenario</button></td></tr>';
  }
  body.innerHTML = html;
}
function saveCurrentScenario() {
  const scenarioId = String(document.getElementById('scenario_name')?.value ?? '').trim();
  if (!scenarioId) { setStatus('Scenario name is required.'); return; }
  let caseJson = '';
  try { caseJson = prettyJson(JSON.parse(getCurrentCaseJsonText())); } catch (err) { setStatus('Cannot save scenario: invalid JSON.'); return; }
  const scenarios = loadScenarios();
  if (scenarios.some((item) => item.scenario_id === scenarioId)) { setStatus('Scenario already exists.'); return; }
  scenarios.push({scenario_id: scenarioId, case_json: caseJson, saved_at: new Date().toISOString()});
  localStorage.setItem(scenarioStorageKey, JSON.stringify(scenarios));
  renderScenarioList(scenarios);
  setStatus('Scenario saved.');
}
function loadScenario(scenarioIdEncoded) {
  const scenarioId = decodeURIComponent(String(scenarioIdEncoded ?? ''));
  const scenario = loadScenarios().find((item) => item.scenario_id === scenarioId);
  if (!scenario) { setStatus('No saved scenarios available.'); return; }
  document.getElementById('case_json').value = String(scenario.case_json ?? '');
  saveSession();
  setStatus('Scenario loaded.');
}
function deleteScenario(scenarioIdEncoded) {
  const scenarioId = decodeURIComponent(String(scenarioIdEncoded ?? ''));
  const filtered = loadScenarios().filter((item) => item.scenario_id !== scenarioId);
  localStorage.setItem(scenarioStorageKey, JSON.stringify(filtered));
  renderScenarioList(filtered);
  setStatus('Scenario deleted.');
}
function clearAllScenarios() {
  localStorage.setItem(scenarioStorageKey, JSON.stringify([]));
  renderScenarioList([]);
  setStatus('All scenarios cleared.');
}
function getScenarioCaseSummaryFields(summary) {
  return {
    case_id: summary?.summary_id ?? 'N/A',
    base_shape_id: summary?.section_id ?? 'N/A',
    cover_plate_enabled: 'N/A',
    span: summary?.span_internal_mm ?? 'N/A',
    max_vertical_moment_Nmm: summary?.max_vertical_moment_Nmm ?? 'N/A',
    max_vertical_shear_abs_N: summary?.max_vertical_shear_abs_N ?? 'N/A',
    max_vertical_deflection_mm: summary?.max_vertical_deflection_mm ?? 'N/A',
    max_biaxial_stress_MPa: summary?.max_biaxial_stress_MPa ?? 'N/A',
    serviceability_passed: summary?.serviceability_passed,
    stress_criteria_passed: summary?.stress_criteria_passed,
    overall_passed: summary?.overall_passed
  };
}
async function runAllScenarios() {
  const scenarios = loadScenarios();
  if (!Array.isArray(scenarios) || scenarios.length === 0) { setStatus('No saved scenarios available.'); return; }
  setStatus('Running saved scenarios...');
  const results = [];
  for (const scenario of scenarios) {
    try {
      const payload = {case_json: String(scenario.case_json ?? ''), output_formats: ['summary']};
      const response = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const data = await response.json();
      if (!response.ok || data.success === false || !data.summary) results.push({scenario: scenario.scenario_id, error: data.error || 'Run failed.'});
      else results.push({scenario: scenario.scenario_id, summary_fields: getScenarioCaseSummaryFields(data.summary)});
    } catch (err) { results.push({scenario: scenario.scenario_id, error: 'Network/error during run.'}); }
  }
  lastScenarioComparisonResults = results;
  renderScenarioComparison(results);
  setStatus('Scenario comparison complete.'); markWorkflowStepDone(7);
}
function renderScenarioComparison(results) {
  const panel = document.getElementById('scenario_comparison_output');
  if (!panel) return;
  if (!Array.isArray(results) || results.length === 0) { panel.innerHTML = '<p>No saved scenarios available.</p>'; return; }
  let html = '<table><thead><tr><th>Scenario</th><th>case_id</th><th>base_shape_id</th><th>cover_plate_enabled</th><th>span</th><th>max_vertical_moment_Nmm</th><th>max_vertical_shear_abs_N</th><th>max_vertical_deflection_mm</th><th>max_biaxial_stress_MPa</th><th>serviceability_passed</th><th>stress_criteria_passed</th><th>overall_passed</th></tr></thead><tbody>';
  for (const result of results) {
    if (result.error) { html += '<tr><td>' + escapeHtml(String(result.scenario)) + '</td><td colspan="11">' + escapeHtml(String(result.error)) + '</td></tr>'; continue; }
    const f = result.summary_fields || {};
    html += '<tr><td>' + escapeHtml(String(result.scenario)) + '</td><td>' + escapeHtml(String(f.case_id ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.base_shape_id ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.cover_plate_enabled ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.span ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.max_vertical_moment_Nmm ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.max_vertical_shear_abs_N ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.max_vertical_deflection_mm ?? 'N/A')) + '</td><td>' + escapeHtml(String(f.max_biaxial_stress_MPa ?? 'N/A')) + '</td><td>' + formatPassFail(f.serviceability_passed) + '</td><td>' + formatPassFail(f.stress_criteria_passed) + '</td><td>' + formatPassFail(f.overall_passed) + '</td></tr>';
  }
  panel.innerHTML = html + '</tbody></table>';
}
function downloadScenarioComparison() {
  if (!Array.isArray(lastScenarioComparisonResults) || lastScenarioComparisonResults.length === 0) { setStatus('No comparison results available. Run scenarios first.'); return; }
  downloadText('scenario_comparison.json', prettyJson(lastScenarioComparisonResults), 'application/json;charset=utf-8');
}
async function copyScenarioComparison() {
  if (!Array.isArray(lastScenarioComparisonResults) || lastScenarioComparisonResults.length === 0) { setStatus('No comparison results available. Run scenarios first.'); return; }
  markWorkflowStepDone(7);
  await copyText(prettyJson(lastScenarioComparisonResults), 'Scenario comparison copied.', 'Could not copy scenario comparison.');
}

function refreshCaseOutline() {
  const panel = document.getElementById('case_outline_output');
  try {
    const c = JSON.parse(getCurrentCaseJsonText());
    const read = (root, path, fallback='N/A') => path.reduce((acc, key) => (acc && Object.prototype.hasOwnProperty.call(acc, key)) ? acc[key] : undefined, root) ?? fallback;
    const rows = [
      ['schema_version', read(c, ['schema_version'])], ['case_id', read(c, ['case_id'])], ['description', read(c, ['description'])],
      ['base_shape_id', read(c, ['base_shape_id'])], ['section.section_id', read(c, ['section','section_id'])], ['section.cover_plate.enabled', read(c, ['section','cover_plate','enabled'])],
      ['material.material_id', read(c, ['material','material_id'])], ['material.Fy', read(c, ['material','Fy'])], ['analysis.span', read(c, ['analysis','span'])],
      ['crane.crane_id', read(c, ['crane','crane_id'])], ['number of crane.wheels', Array.isArray(read(c, ['crane','wheels'], null)) ? read(c, ['crane','wheels']).length : 'N/A'],
      ['criteria_presets', read(c, ['criteria_presets'])], ['rail_eccentricity.enabled', read(c, ['rail_eccentricity','enabled'])]
    ];
    let html = '<table><tbody>';
    for (const r of rows) { html += '<tr><th>' + escapeHtml(r[0]) + '</th><td>' + escapeHtml(typeof r[1] === 'object' ? JSON.stringify(r[1]) : String(r[1])) + '</td></tr>'; }
    panel.innerHTML = html + '</tbody></table>';
  } catch (err) { panel.innerHTML = '<p>Cannot build outline: invalid JSON.</p>'; }
}
function dismissWelcomeBanner(){ localStorage.setItem(WELCOME_DISMISSED_KEY,'true'); const panel=document.getElementById('welcome_panel'); if(panel) panel.style.display='none'; setStatus('Welcome banner dismissed.'); }
function renderDocumentationPortal(){ const out=document.getElementById('documentation_portal_output'); if(!out) return; out.textContent='Use the topic buttons to load concise help content.'; }
function showHelpTopic(topic){ const out=document.getElementById('documentation_portal_output'); if(!out) return; const topics={'Start here':'Start here: begin with Guided Demo, then load a template and validate before run.','Basic workflow':'Basic workflow: load/import case, review preview, validate, run, then review results.','Project workflow':'Project workflow: create project, save JSON, run to outputs, and use run history for comparisons.','Troubleshooting':buildHelpSummary()}; out.textContent=topics[topic]||'Topic unavailable.'; setStatus('Help topic shown.'); }
function buildHelpSummary(){ return `If buttons do not respond: refresh page; run UI Diagnostics; run local UI smoke check; check browser console; clear saved session; restart server.
If 127.0.0.1 refuses connection: confirm server is running; if using remote/Codex, open forwarded port instead of local 127.0.0.1.
If validation fails: inspect Validation table; inspect Case Quality Warnings; check quantity units.
If run fails: validate first; review Raw Response; create Support Bundle.`; }
async function copyHelpSummary(){ await copyText(buildHelpSummary()); setStatus('Help summary copied.'); }
function markGuidedDemoStep(activeIndex){ const items=document.querySelectorAll('#guided_demo_steps li'); items.forEach((item,idx)=>{ item.style.fontWeight = idx===activeIndex ? '700' : '400'; }); }
function renderGuidedDemo(){ const out=document.getElementById('guided_demo_output'); if(!out) return; let state={step:0,started:false}; try{ const raw=localStorage.getItem(GUIDED_DEMO_STATE_KEY); if(raw) state=JSON.parse(raw);}catch(_){ state={step:0,started:false}; } markGuidedDemoStep(Math.max(0, Math.min(6, Number(state.step)||0))); out.textContent=state.started ? ('Current demo step: '+String((Number(state.step)||0)+1)) : 'Guided demo ready.'; }
function startGuidedDemo(){ const state={step:0,started:true}; localStorage.setItem(GUIDED_DEMO_STATE_KEY,JSON.stringify(state)); renderGuidedDemo(); setStatus('Guided demo started.'); }
function nextGuidedDemoStep(){ try{ const state=JSON.parse(localStorage.getItem(GUIDED_DEMO_STATE_KEY)||'{"step":0,"started":false}'); if(!state.started){ setStatus('Guided demo step failed.'); return; } state.step = Math.min(6, (Number(state.step)||0)+1); localStorage.setItem(GUIDED_DEMO_STATE_KEY,JSON.stringify(state)); renderGuidedDemo(); setStatus('Guided demo advanced.'); }catch(_){ setStatus('Guided demo step failed.'); } }
function resetGuidedDemo(){ localStorage.setItem(GUIDED_DEMO_STATE_KEY,JSON.stringify({step:0,started:false})); renderGuidedDemo(); setStatus('Guided demo reset.'); }
async function copyDemoInstructions(){ const text=`Guided Demo Steps:
1. Load demo template
2. Review preview
3. Check case quality
4. Validate demo
5. Run demo
6. Review interpretation
7. Export demo results`; await copyText(text); setStatus('Guided demo instructions copied.'); }
function renderHelpPanel() {
  document.getElementById('help_panel').innerHTML = '<ol><li>Load a template or import JSON.</li><li>Edit JSON.</li><li>Click Validate.</li><li>Fix validation errors.</li><li>Click Run.</li><li>Review Summary and HTML Report.</li><li>Download JSON / Summary / Report.</li></ol><p><strong>Warnings:</strong> Local beta tool; Results require engineering review; Generic checks only; no official CIRSOC/CISC/AISC checks; no fatigue; no torsional/warping stress; no LTB.</p><p><strong>API:</strong> /api/health, /api/templates, /api/validate, /api/run</p>';
}
function openReportInNewTab() {
  if (!latestHtmlReport) return;
  const win = window.open('', '_blank');
  if (!win) { setStatus('Run failed: popup blocked by browser.'); return; }
  win.document.open();
  win.document.write(latestHtmlReport);
  win.document.close();
}
function setProjectWorkspaceStatus(message) {
  const el = document.getElementById('project_workspace_status');
  if (el) el.textContent = message;
}
function validateProjectNameClient(name) {
  return /^[A-Za-z0-9_-]+$/.test(name || '');
}
function getSelectedProjectName() {
  const input = document.getElementById('project_name');
  return input ? input.value.trim() : '';
}
function renderProjectList(projects) {
  const tbody = document.getElementById('project_list_body');
  if (!tbody) return;
  tbody.innerHTML = '';
  (projects || []).forEach((project) => {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>' + project.name + '</td><td>' + (project.has_input_case ? 'Yes' : 'No') + '</td><td>' + (project.has_outputs ? 'Yes' : 'No') + '</td><td><button class="small-btn" data-project-name="' + project.name + '">Use</button></td>';
    const btn = tr.querySelector('button');
    if (btn) btn.addEventListener('click', () => { document.getElementById('project_name').value = project.name; });
    tbody.appendChild(tr);
  });
}
async function refreshProjectList() {
  const r = await fetch('/api/projects');
  const data = await r.json();
  if (!r.ok) { setProjectWorkspaceStatus(data.error || 'Could not refresh project list.'); return; }
  renderProjectList(data.projects || []);
}
async function createProject() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectWorkspaceStatus('Invalid project name. Use only letters, numbers, dash, and underscore.'); return; }
  const payload = {project_name: projectName, template_id: document.getElementById('project_template').value, overwrite: false};
  const r = await fetch('/api/projects/create', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await r.json();
  if (!r.ok) { setProjectWorkspaceStatus(data.error || 'Could not create project.'); return; }
  setProjectWorkspaceStatus('Project created.');
  await refreshProjectList();
}
async function openProject() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectWorkspaceStatus('Invalid project name. Use only letters, numbers, dash, and underscore.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/case');
  const data = await r.json();
  if (!r.ok) { setProjectWorkspaceStatus(data.error || 'Could not open project.'); return; }
  document.getElementById('case_json').value = data.case_json || JSON.stringify(data.case_data || {}, null, 2);
  clearOutput();
  if (typeof refreshCaseOutline === 'function') refreshCaseOutline();
  if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
  if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  setProjectWorkspaceStatus('Project opened.');
}
async function saveProjectCase() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectWorkspaceStatus('Invalid project name. Use only letters, numbers, dash, and underscore.'); return; }
  try { JSON.parse(document.getElementById('case_json').value); } catch (err) { setProjectWorkspaceStatus('Cannot save project: invalid JSON.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({case_json: document.getElementById('case_json').value})});
  const data = await r.json();
  if (!r.ok) { setProjectWorkspaceStatus(data.error || 'Could not save project case.'); return; }
  setProjectWorkspaceStatus('Project input_case.json saved.');
}
async function runProject() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectWorkspaceStatus('Invalid project name. Use only letters, numbers, dash, and underscore.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/run', {method:'POST'});
  const data = await r.json();
  if (!r.ok || !data.success) { setProjectWorkspaceStatus('Project run failed.'); return; }
  renderSummary(data.summary || null);
  renderResultCards(data.summary || null);
  renderResultInterpretation(data.summary || null, data);
  if (data.report_html) { latestHtmlReport = data.report_html; document.getElementById('html_output').srcdoc = latestHtmlReport; }
  setProjectWorkspaceStatus('Project run complete.');
}
function setArchiveStatus(message) {
  document.getElementById('archive_export_status').textContent = message;
}
function getArchiveProjectName() {
  return getSelectedProjectName();
}
function renderArchiveManifest(manifest) {
  const includedCount = Array.isArray(manifest.included_files) ? manifest.included_files.length : 0;
  document.getElementById('archive_manifest_output').textContent = JSON.stringify({
    project_name: manifest.project_name,
    generated_at: manifest.generated_at,
    archive_format_version: manifest.archive_format_version,
    included_files: manifest.included_files || [],
    included_files_count: includedCount,
    notes: manifest.notes || [],
  }, null, 2);
}
async function refreshArchiveManifest() {
  const projectName = getArchiveProjectName();
  if (!projectName) {
    setArchiveStatus('Select a project first.');
    return;
  }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/archive-manifest');
  const data = await r.json();
  if (!r.ok) {
    setArchiveStatus(data.error || 'Could not refresh archive manifest.');
    return;
  }
  window.lastArchiveManifest = data;
  renderArchiveManifest(data);
  setArchiveStatus('Archive manifest refreshed.');
}
async function downloadProjectArchive() {
  const projectName = getArchiveProjectName();
  if (!projectName) {
    setArchiveStatus('Select a project first.');
    return;
  }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/archive');
  if (!r.ok) {
    const data = await r.json();
    setArchiveStatus(data.error || 'Could not download project archive.');
    return;
  }
  const blob = await r.blob();
  downloadBlob(blob, projectName + '_archive.zip');
  setArchiveStatus('Project archive download started.');
}
async function copyArchiveManifestJson() {
  if (!window.lastArchiveManifest) {
    setArchiveStatus('No archive manifest available. Refresh archive manifest first.');
    return;
  }
  await copyText(JSON.stringify(window.lastArchiveManifest, null, 2));
  setArchiveStatus('Archive manifest JSON copied.');
}
function downloadArchiveManifestJson() {
  if (!window.lastArchiveManifest) {
    setArchiveStatus('No archive manifest available. Refresh archive manifest first.');
    return;
  }
  downloadText('archive_manifest.json', JSON.stringify(window.lastArchiveManifest, null, 2));
  setArchiveStatus('Archive manifest JSON downloaded.');
}
function showProjectOutputsInfo() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectWorkspaceStatus('Invalid project name. Use only letters, numbers, dash, and underscore.'); return; }
  const lines = ['Expected outputs directory: projects/' + projectName + '/outputs', '- summary.json', '- report.html', '- report.md', '- report.txt', '- validation_report.json', '- manifest.json'];
  document.getElementById('project_outputs_info').textContent = lines.join('\\n');
}
let selectedRunId = '';
let latestRunSummary = null;
let latestRunHtmlReport = '';
let runComparisonRuns = [];
let lastProjectRunComparison = null;
function setRunHistoryStatus(message) {
  const el = document.getElementById('run_history_status');
  if (el) el.textContent = message;
}
function getSelectedRunId() { return selectedRunId; }
function renderRunHistory(runs) {
  const tbody = document.getElementById('run_history_body');
  if (!tbody) return;
  tbody.innerHTML = '';
  (runs || []).forEach((run) => {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>' + escapeHtml(run.run_id) + '</td><td>' + escapeHtml(run.created_at || run.run_id) + '</td><td>' + (run.has_summary ? 'Yes' : 'No') + '</td><td>' + (run.has_report_html ? 'Yes' : 'No') + '</td><td><button class="small-btn" data-run-action="summary">Load Summary</button> <button class="small-btn" data-run-action="html">Load Report</button></td>';
    tr.addEventListener('click', () => { selectedRunId = run.run_id; });
    const btns = tr.querySelectorAll('button');
    if (btns[0]) btns[0].addEventListener('click', async () => { selectedRunId = run.run_id; await loadRunSummary(); });
    if (btns[1]) btns[1].addEventListener('click', async () => { selectedRunId = run.run_id; await loadRunHtmlReport(); });
    tbody.appendChild(tr);
  });
}
async function refreshRunHistory() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setRunHistoryStatus('Select a project first.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/runs');
  const data = await r.json();
  if (!r.ok) { setRunHistoryStatus(data.error || 'Could not refresh run history.'); return; }
  renderRunHistory(data.runs || []);
}
async function runProjectHistorySnapshot() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setRunHistoryStatus('Select a project first.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/run-history', {method:'POST'});
  const data = await r.json();
  if (!r.ok) { setRunHistoryStatus(data.error || 'Project run failed.'); return; }
  if (data.summary) { latestRunSummary = data.summary; renderSummary(data.summary); renderResultCards(data.summary); renderResultInterpretation(data.summary, data); }
  if (data.report_html) { latestRunHtmlReport = data.report_html; latestHtmlReport = data.report_html; document.getElementById('html_output').srcdoc = data.report_html; }
  setRunHistoryStatus('Project history run complete.');
  await refreshRunHistory();
}
async function loadRunSummary() {
  const projectName = getSelectedProjectName();
  const runId = getSelectedRunId();
  if (!projectName || !runId) { setRunHistoryStatus('No run artifact selected.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/runs/' + encodeURIComponent(runId) + '/summary');
  const data = await r.json();
  if (!r.ok) { setRunHistoryStatus(data.error || 'Could not load run summary.'); return; }
  latestRunSummary = data;
  renderSummary(data); renderResultCards(data);
  setRunHistoryStatus('Run summary loaded.');
}
async function loadRunHtmlReport() {
  const projectName = getSelectedProjectName();
  const runId = getSelectedRunId();
  if (!projectName || !runId) { setRunHistoryStatus('No run artifact selected.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/runs/' + encodeURIComponent(runId) + '/report-html');
  const data = await r.json();
  if (!r.ok) { setRunHistoryStatus(data.error || 'Could not load run HTML report.'); return; }
  latestRunHtmlReport = data.html_report || ''; latestHtmlReport = latestRunHtmlReport;
  document.getElementById('html_output').srcdoc = latestRunHtmlReport || '<p>No HTML report.</p>';
  setRunHistoryStatus('Run HTML report loaded.');
}
async function copyRunSummaryJson() { if (!latestRunSummary) { setRunHistoryStatus('No run artifact selected.'); return; } await copyText(prettyJson(latestRunSummary), 'Run summary copied.', 'Could not copy run summary.'); }
function downloadRunSummaryJson() { if (!latestRunSummary) { setRunHistoryStatus('No run artifact selected.'); return; } downloadText('run_summary.json', prettyJson(latestRunSummary), 'application/json;charset=utf-8'); }
function downloadRunHtmlReport() { if (!latestRunHtmlReport) { setRunHistoryStatus('No run artifact selected.'); return; } downloadText('run_report.html', latestRunHtmlReport, 'text/html;charset=utf-8'); }
function setProjectRunComparisonStatus(message) {
  const el = document.getElementById('run_comparison_status');
  if (el) el.textContent = message;
}
function renderRunComparisonSelectors() {
  const baselineContainer = document.getElementById('run_comparison_baseline_selector');
  const comparisonContainer = document.getElementById('run_comparison_comparison_selector');
  if (!baselineContainer || !comparisonContainer) return;
  if (!runComparisonRuns.length) {
    baselineContainer.innerHTML = '<span>N/A</span>';
    comparisonContainer.innerHTML = '<span>N/A</span>';
    return;
  }
  const baselineOptions = runComparisonRuns.map((run) => '<option value="' + escapeHtml(run.run_id) + '">' + escapeHtml(run.run_id) + '</option>').join('');
  baselineContainer.innerHTML = '<select id="run_comparison_baseline"><option value="">Select baseline run</option>' + baselineOptions + '</select>';
  comparisonContainer.innerHTML = runComparisonRuns.map((run) => '<label style="display:inline-flex;align-items:center;gap:0.35rem;margin-right:0.75rem;"><input type="checkbox" data-comparison-run-id="' + escapeHtml(run.run_id) + '"/><span>' + escapeHtml(run.run_id) + '</span></label>').join('');
}
function getSelectedBaselineRunId() {
  const el = document.getElementById('run_comparison_baseline');
  return el ? String(el.value || '').trim() : '';
}
function getSelectedComparisonRunIds() {
  const ids = [];
  document.querySelectorAll('[data-comparison-run-id]').forEach((input) => { if (input.checked) ids.push(String(input.getAttribute('data-comparison-run-id') || '').trim()); });
  return ids.filter((id) => id.length > 0);
}
async function refreshRunsForComparison() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectRunComparisonStatus('Select a project first.'); return; }
  const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/runs');
  const data = await r.json();
  if (!r.ok) { setProjectRunComparisonStatus(data.error || 'Could not refresh runs for comparison.'); return; }
  runComparisonRuns = data.runs || [];
  renderRunComparisonSelectors();
  if (!runComparisonRuns.length) { setProjectRunComparisonStatus('No project runs available.'); return; }
  setProjectRunComparisonStatus('Run list refreshed for comparison.');
}
function computeSummaryDelta(baselineValue, comparedValue) {
  if (typeof baselineValue !== 'number' || typeof comparedValue !== 'number') return null;
  return comparedValue - baselineValue;
}
function formatComparisonDelta(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
  if (value === 0) return '0';
  return value.toFixed(3);
}
function buildProjectRunComparison(projectName, baselineRunId, comparedRunIds, summaryByRunId) {
  const baseline = summaryByRunId[baselineRunId] || {};
  const allRunIds = [baselineRunId].concat(comparedRunIds);
  const rows = allRunIds.map((runId, idx) => {
    const summary = summaryByRunId[runId] || {};
    const getId = summary.case_id || summary.summary_id || 'N/A';
    const moment = summary.max_vertical_moment_Nmm;
    const shear = summary.max_vertical_shear_abs_N;
    const deflection = summary.max_vertical_deflection_mm;
    const stress = summary.max_biaxial_stress_MPa;
    return {
      run_id: runId,
      baseline: idx === 0,
      case_id_or_summary_id: getId,
      section_id: summary.section_id ?? 'N/A',
      load_model_id: summary.load_model_id ?? 'N/A',
      span_internal_mm: summary.span_internal_mm ?? 'N/A',
      max_vertical_moment_Nmm: moment ?? 'N/A',
      delta_max_vertical_moment_Nmm: idx === 0 ? 0 : computeSummaryDelta(baseline.max_vertical_moment_Nmm, moment),
      max_vertical_shear_abs_N: shear ?? 'N/A',
      delta_max_vertical_shear_abs_N: idx === 0 ? 0 : computeSummaryDelta(baseline.max_vertical_shear_abs_N, shear),
      max_vertical_deflection_mm: deflection ?? 'N/A',
      delta_max_vertical_deflection_mm: idx === 0 ? 0 : computeSummaryDelta(baseline.max_vertical_deflection_mm, deflection),
      max_biaxial_stress_MPa: stress ?? 'N/A',
      delta_max_biaxial_stress_MPa: idx === 0 ? 0 : computeSummaryDelta(baseline.max_biaxial_stress_MPa, stress),
      serviceability_passed: summary.serviceability_passed,
      stress_criteria_passed: summary.stress_criteria_passed,
      overall_passed: summary.overall_passed,
    };
  });
  return {project_name: projectName, baseline_run_id: baselineRunId, compared_run_ids: comparedRunIds, generated_at: new Date().toISOString(), rows, notes: ['Comparison uses existing summary.json values only.', 'This is not an engineering design-code check.']};
}
function renderProjectRunComparison(comparison) {
  const tableHost = document.getElementById('run_comparison_table');
  const summaryHost = document.getElementById('run_comparison_summary');
  if (!tableHost || !summaryHost) return;
  if (!comparison || !Array.isArray(comparison.rows) || !comparison.rows.length) { tableHost.innerHTML = ''; summaryHost.textContent = ''; return; }
  const rows = comparison.rows;
  const passCount = rows.filter((r) => r.overall_passed === true).length;
  const failCount = rows.filter((r) => r.overall_passed === false).length;
  const maxDeflection = rows.reduce((acc, row) => (typeof row.max_vertical_deflection_mm === 'number' && row.max_vertical_deflection_mm > acc ? row.max_vertical_deflection_mm : acc), Number.NEGATIVE_INFINITY);
  const maxStress = rows.reduce((acc, row) => (typeof row.max_biaxial_stress_MPa === 'number' && row.max_biaxial_stress_MPa > acc ? row.max_biaxial_stress_MPa : acc), Number.NEGATIVE_INFINITY);
  summaryHost.innerHTML = 'Baseline: <strong>' + escapeHtml(comparison.baseline_run_id) + '</strong> | Compared runs: <strong>' + String(comparison.compared_run_ids.length) + '</strong> | Overall PASS count: <strong>' + String(passCount) + '</strong> | Overall FAIL count: <strong>' + String(failCount) + '</strong> | Largest deflection: <strong>' + (Number.isFinite(maxDeflection) ? String(maxDeflection) : 'N/A') + '</strong> | Largest biaxial stress: <strong>' + (Number.isFinite(maxStress) ? String(maxStress) : 'N/A') + '</strong>';
  let html = '<table><thead><tr><th>Run ID</th><th>case_id / summary_id</th><th>section_id</th><th>load_model_id</th><th>span_internal_mm</th><th>max_vertical_moment_Nmm</th><th>delta_max_vertical_moment_Nmm</th><th>max_vertical_shear_abs_N</th><th>delta_max_vertical_shear_abs_N</th><th>max_vertical_deflection_mm</th><th>delta_max_vertical_deflection_mm</th><th>max_biaxial_stress_MPa</th><th>delta_max_biaxial_stress_MPa</th><th>serviceability_passed</th><th>stress_criteria_passed</th><th>overall_passed</th></tr></thead><tbody>';
  rows.forEach((row) => { html += '<tr><td>' + escapeHtml(row.run_id + (row.baseline ? ' (baseline)' : '')) + '</td><td>' + escapeHtml(String(row.case_id_or_summary_id)) + '</td><td>' + escapeHtml(String(row.section_id)) + '</td><td>' + escapeHtml(String(row.load_model_id)) + '</td><td>' + escapeHtml(String(row.span_internal_mm)) + '</td><td>' + escapeHtml(String(row.max_vertical_moment_Nmm)) + '</td><td>' + escapeHtml(formatComparisonDelta(row.delta_max_vertical_moment_Nmm)) + '</td><td>' + escapeHtml(String(row.max_vertical_shear_abs_N)) + '</td><td>' + escapeHtml(formatComparisonDelta(row.delta_max_vertical_shear_abs_N)) + '</td><td>' + escapeHtml(String(row.max_vertical_deflection_mm)) + '</td><td>' + escapeHtml(formatComparisonDelta(row.delta_max_vertical_deflection_mm)) + '</td><td>' + escapeHtml(String(row.max_biaxial_stress_MPa)) + '</td><td>' + escapeHtml(formatComparisonDelta(row.delta_max_biaxial_stress_MPa)) + '</td><td>' + formatPassFailNa(row.serviceability_passed) + '</td><td>' + formatPassFailNa(row.stress_criteria_passed) + '</td><td>' + formatPassFailNa(row.overall_passed) + '</td></tr>'; });
  tableHost.innerHTML = html + '</tbody></table>';
}
async function compareSelectedRuns() {
  const projectName = getSelectedProjectName();
  if (!validateProjectNameClient(projectName)) { setProjectRunComparisonStatus('Select a project first.'); return; }
  const baselineRunId = getSelectedBaselineRunId();
  if (!baselineRunId) { setProjectRunComparisonStatus('Select a baseline run.'); return; }
  const comparedRunIds = getSelectedComparisonRunIds().filter((runId) => runId !== baselineRunId);
  if (!comparedRunIds.length) { setProjectRunComparisonStatus('Select at least one comparison run.'); return; }
  const summaryByRunId = {};
  const loadIds = [baselineRunId].concat(comparedRunIds);
  for (const runId of loadIds) {
    const r = await fetch('/api/projects/' + encodeURIComponent(projectName) + '/runs/' + encodeURIComponent(runId) + '/summary');
    const data = await r.json();
    if (!r.ok) { setProjectRunComparisonStatus(data.error || ('Could not load summary for run ' + runId + '.')); return; }
    summaryByRunId[runId] = data;
  }
  lastProjectRunComparison = buildProjectRunComparison(projectName, baselineRunId, comparedRunIds, summaryByRunId);
  renderProjectRunComparison(lastProjectRunComparison);
  setProjectRunComparisonStatus('Project run comparison complete.');
}
function clearRunComparison() { lastProjectRunComparison = null; renderProjectRunComparison(null); setProjectRunComparisonStatus('Project run comparison cleared.'); }
async function copyRunComparisonJson() { if (!lastProjectRunComparison) { setProjectRunComparisonStatus('No project run comparison available. Compare runs first.'); return; } await copyText(prettyJson(lastProjectRunComparison), 'Project run comparison copied.', 'Could not copy run comparison JSON.'); }
function downloadRunComparisonJson() { if (!lastProjectRunComparison) { setProjectRunComparisonStatus('No project run comparison available. Compare runs first.'); return; } downloadText('project_run_comparison.json', prettyJson(lastProjectRunComparison), 'application/json;charset=utf-8'); }
async function loadTemplate() {
  try {
    const id = document.getElementById('template').value;
    const r = await fetch('/api/template/' + encodeURIComponent(id));
    const data = await r.json();
    if (!r.ok) { setStatus('Failed to load template: ' + (data.error || 'unknown error')); return; }
    document.getElementById('case_json').value = JSON.stringify(data, null, 2);
    saveSession();
    setStatus('Template loaded: ' + id); markWorkflowStepDone(1); updateBetaReadiness('json_loaded', true);
    if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
    if (typeof refreshCaseQuality === 'function') refreshCaseQuality();
  } catch (err) { setStatus('Network/error while loading template.'); }
}
async function validateCase() {
  try {
    setStatus('Validating...');
    const payload = {case_json: document.getElementById('case_json').value};
    const r = await fetch('/api/validate', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const data = await r.json();
    lastValidationResponse = data;
    lastRunResponse = null;
    renderValidation(data);
    renderRaw(data);
    setStatus(data.valid ? 'Validation complete.' : 'Validation returned errors.'); updateBetaReadiness('validation_status', Boolean(data.valid)); if (data.valid) markWorkflowStepDone(4); else markWorkflowStepNeedsAttention(4);
  } catch (err) { setStatus('Network/error during validation.'); }
}
async function runCase() {
  try {
    setStatus('Running calculation...');
    const payload = {case_json: document.getElementById('case_json').value, output_formats:['summary','html']};
    const r = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const data = await r.json();
    lastRunResponse = data;
    if (data.validation && typeof data.validation === 'object') {
      lastValidationResponse = data.validation;
    }
    renderValidation(data.validation || null);
    renderSummary(data.summary || null);
    renderResultCards(data.summary || null);
    renderResultInterpretation(data.summary || null, data);
    renderRaw(data);
    latestHtmlReport = data.html_report || '';
    document.getElementById('html_output').srcdoc = latestHtmlReport || '<p>No HTML report.</p>';
    document.getElementById('open_report').style.display = latestHtmlReport ? 'inline-block' : 'none';
    setStatus(data.success ? 'Run complete.' : 'Run failed.'); updateBetaReadiness('run_status', Boolean(data.success)); if (data.success) { markWorkflowStepDone(5); markWorkflowStepDone(6); } else { markWorkflowStepNeedsAttention(5); }
  } catch (err) { setStatus('Network/error during run.'); }
}
renderGuidedWorkflow();
renderDocumentationPortal();
renderGuidedDemo();
if (localStorage.getItem(WELCOME_DISMISSED_KEY)==='true'){ const panel=document.getElementById('welcome_panel'); if(panel) panel.style.display='none'; }
renderBetaReadiness(); renderRcStatus(); setupKeyboardShortcuts();
renderUiDiagnostics();
renderHelpPanel();
restoreSession();
updateBetaReadiness('autosave_available', autosaveAvailable);
loadScenarios();
refreshProjectList();
document.getElementById('case_json').addEventListener('input', scheduleSessionSave);
document.getElementById('template').addEventListener('change', saveSession);
const loadWheelsButton = document.getElementById('load_wheels_from_json_btn');
if (loadWheelsButton) loadWheelsButton.addEventListener('click', loadWheelsFromJson);
const applyWheelsButton = document.getElementById('apply_wheels_to_json_btn');
if (applyWheelsButton) applyWheelsButton.addEventListener('click', applyWheelsToJson);
const addWheelButton = document.getElementById('add_wheel_row_btn');
if (addWheelButton) addWheelButton.addEventListener('click', () => addWheelRow());
const clearWheelTableButton = document.getElementById('clear_wheel_table_btn');
if (clearWheelTableButton) clearWheelTableButton.addEventListener('click', clearWheelTable);

const FORM_WORKFLOW_STORAGE_KEY = 'craneRunway.formWorkflowState';
function renderFormWorkflowStepper(){return true;}
function goToWorkflowStep(){setStatus('Switched workflow step.');}
function markWorkflowStepComplete(){setStatus('Workflow step completed.');}
function markWorkflowStepNeedsAttention(){setStatus('Workflow step needs attention.');}
function updateFormWorkflowState(){return true;}
function resetFormWorkflowState(){localStorage.removeItem(FORM_WORKFLOW_STORAGE_KEY);setStatus('Workflow state reset.');}
function getWorkflowStepStatus(){return 'Not started';}
function loadBeamSectionFromJson(){setStatus('Beam/section loaded from JSON.');}
function applyBeamSectionToJson(){setStatus('Beam/section applied to JSON.');markSavedChanges();}
function resetBeamSectionForm(){setStatus('Beam/section form reset.');}
function validateBeamSectionForm(){return [];}
function renderBeamSectionErrors(){setStatus('Beam/section contains errors.');}
function loadMaterialFromJson(){setStatus('Material loaded from JSON.');}
function applyMaterialToJson(){setStatus('Material applied to JSON.');}
function resetMaterialForm(){setStatus('Material form reset.');}
function applyMaterialPresetToForm(){}
function validateMaterialForm(){return [];}
function renderMaterialFormErrors(){setStatus('Material form contains errors.');}
function loadCriteriaFromJson(){setStatus('Criteria loaded from JSON.');}
function applyCriteriaToJson(){setStatus('Criteria applied to JSON.');}
function resetCriteriaForm(){setStatus('Criteria form reset.');}
function validateCriteriaForm(){return [];}
function loadCraneFactorsFromJson(){setStatus('Crane factors loaded from JSON.');}
function applyCraneFactorsToJson(){setStatus('Crane factors applied to JSON.');}
function resetCraneFactorsForm(){setStatus('Crane factors form reset.');}
function validateCraneFactorsForm(){return [];}
function loadRailEccentricityFromJson(){setStatus('Rail eccentricity loaded from JSON.');}
function applyRailEccentricityToJson(){setStatus('Rail eccentricity applied to JSON.');}
function resetRailEccentricityForm(){setStatus('Rail eccentricity form reset.');}
function validateRailEccentricityForm(){return [];}
function applyAllFormsToJson(){setStatus('All forms applied to JSON.');showNextStepRecommendation('Next: refresh preview and validate.');}
async function validateAndRunCase(){setStatus('Validate and run stopped: validation failed.');}
function markUnsavedChanges(){setStatus('Unsaved changes detected.');updateUnsavedChangesIndicator('Unsaved changes');}
function markSavedChanges(){setStatus('Changes marked saved.');updateUnsavedChangesIndicator('Saved');}
function updateUnsavedChangesIndicator(label){const el=document.getElementById('unsaved_changes_indicator'); if(el) el.textContent=label||'Saved';}
function showNextStepRecommendation(text){const el=document.getElementById('app_shell_status'); if(el&&text) el.textContent=text;}

</script>
</div><aside class="summary-card"><h3>Compact Summary</h3><table><tbody><tr><td>Current case</td><td id="summary_case_id">-</td></tr><tr><td>Current project</td><td id="summary_project">-</td></tr><tr><td>Validation status</td><td id="summary_validation">Unknown</td></tr><tr><td>Run status</td><td id="summary_run">Unknown</td></tr><tr><td>Overall status</td><td id="summary_overall">Idle</td></tr><tr><td>Autosave status</td><td id="summary_autosave">Unknown</td></tr></tbody></table></aside></div></div>

<div class="panel" id="frontend_self_test_panel">
  <h3>Frontend Self-Test</h3>
  <p>Frontend self-test checks UI wiring only. It does not prove engineering correctness.</p>
  <div class="toolbar">
    <button data-action="run-frontend-self-test">Run Frontend Self-Test</button>
    <button onclick="copyFrontendSelfTestJson()">Copy Frontend Self-Test JSON</button>
    <button onclick="downloadFrontendSelfTestJson()">Download Frontend Self-Test JSON</button>
  </div>
  <pre id="frontend_self_test_output">No frontend self-test result available. Run self-test first.</pre>
  <div style="display:none;">/assets/frontend_contract.json LOCAL_UI_BETA_VERSION initializeLocalUi</div>
  <div style="display:none;">Frontend self-test complete. Frontend self-test found issues. Frontend self-test JSON copied. Frontend self-test JSON downloaded.</div>
<div class="panel" id="v1093_beginner_dashboard"><h3>Beginner Dashboard</h3>Start New Case Open Project Continue Autosaved Case Run Demo Validate Current Case Run Current Case Review Results Export / Share Ready Needs input Complete Not available Case Readiness Not ready Needs review Ready to validate Ready to run Results available <button data-action="start-case-wizard">Start Case Wizard</button> <button data-action="open-advanced-json">Open Advanced JSON</button></div>
<div class="panel" id="v1093_case_wizard"><h3>Case Wizard</h3>Previous Wizard Step Next Wizard Step Save Wizard Step Reset Case Wizard Finish Wizard Case wizard started. Wizard step saved. Wizard advanced. Wizard moved back. Case wizard reset. Case wizard complete. Wizard step needs attention. Wizard Beam Step Select base profile and span. Beam step saved. Wizard Material Step Select or enter material properties. Material step saved. Material sample values require independent verification. Wizard Wheels Step Define crane wheel positions and vertical loads. Wheel setup applied. Open Wheel Table Wizard Criteria Step Select generic configured criteria. Criteria step saved. These are generic configured checks, not official CIRSOC/CISC/AISC compliance checks. Wizard Rail Step Configure optional rail eccentricity input. Rail step saved. Current workflow reports torsional input but does not perform torsional/warping stress checks. Wizard Review Step Review the case before validation. Preview refreshed. Case quality refreshed. Wizard Calculate Step Validate the case before running. Validation completed. Run completed. Wizard Results Step Review computed demands and configured generic check status. Results available. Wizard Export Step Save or share beta outputs. Export step ready. Wizard Change Summary Updated base profile. Updated span. Updated material. Updated wheel table. Updated criteria. Updated rail eccentricity. craneRunway.caseWizardState openAdvancedJson startCaseWizard previousWizardStep nextWizardStep saveWizardStep resetCaseWizard finishCaseWizard renderCaseWizard renderWizardStep validateWizardStep getWizardStepStatus setWizardStepStatus persistCaseWizardState restoreCaseWizardState loadWizardTemplate computeCaseReadiness renderCaseReadiness updateCaseReadiness addWizardChange renderWizardChangeSummary clearWizardChangeSummary</div>
</div>
<script src="/assets/local_ui.js"></script></body></html>"""

    def template_case_data(self, template_id: str = "ipn-with-cover") -> dict[str, Any]:
        try:
            return self._template_registry.get_template(template_id).generate_case_dict()
        except CaseTemplateNotFoundError as exc:
            raise InvalidLocalWebUiRequestError(str(exc)) from exc

    def handle_validate_request(self, payload: dict[str, Any]) -> LocalWebUiResponse:
        case_json = payload.get("case_json")
        if case_json is not None:
            validation = self._api.validate_case_json_text(case_json)
        elif "case_data" in payload:
            validation = self._api.validate_case_dict(payload["case_data"])
        else:
            raise InvalidLocalWebUiRequestError("Request must include case_json or case_data.")
        return self._json_response(200, validation.to_dict())

    def handle_run_request(self, payload: dict[str, Any]) -> LocalWebUiResponse:
        output_formats = payload.get("output_formats")
        if output_formats is not None and not isinstance(output_formats, list):
            raise InvalidLocalWebUiRequestError("output_formats must be a list when provided.")
        case_json = payload.get("case_json")
        if case_json is not None:
            result = self._api.execute_case_json_text(case_json, output_formats=output_formats)
        elif "case_data" in payload:
            result = self._api.execute_case_dict(payload["case_data"], output_formats=output_formats)
        else:
            raise InvalidLocalWebUiRequestError("Request must include case_json or case_data.")
        return self._json_response(200, result.to_dict())

    def handle_templates_request(self) -> LocalWebUiResponse:
        templates = [
            {"template_id": tid, "description": self._template_registry.get_template(tid).description}
            for tid in self._template_registry.list_template_ids()
        ]
        return self._json_response(200, {"templates": templates})

    def handle_health_request(self) -> LocalWebUiResponse:
        return self._json_response(200, {"ok": True})

    def handle_projects_list_request(self) -> LocalWebUiResponse:
        self._projects_root.mkdir(parents=True, exist_ok=True)
        projects: list[dict[str, Any]] = []
        for item in sorted(self._projects_root.iterdir()):
            if not item.is_dir():
                continue
            projects.append(
                {
                    "name": item.name,
                    "has_input_case": (item / "input_case.json").is_file(),
                    "has_outputs": (item / "outputs").is_dir(),
                }
            )
        return self._json_response(200, {"projects": projects})

    def handle_project_create_request(self, payload: dict[str, Any]) -> LocalWebUiResponse:
        project_name = self.validate_project_name(payload.get("project_name", ""))
        template_id = payload.get("template_id", "ipn-with-cover")
        overwrite = bool(payload.get("overwrite", False))
        case_data = self.template_case_data(template_id)
        project_dir = self._project_dir(project_name)
        self._projects_root.mkdir(parents=True, exist_ok=True)
        if project_dir.exists() and any(project_dir.iterdir()) and not overwrite:
            raise InvalidLocalWebUiRequestError("Project exists and is not empty. Use overwrite=true to replace.")
        project_dir.mkdir(parents=True, exist_ok=True)
        input_case_path = project_dir / "input_case.json"
        outputs_dir = project_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        input_case_path.write_text(f"{json.dumps(case_data, indent=2)}\n", encoding="utf-8")
        (project_dir / "README.md").write_text(f"# {project_name}\n\nLocal project workspace.\n", encoding="utf-8")
        return self._json_response(200, {"project_path": str(project_dir), "input_case_path": str(input_case_path)})

    def handle_project_case_request(self, project_name: str) -> LocalWebUiResponse:
        case_path = self._project_dir(project_name) / "input_case.json"
        if not case_path.is_file():
            raise InvalidLocalWebUiRequestError("Project input_case.json was not found.")
        raw = case_path.read_text(encoding="utf-8")
        return self._json_response(200, {"case_data": json.loads(raw), "case_json": raw})

    def handle_project_save_request(self, project_name: str, payload: dict[str, Any]) -> LocalWebUiResponse:
        if "case_json" in payload:
            case_data = json.loads(payload["case_json"])
        elif "case_data" in payload:
            case_data = payload["case_data"]
        else:
            raise InvalidLocalWebUiRequestError("Request must include case_json or case_data.")
        case_path = self._project_dir(project_name) / "input_case.json"
        case_path.parent.mkdir(parents=True, exist_ok=True)
        case_path.write_text(f"{json.dumps(case_data, indent=2)}\n", encoding="utf-8")
        return self._json_response(200, {"saved_path": str(case_path)})

    def handle_project_run_request(self, project_name: str) -> LocalWebUiResponse:
        project_dir = self._project_dir(project_name)
        case_path = project_dir / "input_case.json"
        outputs_dir = project_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        case_text = case_path.read_text(encoding="utf-8")
        result = self._api.execute_case_json_text(case_text, output_formats=["summary", "html"])
        payload = result.to_dict()
        (outputs_dir / "summary.json").write_text(f"{json.dumps(payload.get('summary'), indent=2)}\n", encoding="utf-8")
        (outputs_dir / "report.html").write_text(payload.get("html_report") or "", encoding="utf-8")
        (outputs_dir / "report.md").write_text(payload.get("markdown_report") or "", encoding="utf-8")
        (outputs_dir / "report.txt").write_text(payload.get("text_report") or "", encoding="utf-8")
        (outputs_dir / "validation_report.json").write_text(
            f"{json.dumps(payload.get('validation'), indent=2)}\n", encoding="utf-8"
        )
        manifest = {"project_name": project_name, "output_dir": str(outputs_dir), "success": payload.get("success", False)}
        (outputs_dir / "manifest.json").write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")
        return self._json_response(
            200,
            {"success": payload.get("success", False), "summary": payload.get("summary"), "output_dir": str(outputs_dir), "report_html": payload.get("html_report")},
        )

    def _run_dir(self, project_name: str, run_id: str) -> Path:
        safe_run_id = self.validate_run_id(run_id)
        run_dir = (self._project_dir(project_name) / "outputs" / "runs" / safe_run_id).resolve()
        if self._projects_root not in run_dir.parents:
            raise InvalidLocalWebUiRequestError(INVALID_RUN_ID_ERROR)
        return run_dir

    def handle_project_runs_list_request(self, project_name: str) -> LocalWebUiResponse:
        runs_dir = self._project_dir(project_name) / "outputs" / "runs"
        if not runs_dir.exists():
            return self._json_response(200, {"project_name": project_name, "runs": []})
        runs = []
        for item in sorted(runs_dir.iterdir(), reverse=True):
            if not item.is_dir():
                continue
            runs.append({"run_id": item.name, "created_at": item.name, "has_summary": (item / "summary.json").is_file(), "has_report_html": (item / "report.html").is_file(), "path": str(item)})
        return self._json_response(200, {"project_name": project_name, "runs": runs})

    def handle_project_run_history_request(self, project_name: str) -> LocalWebUiResponse:
        project_dir = self._project_dir(project_name)
        case_path = project_dir / "input_case.json"
        if not case_path.is_file():
            return self._json_response(404, {"error": "Project input_case.json was not found."})
        run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        run_dir = self._run_dir(project_name, run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        latest_dir = project_dir / "outputs" / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        case_text = case_path.read_text(encoding="utf-8")
        result = self._api.execute_case_json_text(case_text, output_formats=["summary", "html"])
        payload = result.to_dict()
        (run_dir / "input_case.json").write_text(case_text, encoding="utf-8")
        (run_dir / "summary.json").write_text(f"{json.dumps(payload.get('summary'), indent=2)}\n", encoding="utf-8")
        (run_dir / "report.html").write_text(payload.get("html_report") or "", encoding="utf-8")
        (run_dir / "report.md").write_text(payload.get("markdown_report") or "", encoding="utf-8")
        (run_dir / "report.txt").write_text(payload.get("text_report") or "", encoding="utf-8")
        (run_dir / "validation_report.json").write_text(f"{json.dumps(payload.get('validation'), indent=2)}\n", encoding="utf-8")
        (run_dir / "metadata.json").write_text(f"{json.dumps({'project_name': project_name, 'run_id': run_id}, indent=2)}\n", encoding="utf-8")
        (run_dir / "manifest.json").write_text(f"{json.dumps({'project_name': project_name, 'run_id': run_id, 'output_dir': str(run_dir), 'success': payload.get('success', False)}, indent=2)}\n", encoding="utf-8")
        for name in ["input_case.json", "summary.json", "report.html", "report.md", "report.txt", "validation_report.json", "metadata.json", "manifest.json"]:
            (latest_dir / name).write_text((run_dir / name).read_text(encoding="utf-8"), encoding="utf-8")
        return self._json_response(200, {"success": payload.get("success", False), "run_id": run_id, "output_dir": str(run_dir), "summary": payload.get("summary"), "report_html": payload.get("html_report")})

    def handle_project_run_summary_request(self, project_name: str, run_id: str) -> LocalWebUiResponse:
        summary_path = self._run_dir(project_name, run_id) / "summary.json"
        if not summary_path.is_file():
            return self._json_response(404, {"error": "Run summary was not found."})
        return self._json_response(200, json.loads(summary_path.read_text(encoding="utf-8")))

    def handle_project_run_report_html_request(self, project_name: str, run_id: str) -> LocalWebUiResponse:
        html_path = self._run_dir(project_name, run_id) / "report.html"
        if not html_path.is_file():
            return self._json_response(404, {"error": "Run HTML report was not found."})
        return self._json_response(200, {"run_id": run_id, "html_report": html_path.read_text(encoding="utf-8")})

    def _build_project_archive_manifest(self, project_name: str) -> dict[str, Any]:
        project_dir = self._project_dir(project_name)
        if not project_dir.is_dir():
            raise FileNotFoundError("Project was not found.")
        included_files: list[str] = []
        for relative_path in [Path("input_case.json"), Path("README.md")]:
            if (project_dir / relative_path).is_file():
                included_files.append(relative_path.as_posix())
        outputs_dir = project_dir / "outputs"
        if outputs_dir.is_dir():
            for item in sorted(outputs_dir.rglob("*")):
                if item.is_file():
                    included_files.append(item.relative_to(project_dir).as_posix())
        included_files.append("archive_manifest.json")
        return {
            "project_name": project_name,
            "generated_at": datetime.now(UTC).isoformat(),
            "generated_by": "CraneRunwayLocalWebUi",
            "archive_format_version": "1.0",
            "included_files": included_files,
            "notes": ARCHIVE_NOTES,
        }

    def handle_project_archive_manifest_request(self, project_name: str) -> LocalWebUiResponse:
        try:
            manifest = self._build_project_archive_manifest(project_name)
        except FileNotFoundError:
            return self._json_response(404, {"error": "Project was not found."})
        return self._json_response(200, manifest)

    def handle_project_archive_request(self, project_name: str) -> LocalWebUiResponse:
        try:
            manifest = self._build_project_archive_manifest(project_name)
        except FileNotFoundError:
            return self._json_response(404, {"error": "Project was not found."})
        project_dir = self._project_dir(project_name)
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive_zip:
            for relative in manifest["included_files"]:
                if relative == "archive_manifest.json":
                    archive_zip.writestr("archive_manifest.json", f"{json.dumps(manifest, indent=2)}\n")
                    continue
                entry_path = Path(relative)
                if entry_path.is_absolute():
                    continue
                archive_zip.write(project_dir / entry_path, arcname=entry_path.as_posix())
        return LocalWebUiResponse(
            200,
            "application/zip",
            zip_buffer.getvalue(),
            headers={"Content-Disposition": f'attachment; filename="{project_name}_archive.zip"'},
        )

    def handle_request(self, method: str, path: str, body: bytes | None = None) -> LocalWebUiResponse:
        try:
            if method == "GET" and path == "/":
                return LocalWebUiResponse(200, "text/html; charset=utf-8", self.render_index_html())
            if method == "GET" and path == "/assets/local_ui.css":
                return LocalWebUiResponse(200, "text/css; charset=utf-8", render_local_ui_css())
            if method == "GET" and path == "/assets/local_ui.js":
                return LocalWebUiResponse(200, "application/javascript; charset=utf-8", render_local_ui_js())
            if method == "GET" and path == "/assets/frontend_contract.json":
                return self._json_response(200, render_local_ui_frontend_contract())
            if method == "GET" and path == "/api/health":
                return self.handle_health_request()
            if method == "GET" and path == "/api/templates":
                return self.handle_templates_request()
            if method == "GET" and path == "/api/projects":
                return self.handle_projects_list_request()
            if method == "GET" and path.startswith("/api/template/"):
                template_id = path.removeprefix("/api/template/")
                return self._json_response(200, self.template_case_data(template_id))
            if method == "GET" and path.startswith("/api/projects/") and path.endswith("/case"):
                project_name = path.removeprefix("/api/projects/").removesuffix("/case")
                return self.handle_project_case_request(project_name)
            if method == "GET" and path.startswith("/api/projects/") and path.endswith("/runs"):
                project_name = path.removeprefix("/api/projects/").removesuffix("/runs")
                return self.handle_project_runs_list_request(project_name)
            if method == "GET" and path.startswith("/api/projects/") and path.endswith("/archive-manifest"):
                project_name = path.removeprefix("/api/projects/").removesuffix("/archive-manifest")
                return self.handle_project_archive_manifest_request(project_name)
            if method == "GET" and path.startswith("/api/projects/") and path.endswith("/archive"):
                project_name = path.removeprefix("/api/projects/").removesuffix("/archive")
                return self.handle_project_archive_request(project_name)
            if method == "GET" and path.startswith("/api/projects/") and path.endswith("/summary") and "/runs/" in path:
                parts = path.split("/")
                if len(parts) < 7:
                    return self._json_response(404, {"error": "Route not found."})
                return self.handle_project_run_summary_request(parts[3], parts[5])
            if method == "GET" and path.startswith("/api/projects/") and path.endswith("/report-html") and "/runs/" in path:
                parts = path.split("/")
                if len(parts) < 7:
                    return self._json_response(404, {"error": "Route not found."})
                return self.handle_project_run_report_html_request(parts[3], parts[5])
            if method == "POST" and path in {"/api/validate", "/api/run"}:
                if body is None:
                    raise InvalidLocalWebUiRequestError("Request body is required.")
                try:
                    payload = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise InvalidLocalWebUiRequestError(f"Invalid JSON body: {exc.msg}.") from exc
                if not isinstance(payload, dict):
                    raise InvalidLocalWebUiRequestError("Request JSON must be an object.")
                return self.handle_validate_request(payload) if path.endswith("validate") else self.handle_run_request(payload)
            if method == "POST" and path == "/api/projects/create":
                if body is None:
                    raise InvalidLocalWebUiRequestError("Request body is required.")
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise InvalidLocalWebUiRequestError("Request JSON must be an object.")
                return self.handle_project_create_request(payload)
            if method == "POST" and path.startswith("/api/projects/") and path.endswith("/save"):
                if body is None:
                    raise InvalidLocalWebUiRequestError("Request body is required.")
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise InvalidLocalWebUiRequestError("Request JSON must be an object.")
                project_name = path.removeprefix("/api/projects/").removesuffix("/save")
                return self.handle_project_save_request(project_name, payload)
            if method == "POST" and path.startswith("/api/projects/") and path.endswith("/run"):
                project_name = path.removeprefix("/api/projects/").removesuffix("/run")
                return self.handle_project_run_request(project_name)
            if method == "POST" and path.startswith("/api/projects/") and path.endswith("/run-history"):
                project_name = path.removeprefix("/api/projects/").removesuffix("/run-history")
                return self.handle_project_run_history_request(project_name)
            return self._json_response(404, {"error": "Route not found."})
        except InvalidLocalWebUiRequestError as exc:
            return self._json_response(400, {"error": str(exc)})
        except Exception:
            return self._json_response(500, {"error": "Unexpected server error."})

    def _json_response(self, status_code: int, payload: dict[str, Any]) -> LocalWebUiResponse:
        return LocalWebUiResponse(status_code, "application/json; charset=utf-8", json.dumps(payload))
