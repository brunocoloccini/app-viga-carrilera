"""User-facing validation and execution error formatting for crane runway cases."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .case_io import InvalidCraneRunwayCaseError
from .case_schema import CaseSchemaValidationResult, validate_crane_runway_case_dict

_ALLOWED_SEVERITIES = {"error", "warning", "info"}


@dataclass(frozen=True)
class UserFacingValidationMessage:
    path: str
    message: str
    severity: str
    code: str | None = None
    hint: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("path is required. Use '$' for top-level/global errors.")
        if not self.message:
            raise ValueError("message is required.")
        if self.severity not in _ALLOWED_SEVERITIES:
            raise ValueError("severity must be one of: error, warning, info.")


@dataclass(frozen=True)
class UserFacingValidationReport:
    valid: bool
    messages: list[UserFacingValidationMessage] = field(default_factory=list)
    metadata: dict[str, Any] | None = None

    def error_count(self) -> int:
        return sum(1 for msg in self.messages if msg.severity == "error")

    def warning_count(self) -> int:
        return sum(1 for msg in self.messages if msg.severity == "warning")

    def info_count(self) -> int:
        return sum(1 for msg in self.messages if msg.severity == "info")

    def has_errors(self) -> bool:
        return self.error_count() > 0

    def to_text(self) -> str:
        lines: list[str] = []
        for msg in self.messages:
            lines.append(f"{msg.severity.upper()} {msg.path}: {msg.message}")
            if msg.hint:
                lines.append(f"Hint: {msg.hint}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CraneRunwayCaseErrorFormatter:
    @staticmethod
    def _hint_for(path: str, message: str) -> str | None:
        p = path.lower()
        m = message.lower()
        if "schema_version" in p and "missing required field" in m:
            return 'Add "schema_version": "1.0" at the top level.'
        if ".unit" in p and "missing required field 'unit'" in m:
            return 'Use quantity objects like {"value": 80, "unit": "kN"}.'
        if "serviceability_limits" in p and "unsupported serviceability limit type" in m:
            return "Supported serviceability limit types are span_over, absolute, minimum_of_span_over_and_absolute."
        if "stress_limits" in p and "unsupported stress limit type" in m:
            return "Supported stress limit types are absolute and fraction_of_Fy."
        if "wheel_id" in p and "duplicate wheel_id" in m:
            return "Each wheel in crane.wheels must have a unique wheel_id."
        if "rail_eccentricity" in p and "include_vertical/include_lateral" in m:
            return "Set include_vertical or include_lateral to true, or disable rail_eccentricity."
        return None

    @classmethod
    def from_schema_validation_result(cls, validation_result: CaseSchemaValidationResult) -> UserFacingValidationReport:
        messages: list[UserFacingValidationMessage] = []
        for issue in validation_result.issues:
            code = (issue.metadata or {}).get("code") or "CASE_SCHEMA_ERROR"
            messages.append(
                UserFacingValidationMessage(
                    path=issue.path or "$",
                    message=issue.message,
                    severity=issue.severity,
                    code=code,
                    hint=cls._hint_for(issue.path, issue.message),
                    metadata=issue.metadata,
                )
            )
        return UserFacingValidationReport(valid=validation_result.valid, messages=messages, metadata=validation_result.metadata)

    @classmethod
    def from_exception(cls, exc: Exception, path: str = "$") -> UserFacingValidationReport:
        code = "CASE_UNKNOWN_ERROR"
        if isinstance(exc, InvalidCraneRunwayCaseError):
            code = "CASE_IO_ERROR"
        elif isinstance(exc, (json.JSONDecodeError, FileNotFoundError)):
            code = "CASE_JSON_ERROR"
        msg = UserFacingValidationMessage(path=path or "$", message=str(exc), severity="error", code=code)
        return UserFacingValidationReport(valid=False, messages=[msg])

    @classmethod
    def validate_case_dict_for_user(cls, data: Any, strict: bool = True) -> UserFacingValidationReport:
        result = validate_crane_runway_case_dict(data, strict=strict)
        return cls.from_schema_validation_result(result)

    @classmethod
    def validate_case_json_for_user(cls, path: str | Path, strict: bool = True) -> UserFacingValidationReport:
        path_obj = Path(path)
        if not path_obj.exists():
            return UserFacingValidationReport(
                valid=False,
                messages=[
                    UserFacingValidationMessage(
                        path="$",
                        message=f"Case file not found: '{path_obj}'.",
                        severity="error",
                        code="CASE_JSON_ERROR",
                    )
                ],
            )
        try:
            data = json.loads(path_obj.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return UserFacingValidationReport(
                valid=False,
                messages=[UserFacingValidationMessage(path="$", message=f"Invalid JSON in '{path_obj}': {exc}", severity="error", code="CASE_JSON_ERROR")],
            )
        except OSError as exc:
            return UserFacingValidationReport(
                valid=False,
                messages=[UserFacingValidationMessage(path="$", message=f"Could not read case file '{path_obj}': {exc}", severity="error", code="CASE_IO_ERROR")],
            )
        return cls.validate_case_dict_for_user(data, strict=strict)
