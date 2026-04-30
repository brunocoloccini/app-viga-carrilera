"""Local API boundary for crane runway case validation/execution (V1-053)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .case_io import run_crane_runway_case_dict
from .error_formatting import CraneRunwayCaseErrorFormatter
from .html_reporting import CraneRunwayDemandSummaryHtmlFormatter


class CraneRunwayApiServiceError(Exception):
    """Base error for crane runway local API service."""


class InvalidCraneRunwayApiRequestError(CraneRunwayApiServiceError):
    """Invalid request to crane runway local API service."""


@dataclass
class CraneRunwayApiValidationResponse:
    valid: bool
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "messages": list(self.messages),
            "metadata": dict(self.metadata),
        }


@dataclass
class CraneRunwayApiExecutionResponse:
    success: bool
    summary: dict[str, Any] | None = None
    text_report: str | None = None
    markdown_report: str | None = None
    html_report: str | None = None
    validation: CraneRunwayApiValidationResponse | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "summary": self.summary,
            "text_report": self.text_report,
            "markdown_report": self.markdown_report,
            "html_report": self.html_report,
            "validation": self.validation.to_dict() if self.validation else None,
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }


class CraneRunwayApiService:
    """Lightweight pure-Python service wrapper around crane runway case engine."""

    _SUPPORTED_OUTPUTS = {"summary", "text", "markdown", "html"}

    def validate_case_dict(self, data: Any, strict: bool = True) -> CraneRunwayApiValidationResponse:
        report = CraneRunwayCaseErrorFormatter.validate_case_dict_for_user(data, strict=strict)
        return CraneRunwayApiValidationResponse(valid=report.valid, messages=report.to_dict().get("messages", []), metadata=report.metadata or {})

    def validate_case_json_text(self, json_text: str, strict: bool = True) -> CraneRunwayApiValidationResponse:
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            report = CraneRunwayCaseErrorFormatter.from_exception(exc)
            return CraneRunwayApiValidationResponse(valid=False, messages=report.to_dict().get("messages", []), metadata=report.metadata or {})
        return self.validate_case_dict(data, strict=strict)

    def execute_case_dict(self, data: Any, output_formats: list[str] | None = None) -> CraneRunwayApiExecutionResponse:
        formats = ["summary"] if output_formats is None else list(output_formats)
        unknown = sorted(set(formats) - self._SUPPORTED_OUTPUTS)
        if unknown:
            err = {"path": "$.output_formats", "message": f"Unsupported output format(s): {', '.join(unknown)}.", "severity": "error", "code": "API_OUTPUT_FORMAT_ERROR"}
            return CraneRunwayApiExecutionResponse(success=False, errors=[err], metadata={"supported_output_formats": sorted(self._SUPPORTED_OUTPUTS)})

        validation = self.validate_case_dict(data)
        if not validation.valid:
            return CraneRunwayApiExecutionResponse(success=False, validation=validation, errors=list(validation.messages))

        try:
            result = run_crane_runway_case_dict(data)
            summary = result.workflow_result.summary
            response = CraneRunwayApiExecutionResponse(success=True)
            if "summary" in formats:
                response.summary = summary.to_dict()
            if "text" in formats:
                response.text_report = result.text_report
            if "markdown" in formats:
                response.markdown_report = result.markdown_report
            if "html" in formats:
                response.html_report = CraneRunwayDemandSummaryHtmlFormatter().format_html(summary)
            response.metadata = {"case_id": result.case_id}
            return response
        except Exception as exc:
            report = CraneRunwayCaseErrorFormatter.from_exception(exc)
            return CraneRunwayApiExecutionResponse(success=False, errors=report.to_dict().get("messages", []), metadata=report.metadata or {})

    def execute_case_json_text(self, json_text: str, output_formats: list[str] | None = None) -> CraneRunwayApiExecutionResponse:
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            report = CraneRunwayCaseErrorFormatter.from_exception(exc)
            validation = CraneRunwayApiValidationResponse(valid=False, messages=report.to_dict().get("messages", []), metadata=report.metadata or {})
            return CraneRunwayApiExecutionResponse(success=False, validation=validation, errors=list(validation.messages))
        return self.execute_case_dict(data, output_formats=output_formats)
