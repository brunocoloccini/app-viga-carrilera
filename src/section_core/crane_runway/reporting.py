"""Crane runway demand summary text/markdown formatting (V1-033)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .demand_summary import CraneRunwayDemandSummary


class ReportingError(ValueError):
    """Base error for crane runway report formatting."""


class InvalidReportSummaryError(ReportingError):
    """Raised when a summary object cannot be formatted."""


@dataclass
class ReportValue:
    label: str
    value: float | str | bool | None
    unit: str | None
    formatted_value: str
    metadata: dict = field(default_factory=dict)


@dataclass
class CraneRunwaySummaryReport:
    title: str
    summary_id: str
    lines: list[str]
    markdown: str
    metadata: dict = field(default_factory=dict)


class CraneRunwayDemandSummaryFormatter:
    """Formatter for text/markdown crane runway demand summaries."""

    TITLE = "Crane Runway Demand Summary"

    def _validate_summary(self, summary: object) -> CraneRunwayDemandSummary:
        if summary is None:
            raise InvalidReportSummaryError("summary must not be None.")

        required = [
            "summary_id",
            "span_internal_mm",
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
        ]
        missing = [name for name in required if not hasattr(summary, name)]
        if missing:
            raise InvalidReportSummaryError(f"summary object missing required members: {', '.join(missing)}")
        return summary  # type: ignore[return-value]

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

    def format_values(self, summary: object) -> list[ReportValue]:
        s = self._validate_summary(summary)
        return [
            ReportValue("Span", s.span_internal_mm, "m", self._fmt_number(s.span_internal_mm, "m", divisor=1000.0)),
            ReportValue(
                "Max vertical moment",
                s.max_vertical_moment_Nmm(),
                "kN·m",
                self._fmt_number(s.max_vertical_moment_Nmm(), "kN·m", divisor=1_000_000.0),
            ),
            ReportValue(
                "Max vertical shear",
                s.max_vertical_shear_abs_N(),
                "kN",
                self._fmt_number(s.max_vertical_shear_abs_N(), "kN", divisor=1000.0),
            ),
            ReportValue(
                "Max vertical deflection",
                s.max_vertical_deflection_mm(),
                "mm",
                self._fmt_number(s.max_vertical_deflection_mm(), "mm"),
            ),
            ReportValue(
                "Max lateral moment",
                s.max_lateral_moment_Nmm(),
                "kN·m",
                self._fmt_number(s.max_lateral_moment_Nmm(), "kN·m", divisor=1_000_000.0),
            ),
            ReportValue(
                "Max biaxial stress",
                s.max_biaxial_stress_MPa(),
                "MPa",
                self._fmt_number(s.max_biaxial_stress_MPa(), "MPa"),
            ),
            ReportValue(
                "Max torsional input",
                s.max_torsional_input_Nmm(),
                "kN·m",
                self._fmt_number(s.max_torsional_input_Nmm(), "kN·m", divisor=1_000_000.0),
            ),
        ]

    def format_text(self, summary: object) -> str:
        s = self._validate_summary(summary)
        values = {x.label: x.formatted_value for x in self.format_values(s)}
        warnings = s.warnings or []
        warning_text = "None" if not warnings else "; ".join(warnings)

        lines = [
            self.TITLE,
            f"summary_id: {s.summary_id}",
            f"section_id: {s.section_id or 'N/A'}",
            f"load_model_id: {s.load_model_id or 'N/A'}",
            f"span: {values['Span']}",
            f"max vertical moment: {values['Max vertical moment']}",
            f"max vertical shear: {values['Max vertical shear']}",
            f"max vertical deflection: {values['Max vertical deflection']}",
            f"max lateral moment: {values['Max lateral moment']}",
            f"max biaxial stress: {values['Max biaxial stress']}",
            f"max torsional input: {values['Max torsional input']}",
            f"serviceability status: {self._fmt_status(s.serviceability_passed())}",
            f"stress criteria status: {self._fmt_status(s.stress_criteria_passed())}",
            f"overall status: {self._fmt_status(s.overall_passed())}",
            f"warnings: {warning_text}",
        ]
        return "\n".join(lines)

    def format_markdown(self, summary: object) -> str:
        s = self._validate_summary(summary)
        values = self.format_values(s)
        value_map = {x.label: x.formatted_value for x in values}
        warnings = s.warnings or []

        md_lines = [
            f"# {self.TITLE}",
            "",
            "## Identification",
            "| Field | Value |",
            "|---|---|",
            f"| summary_id | {s.summary_id} |",
            f"| section_id | {s.section_id or 'N/A'} |",
            f"| load_model_id | {s.load_model_id or 'N/A'} |",
            "",
            "## Demands",
            "| Demand | Value |",
            "|---|---|",
        ]
        for rv in values:
            md_lines.append(f"| {rv.label} | {rv.formatted_value} |")

        md_lines.extend(
            [
                "",
                "## Checks",
                "| Check | Status |",
                "|---|---|",
                f"| Serviceability | {self._fmt_status(s.serviceability_passed())} |",
                f"| Stress criteria | {self._fmt_status(s.stress_criteria_passed())} |",
                f"| Overall | {self._fmt_status(s.overall_passed())} |",
            ]
        )

        if s.serviceability_results:
            md_lines.extend(["", "### Serviceability details", "| Check ID | Limit ID | Demand | Allowable | Utilization | Status |", "|---|---|---:|---:|---:|---|"])
            for r in s.serviceability_results:
                util = getattr(r, "utilization", None)
                util_text = f"{util:.3f}" if isinstance(util, float) else (str(util) if util is not None else "N/A")
                md_lines.append(
                    "| "
                    + f"{getattr(r, 'check_id', 'N/A')} | {getattr(r, 'limit_id', 'N/A')} | "
                    + f"{getattr(r, 'demand_mm', 'N/A')} | {getattr(r, 'allowable_mm', 'N/A')} | "
                    + f"{util_text} | "
                    + f"{self._fmt_status(getattr(r, 'passed', None))} |"
                )

        if s.stress_utilization_results:
            md_lines.extend(["", "### Stress utilization details", "| Check ID | Limit ID | Demand | Allowable | Utilization | Critical Point | Status |", "|---|---|---:|---:|---:|---|---|"])
            for r in s.stress_utilization_results:
                util = getattr(r, "utilization", None)
                util_text = f"{util:.3f}" if isinstance(util, float) else (str(util) if util is not None else "N/A")
                md_lines.append(
                    f"| {getattr(r, 'check_id', 'N/A')} | {getattr(r, 'limit_id', 'N/A')} | "
                    f"{getattr(r, 'demand_MPa', 'N/A')} | {getattr(r, 'allowable_MPa', 'N/A')} | {util_text} | "
                    f"{getattr(r, 'critical_point_id', 'N/A')} | {self._fmt_status(getattr(r, 'passed', None))} |"
                )

        md_lines.extend(["", "## Warnings"])
        if warnings:
            md_lines.extend([f"- {w}" for w in warnings])
        else:
            md_lines.append("- None")

        report = CraneRunwaySummaryReport(
            title=self.TITLE,
            summary_id=s.summary_id,
            lines=[f"{rv.label}: {value_map[rv.label]}" for rv in values],
            markdown="\n".join(md_lines),
        )
        return report.markdown
