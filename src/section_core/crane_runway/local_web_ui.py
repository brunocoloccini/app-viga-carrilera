"""Minimal local web UI adapter for crane runway beta workflows (V1-059)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any

from .api_service import CraneRunwayApiService
from .case_templates import (
    CaseTemplateNotFoundError,
    build_default_crane_runway_case_template_registry,
)


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


class CraneRunwayLocalWebUi:
    """Route handler for local crane runway browser workflows."""

    def __init__(self) -> None:
        self._api = CraneRunwayApiService()
        self._template_registry = build_default_crane_runway_case_template_registry()

    def render_index_html(self) -> str:
        return """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"/><title>Crane Runway Local UI</title>
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
.panel { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.8rem; }
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
</style>
</head>
<body>
<h1>Crane Runway Local UI</h1>
<p class=\"warning\">Local beta tool. Results require engineering review.</p>
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
<div class="panel" style="margin-top: 1rem;">
  <h3>Common Inputs</h3>
  <p style="margin-top:0;">Common Inputs edits the JSON below. Review generated JSON before running.</p>
  <p style="margin-top:0.2rem;">Advanced fields remain editable directly in JSON.</p>
  <p style="margin-top:0.2rem;"><strong>For more than two wheels, use Wheel Table Editor.</strong></p>
  <div class="toolbar" style="margin-top:0;">
    <button onclick="loadCommonInputsFromJson()">Load Form From JSON</button>
    <button onclick="validateCommonInputsOnly()">Validate Common Inputs</button>
    <button onclick="applyCommonInputsToJson()">Apply Form To JSON</button>
    <button onclick="resetCommonInputs()">Reset Form</button>
  </div>
  <table><tbody><tr><td>Case ID</td><td><input id="common_case_id"/></td><td>Description</td><td><input id="common_description"/></td></tr>
  <tr><td>Base Shape ID</td><td><input id="common_base_shape_id"/></td><td>Cover Plate Enabled</td><td><input id="common_cover_plate_enabled" type="checkbox"/></td></tr>
  <tr><td>Cover Plate Width</td><td><input id="common_cover_plate_width"/><select id="common_cover_plate_width_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Cover Plate Thickness</td><td><input id="common_cover_plate_thickness"/><select id="common_cover_plate_thickness_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr>
  <tr><td>Cover Plate Weld Size</td><td><input id="common_cover_plate_weld_size"/><select id="common_cover_plate_weld_size_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Material ID</td><td><input id="common_material_id"/></td></tr>
  <tr><td>Fy</td><td><input id="common_fy"/><select id="common_fy_unit"><option>MPa</option><option>ksi</option><option>psi</option></select></td><td>Fu</td><td><input id="common_fu"/><select id="common_fu_unit"><option>MPa</option><option>ksi</option><option>psi</option></select></td></tr><tr><td>E</td><td><input id="common_e"/><select id="common_e_unit"><option>MPa</option><option>ksi</option><option>psi</option></select></td><td>Span</td><td><input id="common_span"/><select id="common_span_unit"><option>m</option><option>mm</option><option>ft</option></select></td></tr>
  <tr><td>Movement Step</td><td><input id="common_movement_step"/><select id="common_movement_step_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Station Step</td><td><input id="common_station_step"/><select id="common_station_step_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr><tr><td>Crane ID</td><td><input id="common_crane_id"/></td><td>Vertical Impact Factor</td><td><input id="common_vertical_impact_factor"/></td></tr>
  <tr><td>Lateral Force Factor</td><td><input id="common_lateral_force_factor"/></td><td>Wheel 1 Load</td><td><input id="common_wheel_1_load"/><select id="common_wheel_1_load_unit"><option>kN</option><option>N</option><option>kip</option></select></td></tr><tr><td>Wheel 2 Load</td><td><input id="common_wheel_2_load"/><select id="common_wheel_2_load_unit"><option>kN</option><option>N</option><option>kip</option></select></td><td>Wheel Spacing</td><td><input id="common_wheel_spacing"/><select id="common_wheel_spacing_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr>
  <tr><td>Rail Eccentricity Enabled</td><td><input id="common_rail_eccentricity_enabled" type="checkbox"/></td><td>Vertical Eccentricity Y</td><td><input id="common_vertical_eccentricity_y"/><select id="common_vertical_eccentricity_y_unit"><option>mm</option><option>cm</option><option>in</option></select></td></tr><tr><td>Lateral Load Height Z</td><td><input id="common_lateral_load_height_z"/><select id="common_lateral_load_height_z_unit"><option>mm</option><option>cm</option><option>in</option></select></td><td>Deflection Preset</td><td><input id="common_deflection_preset"/></td></tr><tr><td>Stress Preset</td><td><input id="common_stress_preset"/></td><td></td><td></td></tr></tbody></table>
  <h4>Common Inputs Errors</h4><div id="common_inputs_errors">No common input errors.</div>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>Wheel Table Editor</h3>
  <div class="toolbar" style="margin-top:0;">
    <button id="load_wheels_from_json_btn">Load Wheels From JSON</button>
    <button id="apply_wheels_to_json_btn">Apply Wheels To JSON</button>
    <button id="add_wheel_row_btn">Add Wheel</button>
    <button id="clear_wheel_table_btn">Clear Wheel Table</button>
  </div>
  <table><thead><tr><th>Wheel ID</th><th>Position X</th><th>Position Unit</th><th>Vertical Force</th><th>Force Unit</th><th>Remove</th></tr></thead><tbody id="wheel_table_body"></tbody></table>
  <h4>Wheel Table Errors</h4><div id="wheel_table_errors">No wheel table errors.</div>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>Visual Preview</h3>
  <div class="toolbar" style="margin-top:0;"><button onclick="refreshVisualPreview()">Refresh Visual Preview</button></div>
  <p style="margin-top:0.35rem;color:#4b5563;">Preview is schematic only and not to scale.</p>
  <h4>Beam Preview</h4><div id="beam_preview_output"></div>
  <h4>Section Preview</h4><div id="section_preview_output"></div>
  <h4>Preview Summary</h4><div id="preview_summary_output"></div>
</div>
<div class="panel" style="margin-top: 1rem;">
  <h3>Scenario Comparison</h3>
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
<div id=\"status\" class=\"status\">Ready.</div>
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
  <div class=\"panel\"><h3>Validation</h3><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"copyErrorList()\">Copy Error List</button></div><div id=\"validation_output\"></div></div>
  <div class=\"panel\"><h3>Summary</h3><div id=\"result_cards\"></div><div id=\"summary_output\"></div></div>
  <div class=\"panel\"><h3>Result Interpretation</h3><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"copyInterpretation()\">Copy Interpretation</button></div><div id=\"interpretation_output\"><p>Run a case to see result interpretation.</p></div></div>
  <div class=\"panel\">
    <h3>HTML Report</h3>
    <button id=\"open_report\" onclick=\"openReportInNewTab()\" style=\"display:none; margin-bottom: 0.6rem;\">Open report in new tab</button>
    <iframe id=\"html_output\" style=\"width:100%;height:380px;border:1px solid #d1d5db;border-radius:6px;\"></iframe>
  </div>
  <div class=\"panel\"><h3>Raw Response</h3><pre id=\"raw_output\"></pre></div>
  </div>
</div>
<script>
let latestHtmlReport = '';
let lastValidationResponse = null;
let lastRunResponse = null;
let lastRawResponse = null;
let lastScenarioComparisonResults = null;
const scenarioStorageKey = 'craneRunway.scenarios';
const autosaveStorageKeys = {
  caseJson: 'craneRunway.caseJson',
  selectedTemplate: 'craneRunway.selectedTemplate',
  lastSavedAt: 'craneRunway.lastSavedAt'
};
let autosaveAvailable = true;
let autosaveTimer = null;
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
function setStatus(msg) { document.getElementById('status').textContent = msg; }
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
function refreshVisualPreview() { let caseData; try { caseData = JSON.parse(getCurrentCaseJsonText()); } catch (err) { setStatus('Cannot refresh visual preview: invalid JSON.'); return; } renderBeamPreview(caseData); renderSectionPreview(caseData); renderPreviewSummary(caseData); setStatus('Visual preview refreshed.'); }

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
    setStatus('Imported JSON file: ' + file.name);
    if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
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
  setStatus('Summary downloaded.');
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
  setStatus('Package metadata downloaded.');
}
function downloadPackageCaseJson() {
  const artifact = buildPackageArtifacts()['case.json'];
  if (!artifact.available) { setStatus(artifact.reason); return; }
  downloadText('case.json', artifact.content, artifact.contentType);
  setStatus('Case JSON downloaded.');
}
function downloadValidationResponse() {
  const artifact = buildPackageArtifacts()['validation_response.json'];
  if (!artifact.available) { setStatus(artifact.reason); return; }
  downloadText('validation_response.json', artifact.content, artifact.contentType);
  setStatus('Validation response downloaded.');
}
function downloadRunResponse() {
  const artifact = buildPackageArtifacts()['run_response.json'];
  if (!artifact.available) { setStatus(artifact.reason); return; }
  downloadText('run_response.json', artifact.content, artifact.contentType);
  setStatus('Run response downloaded.');
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
  setStatus('HTML report downloaded.');
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
  setStatus('Common inputs applied to JSON.');
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
  if (wheels.length === 0) { setWheelRows([]); setStatus('No wheels found in JSON.'); return; }
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
  if (typeof refreshCaseOutline === 'function') refreshCaseOutline();
  setStatus('Wheel table applied to JSON.');
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
  let html = '<h4>Result Cards</h4><div class=\"result-cards\">';
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
  setStatus('Scenario comparison complete.');
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
async function loadTemplate() {
  try {
    const id = document.getElementById('template').value;
    const r = await fetch('/api/template/' + encodeURIComponent(id));
    const data = await r.json();
    if (!r.ok) { setStatus('Failed to load template: ' + (data.error || 'unknown error')); return; }
    document.getElementById('case_json').value = JSON.stringify(data, null, 2);
    saveSession();
    setStatus('Template loaded: ' + id);
    if (typeof refreshVisualPreview === 'function') refreshVisualPreview();
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
    setStatus(data.valid ? 'Validation complete.' : 'Validation returned errors.');
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
    setStatus(data.success ? 'Run complete.' : 'Run failed.');
  } catch (err) { setStatus('Network/error during run.'); }
}
renderHelpPanel();
restoreSession();
loadScenarios();
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
</script>
</body></html>"""

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

    def handle_request(self, method: str, path: str, body: bytes | None = None) -> LocalWebUiResponse:
        try:
            if method == "GET" and path == "/":
                return LocalWebUiResponse(200, "text/html; charset=utf-8", self.render_index_html())
            if method == "GET" and path == "/api/health":
                return self.handle_health_request()
            if method == "GET" and path == "/api/templates":
                return self.handle_templates_request()
            if method == "GET" and path.startswith("/api/template/"):
                template_id = path.removeprefix("/api/template/")
                return self._json_response(200, self.template_case_data(template_id))
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
            return self._json_response(404, {"error": "Route not found."})
        except InvalidLocalWebUiRequestError as exc:
            return self._json_response(400, {"error": str(exc)})
        except Exception:
            return self._json_response(500, {"error": "Unexpected server error."})

    def _json_response(self, status_code: int, payload: dict[str, Any]) -> LocalWebUiResponse:
        return LocalWebUiResponse(status_code, "application/json; charset=utf-8", json.dumps(payload))
