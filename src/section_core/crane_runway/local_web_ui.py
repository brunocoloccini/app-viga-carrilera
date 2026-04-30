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
<html lang=\"en\"><head><meta charset=\"utf-8\"/><title>Crane Runway Local UI</title></head>
<body>
<h1>Crane Runway Local UI</h1>
<p>Load a template, edit JSON, then validate or run.</p>
<label for=\"template\">Template:</label>
<select id=\"template\">
  <option value=\"ipn-with-cover\">ipn-with-cover</option>
  <option value=\"ipn-without-cover\">ipn-without-cover</option>
  <option value=\"ipn-no-rail-eccentricity\">ipn-no-rail-eccentricity</option>
</select>
<button onclick=\"loadTemplate()\">Load Template</button>
<br/><br/>
<textarea id=\"case_json\" rows=\"22\" cols=\"120\"></textarea><br/>
<button onclick=\"validateCase()\">Validate</button>
<button onclick=\"runCase()\">Run</button>
<h3>Validation Messages</h3><pre id=\"validation_output\"></pre>
<h3>Summary JSON</h3><pre id=\"summary_output\"></pre>
<h3>HTML Report Preview</h3><iframe id=\"html_output\" style=\"width:100%;height:380px;border:1px solid #ccc;\"></iframe>
<script>
async function loadTemplate() {
  const id = document.getElementById('template').value;
  const r = await fetch('/api/template/' + encodeURIComponent(id));
  const data = await r.json();
  document.getElementById('case_json').value = JSON.stringify(data, null, 2);
}
async function validateCase() {
  const payload = {case_json: document.getElementById('case_json').value};
  const r = await fetch('/api/validate', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await r.json();
  document.getElementById('validation_output').textContent = JSON.stringify(data, null, 2);
}
async function runCase() {
  const payload = {case_json: document.getElementById('case_json').value, output_formats:['summary','html']};
  const r = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await r.json();
  document.getElementById('validation_output').textContent = JSON.stringify(data.validation || {}, null, 2);
  document.getElementById('summary_output').textContent = JSON.stringify(data.summary || {}, null, 2);
  document.getElementById('html_output').srcdoc = data.html_report || '<p>No HTML report.</p>';
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
