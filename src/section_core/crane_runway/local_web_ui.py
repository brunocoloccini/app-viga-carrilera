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
    <button onclick=\"downloadHtmlReport()\">Download Report HTML</button>
    <button onclick=\"downloadAllPackageFiles()\">Download All Package Files</button>
  </div>
</div>
<div id=\"status\" class=\"status\">Ready.</div>
<div class=\"page\">
  <div class=\"left-col\">
    <div class=\"panel\">
      <h3>JSON Editor</h3>
      <textarea id=\"case_json\"></textarea>
    </div>
  </div>
  <div class=\"right-col\">
  <div class=\"panel\"><h3>Help / Workflow</h3><div id=\"help_panel\"></div></div>
  <div class=\"panel\"><h3>Case Outline</h3><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"refreshCaseOutline()\">Refresh Case Outline</button></div><div id=\"case_outline_output\"></div></div>
  <div class=\"panel\"><h3>Validation</h3><div class=\"toolbar\" style=\"margin-top:0;\"><button onclick=\"copyErrorList()\">Copy Error List</button></div><div id=\"validation_output\"></div></div>
  <div class=\"panel\"><h3>Summary</h3><div id=\"result_cards\"></div><div id=\"summary_output\"></div></div>
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
  setStatus('Output cleared.');
}
function clearJson() { document.getElementById('case_json').value = ''; setStatus('JSON editor cleared.'); }

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
    setStatus('Imported JSON file: ' + file.name);
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
    const find = path !== 'N/A' ? '<button class=\"small-btn\" onclick=\"findJsonPath(\\'' + escapeHtml(String(path).replaceAll('\\\\', '\\\\\\\\').replaceAll('\'', '\\\\\'')) + '\\')\">Find Path</button>' : '';
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
  document.getElementById('help_panel').innerHTML = '<ol><li>Load a template or import JSON.</li><li>Edit JSON.</li><li>Click Validate.</li><li>Fix validation errors.</li><li>Click Run.</li><li>Review Summary and HTML Report.</li><li>Download JSON / Summary / Report.</li></ol><p><strong>Warnings:</strong> Local beta tool; Results require engineering review; Generic checks only; no official CIRSOC/CISC/AISC checks; no fatigue; no torsional/warping stress; no LTB.</p>';
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
    setStatus('Template loaded: ' + id);
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
    renderRaw(data);
    latestHtmlReport = data.html_report || '';
    document.getElementById('html_output').srcdoc = latestHtmlReport || '<p>No HTML report.</p>';
    document.getElementById('open_report').style.display = latestHtmlReport ? 'inline-block' : 'none';
    setStatus(data.success ? 'Run complete.' : 'Run failed.');
  } catch (err) { setStatus('Network/error during run.'); }
}
renderHelpPanel();
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
