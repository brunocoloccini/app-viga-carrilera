"""Report package export for crane runway case execution (V1-052)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .case_io import CraneRunwayCaseResult, run_crane_runway_case_json
from .error_formatting import CraneRunwayCaseErrorFormatter, UserFacingValidationReport
from .html_reporting import CraneRunwayDemandSummaryHtmlFormatter


class ReportPackageError(ValueError):
    """Base error for report package export."""


class InvalidReportPackageError(ReportPackageError):
    """Raised when inputs or case validation make package generation invalid."""


class ReportPackageWriteError(ReportPackageError):
    """Raised when package file writes fail."""


@dataclass(frozen=True)
class CraneRunwayReportPackageManifest:
    package_id: str
    case_id: str
    output_dir: str
    files: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.package_id:
            raise InvalidReportPackageError("package_id is required.")
        if not self.case_id:
            raise InvalidReportPackageError("case_id is required.")
        if not self.output_dir:
            raise InvalidReportPackageError("output_dir is required.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "case_id": self.case_id,
            "output_dir": self.output_dir,
            "files": dict(self.files),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CraneRunwayReportPackageResult:
    manifest: CraneRunwayReportPackageManifest
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.manifest is None:
            raise InvalidReportPackageError("manifest is required.")


class CraneRunwayReportPackageWriter:
    _PACKAGE_FILE_NAMES = (
        "input_case.json",
        "validation_report.json",
        "summary.json",
        "report.txt",
        "report.md",
        "report.html",
        "metadata.json",
        "manifest.json",
    )

    def write_case_package(
        self,
        case_path: str | Path,
        output_dir: str | Path,
        package_id: str | None = None,
        overwrite: bool = False,
    ) -> CraneRunwayReportPackageResult:
        validation = CraneRunwayCaseErrorFormatter.validate_case_json_for_user(case_path)
        if not validation.valid:
            raise InvalidReportPackageError(validation.to_text())
        result = run_crane_runway_case_json(case_path)
        return self.write_case_result_package(case_path, result, validation, output_dir, package_id=package_id, overwrite=overwrite)

    def write_case_result_package(
        self,
        case_path: str | Path,
        case_result: CraneRunwayCaseResult,
        validation_report: UserFacingValidationReport,
        output_dir: str | Path,
        package_id: str | None = None,
        overwrite: bool = False,
    ) -> CraneRunwayReportPackageResult:
        if case_result is None:
            raise InvalidReportPackageError("case_result is required.")
        if validation_report is None:
            raise InvalidReportPackageError("validation_report is required.")
        if not validation_report.valid:
            raise InvalidReportPackageError(validation_report.to_text())

        case_path_obj = Path(case_path)
        output_path = Path(output_dir)
        self._prepare_output_dir(output_path, overwrite=overwrite)

        payload = json.loads(case_path_obj.read_text(encoding="utf-8"))
        summary_dict = case_result.workflow_result.summary.to_dict()
        report_html = CraneRunwayDemandSummaryHtmlFormatter().format_html(case_result.workflow_result.summary)

        resolved_package_id = package_id or f"{case_result.case_id}-package"
        file_map: dict[str, str] = {name: str(output_path / name) for name in self._PACKAGE_FILE_NAMES}

        metadata = {
            "package_id": resolved_package_id,
            "case_id": case_result.case_id,
            "source_case_path": str(case_path_obj.resolve()),
            "schema_version": payload.get("schema_version"),
            "generated_by": "CraneRunwayReportPackageWriter",
            "files": dict(file_map),
            "notes": [
                "This package is a reproducible calculation output, not an independent engineering verification.",
                "Review all assumptions and limitations before production design use.",
            ],
        }

        manifest = CraneRunwayReportPackageManifest(
            package_id=resolved_package_id,
            case_id=case_result.case_id,
            output_dir=str(output_path.resolve()),
            files=dict(file_map),
            metadata={"schema_version": payload.get("schema_version")},
        )

        try:
            self._write_json(output_path / "input_case.json", payload)
            self._write_json(output_path / "validation_report.json", validation_report.to_dict())
            self._write_json(output_path / "summary.json", summary_dict)
            self._write_text(output_path / "report.txt", case_result.text_report)
            self._write_text(output_path / "report.md", case_result.markdown_report)
            self._write_text(output_path / "report.html", report_html)
            self._write_json(output_path / "metadata.json", metadata)
            self._write_json(output_path / "manifest.json", manifest.to_dict())
        except OSError as exc:
            raise ReportPackageWriteError(f"Failed to write report package to '{output_path}': {exc}") from exc

        return CraneRunwayReportPackageResult(manifest=manifest, metadata={"output_dir": str(output_path.resolve())})

    def _prepare_output_dir(self, output_path: Path, *, overwrite: bool) -> None:
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            return
        if not output_path.is_dir():
            raise ReportPackageError(f"Output path is not a directory: '{output_path}'.")
        if any(output_path.iterdir()) and not overwrite:
            raise ReportPackageError(f"Output directory '{output_path}' is not empty. Use overwrite=True to replace package files.")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
