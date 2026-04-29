"""Crane runway scenario matrix HTML reporting (V1-045)."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape


class MatrixReportingError(ValueError):
    """Base error for crane runway matrix report formatting."""


@dataclass
class CraneRunwayMatrixCaseRow:
    case_id: str
    case_path: str | None = None
    max_vertical_moment_Nmm: float | None = None
    max_vertical_shear_abs_N: float | None = None
    max_vertical_deflection_mm: float | None = None
    max_biaxial_stress_MPa: float | None = None
    max_torsional_input_Nmm: float | None = None
    serviceability_passed: bool | None = None
    stress_criteria_passed: bool | None = None
    overall_passed: bool | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.case_id:
            raise MatrixReportingError("case_id is required.")


@dataclass
class CraneRunwayMatrixReport:
    title: str
    rows: list[CraneRunwayMatrixCaseRow]
    html: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title:
            raise MatrixReportingError("title is required.")
        if not self.rows:
            raise MatrixReportingError("at least one row is required.")
        if not self.html:
            raise MatrixReportingError("html is required.")


class CraneRunwayMatrixHtmlFormatter:
    TITLE = "Crane Runway Scenario Matrix"

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

    def row_from_case_result(self, case_result: object, case_path: str | None = None) -> CraneRunwayMatrixCaseRow:
        if case_result is None or not hasattr(case_result, "workflow_result"):
            raise MatrixReportingError("case_result with workflow_result is required.")
        summary = case_result.workflow_result.summary
        return CraneRunwayMatrixCaseRow(
            case_id=str(getattr(case_result, "case_id", "")),
            case_path=case_path,
            max_vertical_moment_Nmm=summary.max_vertical_moment_Nmm(),
            max_vertical_shear_abs_N=summary.max_vertical_shear_abs_N(),
            max_vertical_deflection_mm=summary.max_vertical_deflection_mm(),
            max_biaxial_stress_MPa=summary.max_biaxial_stress_MPa(),
            max_torsional_input_Nmm=summary.max_torsional_input_Nmm(),
            serviceability_passed=summary.serviceability_passed(),
            stress_criteria_passed=summary.stress_criteria_passed(),
            overall_passed=summary.overall_passed(),
            warnings=[str(w) for w in (summary.warnings or [])],
            metadata=dict(summary.metadata or {}),
        )

    def format_html(self, rows: list[CraneRunwayMatrixCaseRow], title: str = TITLE) -> str:
        if not title:
            raise MatrixReportingError("title is required.")
        if not rows:
            raise MatrixReportingError("at least one row is required.")

        body_rows: list[str] = []
        for row in rows:
            warnings_text = "; ".join(row.warnings) if row.warnings else "None"
            body_rows.append(
                "<tr>"
                f"<td>{escape(row.case_id)}</td>"
                f"<td>{escape(row.case_path or 'N/A')}</td>"
                f"<td>{escape(self._fmt_number(row.max_vertical_moment_Nmm, 'kN·m', divisor=1_000_000.0))}</td>"
                f"<td>{escape(self._fmt_number(row.max_vertical_shear_abs_N, 'kN', divisor=1_000.0))}</td>"
                f"<td>{escape(self._fmt_number(row.max_vertical_deflection_mm, 'mm'))}</td>"
                f"<td>{escape(self._fmt_number(row.max_biaxial_stress_MPa, 'MPa'))}</td>"
                f"<td>{escape(self._fmt_number(row.max_torsional_input_Nmm, 'kN·m', divisor=1_000_000.0))}</td>"
                f"<td>{escape(self._fmt_status(row.serviceability_passed))}</td>"
                f"<td>{escape(self._fmt_status(row.stress_criteria_passed))}</td>"
                f"<td>{escape(self._fmt_status(row.overall_passed))}</td>"
                f"<td>{escape(warnings_text)}</td>"
                "</tr>"
            )

        return (
            "<!doctype html>\n"
            "<html lang=\"en\">\n"
            "<head><meta charset=\"utf-8\"><title>Crane Runway Scenario Matrix</title>"
            "<style>body{font-family:Arial,sans-serif;margin:1.5rem;}table{border-collapse:collapse;width:100%;margin:0.5rem 0 1rem;}"
            "th,td{border:1px solid #ccc;padding:0.4rem;text-align:left;}thead th{background:#f5f5f5;}h1{margin:0.5rem 0;}</style></head>\n"
            "<body>"
            f"<h1>{escape(title)}</h1>"
            "<table><thead><tr>"
            "<th>Case ID</th><th>Case Path</th><th>Max Mv (kN·m)</th><th>Max Vv (kN)</th>"
            "<th>Max Deflection (mm)</th><th>Max Biaxial Stress (MPa)</th><th>Max Torsional Input (kN·m)</th>"
            "<th>Serviceability</th><th>Stress</th><th>Overall</th><th>Warnings</th>"
            "</tr></thead><tbody>"
            + "".join(body_rows)
            + "</tbody></table></body></html>"
        )

    def build_report(self, rows: list[CraneRunwayMatrixCaseRow], title: str = TITLE) -> CraneRunwayMatrixReport:
        html = self.format_html(rows=rows, title=title)
        return CraneRunwayMatrixReport(title=title, rows=list(rows), html=html, metadata={})
