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
.toolbar { margin-top: 0.8rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
button { padding: 0.45rem 0.7rem; border: 1px solid #d1d5db; border-radius: 6px; background: white; cursor: pointer; }
button:hover { background: #f3f4f6; }
select, textarea { border: 1px solid #d1d5db; border-radius: 6px; }
textarea { width: 100%; min-height: 300px; font-family: Consolas, monospace; padding: 0.6rem; box-sizing: border-box; }
.status { margin-top: 0.8rem; padding: 0.6rem; background: #eff6ff; border: 1px solid #93c5fd; border-radius: 6px; }
.grid { display: grid; grid-template-columns: 1fr; gap: 1rem; margin-top: 1rem; }
.panel { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.8rem; }
.panel h3 { margin-top: 0; }
pre { white-space: pre-wrap; word-break: break-word; background: #f9fafb; border: 1px solid #e5e7eb; padding: 0.6rem; border-radius: 6px; min-height: 80px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #e5e7eb; padding: 0.4rem; text-align: left; font-size: 0.92rem; }
th { width: 40%; background: #f9fafb; }
.pass { color: #166534; font-weight: bold; }
.fail { color: #991b1b; font-weight: bold; }
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
<div id=\"status\" class=\"status\">Ready.</div>
<div class=\"panel\" style=\"margin-top: 1rem;\">
  <h3>JSON Editor</h3>
  <textarea id=\"case_json\"></textarea>
</div>
<div class=\"grid\">
  <div class=\"panel\"><h3>Validation</h3><div id=\"validation_output\"></div></div>
  <div class=\"panel\"><h3>Summary</h3><div id=\"summary_output\"></div></div>
  <div class=\"panel\">
    <h3>HTML Report</h3>
    <button id=\"open_report\" onclick=\"openReportInNewTab()\" style=\"display:none; margin-bottom: 0.6rem;\">Open report in new tab</button>
    <iframe id=\"html_output\" style=\"width:100%;height:380px;border:1px solid #d1d5db;border-radius:6px;\"></iframe>
  </div>
  <div class=\"panel\"><h3>Raw Response</h3><pre id=\"raw_output\"></pre></div>
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
function renderValidation(validation) {
  const panel = document.getElementById('validation_output');
  if (!validation || typeof validation !== 'object') { panel.innerHTML = '<p>N/A</p>'; return; }
  const isValid = validation.valid === true;
  let html = '<p><strong>Status:</strong> <span class=\"' + (isValid ? 'pass' : 'fail') + '\">' + (isValid ? 'VALID' : 'INVALID') + '</span></p>';
  const messages = Array.isArray(validation.messages) ? validation.messages : [];
  if (messages.length === 0) { html += '<p>No validation messages.</p>'; panel.innerHTML = html; return; }
  html += '<ul>';
  for (const m of messages) {
    const sev = m && m.severity ? m.severity : 'N/A';
    const path = m && m.path ? m.path : 'N/A';
    const msg = m && m.message ? m.message : 'N/A';
    const hint = m && m.hint ? m.hint : 'N/A';
    html += '<li><strong>[' + escapeHtml(sev) + ']</strong> path=' + escapeHtml(path) + ' | message=' + escapeHtml(msg) + ' | hint=' + escapeHtml(hint) + '</li>';
  }
  html += '</ul>';
  panel.innerHTML = html;
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
    renderRaw(data);
    latestHtmlReport = data.html_report || '';
    document.getElementById('html_output').srcdoc = latestHtmlReport || '<p>No HTML report.</p>';
    document.getElementById('open_report').style.display = latestHtmlReport ? 'inline-block' : 'none';
    setStatus(data.success ? 'Run complete.' : 'Run failed.');
  } catch (err) { setStatus('Network/error during run.'); }
}
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
