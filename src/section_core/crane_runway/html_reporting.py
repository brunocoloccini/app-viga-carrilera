"""Crane runway demand summary HTML formatting (V1-043)."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape


class HtmlReportingError(ValueError):
    """Base error for crane runway HTML report formatting."""


class InvalidHtmlReportSummaryError(HtmlReportingError):
    """Raised when a summary object cannot be rendered as HTML."""


@dataclass
class CraneRunwayHtmlReport:
    title: str
    summary_id: str
    html: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title:
            raise HtmlReportingError("title is required.")
        if not self.summary_id:
            raise HtmlReportingError("summary_id is required.")
        if not self.html:
            raise HtmlReportingError("html is required.")


class CraneRunwayDemandSummaryHtmlFormatter:
    TITLE = "Crane Runway Demand Summary"

    def _validate_summary(self, summary: object) -> object:
        if summary is None:
            raise InvalidHtmlReportSummaryError("summary must not be None.")

        required = [
            "summary_id",
            "span_internal_mm",
            "section_id",
            "load_model_id",
            "max_vertical_moment_Nmm",
            "max_vertical_shear_abs_N",
            "max_vertical_deflection_mm",
            "max_lateral_moment_Nmm",
            "max_biaxial_stress_MPa",
            "max_torsional_input_Nmm",
            "serviceability_passed",
            "stress_criteria_passed",
            "overall_passed",
            "warnings",
            "serviceability_results",
            "stress_utilization_results",
            "metadata",
        ]
        missing = [name for name in required if not hasattr(summary, name)]
        if missing:
            raise InvalidHtmlReportSummaryError(f"summary object missing required members: {', '.join(missing)}")
        return summary

    @staticmethod
    def _fmt_status(value: bool | None) -> str:
        if value is True:
            return "PASS"
        if value is False:
            return "FAIL"
        return "N/A"

    @staticmethod
    def _fmt_number(value: float | None, unit: str, divisor: float = 1.0) -> str:
        if value is None:
            return "N/A"
        return f"{(value / divisor):.3f} {unit}"

    @staticmethod
    def _table_row(label: str, value: str) -> str:
        return f"<tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>"

    def format_html(self, summary: object) -> str:
        s = self._validate_summary(summary)
        span = self._fmt_number(getattr(s, "span_internal_mm"), "m", divisor=1000.0)
        values = [
            ("Span", span),
            ("Max vertical moment", self._fmt_number(s.max_vertical_moment_Nmm(), "kN·m", divisor=1_000_000.0)),
            ("Max vertical shear", self._fmt_number(s.max_vertical_shear_abs_N(), "kN", divisor=1000.0)),
            ("Max vertical deflection", self._fmt_number(s.max_vertical_deflection_mm(), "mm")),
            ("Max lateral moment", self._fmt_number(s.max_lateral_moment_Nmm(), "kN·m", divisor=1_000_000.0)),
            ("Max biaxial stress", self._fmt_number(s.max_biaxial_stress_MPa(), "MPa")),
            ("Max torsional input", self._fmt_number(s.max_torsional_input_Nmm(), "kN·m", divisor=1_000_000.0)),
        ]

        serviceability_rows = []
        for r in s.serviceability_results or []:
            util = getattr(r, "utilization", None)
            util_text = f"{util:.3f}" if isinstance(util, float) else ("N/A" if util is None else str(util))
            serviceability_rows.append(
                "<tr>"
                f"<td>{escape(str(getattr(r, 'check_id', 'N/A')))}</td>"
                f"<td>{escape(str(getattr(r, 'limit_id', 'N/A')))}</td>"
                f"<td>{escape(str(getattr(r, 'demand_mm', 'N/A')))}</td>"
                f"<td>{escape(str(getattr(r, 'allowable_mm', 'N/A')))}</td>"
                f"<td>{escape(util_text)}</td>"
                f"<td>{escape(self._fmt_status(getattr(r, 'passed', None)))}</td>"
                "</tr>"
            )

        stress_rows = []
        for r in s.stress_utilization_results or []:
            util = getattr(r, "utilization", None)
            util_text = f"{util:.3f}" if isinstance(util, float) else ("N/A" if util is None else str(util))
            stress_rows.append(
                "<tr>"
                f"<td>{escape(str(getattr(r, 'check_id', 'N/A')))}</td>"
                f"<td>{escape(str(getattr(r, 'limit_id', 'N/A')))}</td>"
                f"<td>{escape(str(getattr(r, 'demand_MPa', 'N/A')))}</td>"
                f"<td>{escape(str(getattr(r, 'allowable_MPa', 'N/A')))}</td>"
                f"<td>{escape(util_text)}</td>"
                f"<td>{escape(str(getattr(r, 'critical_point_id', 'N/A')))}</td>"
                f"<td>{escape(self._fmt_status(getattr(r, 'passed', None)))}</td>"
                "</tr>"
            )

        warnings = s.warnings or []
        warning_items = "".join(f"<li>{escape(str(w))}</li>" for w in warnings) if warnings else "<li>None</li>"

        metadata_rows = "".join(
            self._table_row(str(k), "N/A" if v is None else str(v)) for k, v in sorted((s.metadata or {}).items())
        )
        metadata_block = ""
        if metadata_rows:
            metadata_block = (
                "<section><h2>Metadata</h2><table><thead><tr><th>Key</th><th>Value</th></tr></thead>"
                f"<tbody>{metadata_rows}</tbody></table></section>"
            )

        demand_rows = "".join(self._table_row(k, v) for k, v in values)

        serviceability_block = ""
        if serviceability_rows:
            serviceability_block = (
                "<section><h2>Serviceability Checks</h2><table><thead><tr>"
                "<th>Check ID</th><th>Limit ID</th><th>Demand</th><th>Allowable</th><th>Utilization</th><th>Status</th>"
                "</tr></thead><tbody>"
                + "".join(serviceability_rows)
                + "</tbody></table></section>"
            )

        stress_block = ""
        if stress_rows:
            stress_block = (
                "<section><h2>Stress Criteria Checks</h2><table><thead><tr>"
                "<th>Check ID</th><th>Limit ID</th><th>Demand</th><th>Allowable</th><th>Utilization</th><th>Critical Point</th><th>Status</th>"
                "</tr></thead><tbody>"
                + "".join(stress_rows)
                + "</tbody></table></section>"
            )

        return (
            "<!doctype html>\n"
            "<html lang=\"en\">\n"
            "<head><meta charset=\"utf-8\"><title>Crane Runway Demand Summary</title>"
            "<style>body{font-family:Arial,sans-serif;margin:1.5rem;}table{border-collapse:collapse;width:100%;margin:0.5rem 0 1rem;}"
            "th,td{border:1px solid #ccc;padding:0.4rem;text-align:left;}thead th{background:#f5f5f5;}h1,h2{margin:0.5rem 0;}"
            "ul{margin-top:0.25rem;}</style></head>\n"
            "<body>"
            "<h1>Crane Runway Demand Summary</h1>"
            "<section><h2>Identification</h2><table><tbody>"
            f"{self._table_row('summary_id', str(s.summary_id))}"
            f"{self._table_row('section_id', str(s.section_id) if s.section_id else 'N/A')}"
            f"{self._table_row('load_model_id', str(s.load_model_id) if s.load_model_id else 'N/A')}"
            "</tbody></table></section>"
            "<section><h2>Demands</h2><table><tbody>"
            f"{demand_rows}"
            "</tbody></table></section>"
            "<section><h2>Checks</h2><table><thead><tr><th>Check</th><th>Status</th></tr></thead><tbody>"
            f"<tr><th>Serviceability</th><td>{escape(self._fmt_status(s.serviceability_passed()))}</td></tr>"
            f"<tr><th>Stress criteria</th><td>{escape(self._fmt_status(s.stress_criteria_passed()))}</td></tr>"
            f"<tr><th>Overall</th><td>{escape(self._fmt_status(s.overall_passed()))}</td></tr>"
            "</tbody></table></section>"
            f"{serviceability_block}{stress_block}{metadata_block}"
            "<section><h2>Warnings</h2><ul>"
            f"{warning_items}</ul></section>"
            "</body></html>"
        )

    def build_report(self, summary: object) -> CraneRunwayHtmlReport:
        s = self._validate_summary(summary)
        html = self.format_html(s)
        return CraneRunwayHtmlReport(
            title=self.TITLE,
            summary_id=str(getattr(s, "summary_id")),
            html=html,
            metadata=dict(getattr(s, "metadata", {}) or {}),
        )
