"""Schema definition and validation for crane runway case JSON (V1)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CASE_SCHEMA_VERSION = "1.0"


class CraneRunwayCaseSchemaError(ValueError):
    """Base error for crane runway case schema handling."""


class InvalidCraneRunwayCaseSchemaError(CraneRunwayCaseSchemaError):
    """Raised when crane runway case data does not satisfy schema rules."""


@dataclass(frozen=True)
class CaseSchemaValidationIssue:
    path: str
    message: str
    severity: str = "error"
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class CaseSchemaValidationResult:
    valid: bool
    issues: list[CaseSchemaValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] | None = None

    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def raise_for_errors(self) -> None:
        errors = [i for i in self.issues if i.severity == "error"]
        if not errors:
            return
        details = "\n".join(f"- {i.path}: {i.message}" for i in errors)
        raise InvalidCraneRunwayCaseSchemaError(f"Crane runway case schema validation failed:\n{details}")


def get_crane_runway_case_schema_v1() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "crane_runway_case_schema_v1.json",
        "title": "Crane Runway Calculation Case V1",
        "type": "object",
        "x-schema-version": CASE_SCHEMA_VERSION,
        "required": [
            "schema_version",
            "case_id",
            "shape_library_path",
            "base_shape_id",
            "section",
            "span",
            "analysis",
            "crane",
        ],
        "properties": {
            "schema_version": {"type": "string", "const": CASE_SCHEMA_VERSION},
            "case_id": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
            "shape_library_path": {"type": "string", "minLength": 1},
            "base_shape_id": {"type": "string", "minLength": 1},
            "section": {"type": "object"},
            "span": {"$ref": "#/$defs/quantity"},
            "analysis": {"type": "object"},
            "crane": {"type": "object"},
            "serviceability_limits": {"type": "array"},
            "stress_limits": {"type": "array"},
            "rail_eccentricity": {"type": "object"},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "metadata": {"type": "object"},
        },
        "$defs": {
            "quantity": {
                "type": "object",
                "required": ["value", "unit"],
                "properties": {
                    "value": {"type": "number"},
                    "unit": {"type": "string", "minLength": 1},
                },
            }
        },
    }


def write_crane_runway_case_schema_v1(path: str | Path) -> None:
    Path(path).write_text(json.dumps(get_crane_runway_case_schema_v1(), indent=2) + "\n", encoding="utf-8")


def validate_crane_runway_case_dict(data: Any, strict: bool = True) -> CaseSchemaValidationResult:
    issues: list[CaseSchemaValidationIssue] = []

    def add(path: str, message: str, severity: str = "error") -> None:
        issues.append(CaseSchemaValidationIssue(path=path, message=message, severity=severity))

    def is_non_empty_string(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def validate_quantity(parent: dict[str, Any], field: str, path: str) -> None:
        q = parent.get(field)
        if not isinstance(q, dict):
            add(path, "Must be a quantity object.")
            return
        if "value" not in q:
            add(f"{path}.value", "Missing required field 'value'.")
        elif not isinstance(q["value"], (int, float)):
            add(f"{path}.value", "Must be numeric.")
        if "unit" not in q:
            add(f"{path}.unit", "Missing required field 'unit'.")
        elif not is_non_empty_string(q["unit"]):
            add(f"{path}.unit", "Must be a non-empty string.")

    if not isinstance(data, dict):
        add("$", "Case data must be a JSON object.")
        return CaseSchemaValidationResult(valid=False, issues=issues, metadata={"strict": strict})

    sv = data.get("schema_version")
    if sv is None:
        add("$.schema_version", "Missing required field 'schema_version'.", severity="error" if strict else "warning")
    elif sv != CASE_SCHEMA_VERSION:
        add("$.schema_version", f"Unsupported schema_version '{sv}'. Expected '{CASE_SCHEMA_VERSION}'.")

    for field in ["case_id", "shape_library_path", "base_shape_id"]:
        if field not in data:
            add(f"$.{field}", f"Missing required field '{field}'.")
        elif not is_non_empty_string(data[field]):
            add(f"$.{field}", "Must be a non-empty string.")

    if not isinstance(data.get("section"), dict):
        add("$.section", "Required field must be an object.")
    else:
        section = data["section"]
        for sf in ["section_id", "base_component_id"]:
            if sf not in section:
                add(f"$.section.{sf}", f"Missing required field '{sf}'.")
            elif not is_non_empty_string(section[sf]):
                add(f"$.section.{sf}", "Must be a non-empty string.")
        validate_quantity(section, "base_center_y", "$.section.base_center_y")
        validate_quantity(section, "base_center_z", "$.section.base_center_z")

        cover = section.get("cover_plate")
        if cover is not None:
            if not isinstance(cover, dict):
                add("$.section.cover_plate", "Must be an object.")
            elif bool(cover.get("enabled", False)):
                if not is_non_empty_string(cover.get("element_id")):
                    add("$.section.cover_plate.element_id", "Required when cover_plate.enabled is true.")
                validate_quantity(cover, "width", "$.section.cover_plate.width")
                validate_quantity(cover, "thickness", "$.section.cover_plate.thickness")
                validate_quantity(cover, "weld_size", "$.section.cover_plate.weld_size")
                if "weld_type" in cover and not is_non_empty_string(cover.get("weld_type")):
                    add("$.section.cover_plate.weld_type", "Must be a non-empty string when provided.")

    validate_quantity(data, "span", "$.span")

    if not isinstance(data.get("analysis"), dict):
        add("$.analysis", "Required field must be an object.")
    else:
        analysis = data["analysis"]
        validate_quantity(analysis, "movement_step", "$.analysis.movement_step")
        validate_quantity(analysis, "station_step", "$.analysis.station_step")
        validate_quantity(analysis, "E", "$.analysis.E")

    if not isinstance(data.get("crane"), dict):
        add("$.crane", "Required field must be an object.")
    else:
        crane = data["crane"]
        if not is_non_empty_string(crane.get("crane_id")):
            add("$.crane.crane_id", "Missing or empty crane_id.")
        wheels = crane.get("wheels")
        if not isinstance(wheels, list):
            add("$.crane.wheels", "Must be a non-empty list.")
        elif not wheels:
            add("$.crane.wheels", "Must be a non-empty list.")
        else:
            seen: set[str] = set()
            for idx, wheel in enumerate(wheels):
                p = f"$.crane.wheels[{idx}]"
                if not isinstance(wheel, dict):
                    add(p, "Must be an object.")
                    continue
                wheel_id = wheel.get("wheel_id")
                if not is_non_empty_string(wheel_id):
                    add(f"{p}.wheel_id", "Missing or empty wheel_id.")
                elif wheel_id in seen:
                    add(f"{p}.wheel_id", f"Duplicate wheel_id '{wheel_id}'.")
                else:
                    seen.add(wheel_id)
                validate_quantity(wheel, "position_x", f"{p}.position_x")
                validate_quantity(wheel, "vertical_force", f"{p}.vertical_force")
        for ff in ["vertical_impact_factor", "lateral_force_factor", "longitudinal_force_factor"]:
            if ff in crane:
                val = crane[ff]
                if not isinstance(val, (int, float)):
                    add(f"$.crane.{ff}", "Must be numeric when provided.")
                elif val < 0:
                    add(f"$.crane.{ff}", "Must be >= 0.")

    for idx, lim in enumerate(data.get("serviceability_limits", [])):
        p = f"$.serviceability_limits[{idx}]"
        if not isinstance(lim, dict):
            add(p, "Must be an object.")
            continue
        t = lim.get("type")
        if t not in {"span_over", "absolute", "minimum_of_span_over_and_absolute"}:
            add(f"{p}.type", f"Unsupported serviceability limit type '{t}'.")
        elif t == "span_over":
            if not isinstance(lim.get("divisor"), (int, float)) or lim["divisor"] <= 0:
                add(f"{p}.divisor", "Must be numeric > 0 for span_over.")
        elif t == "absolute":
            validate_quantity(lim, "value", f"{p}.value")
        else:
            if not isinstance(lim.get("divisor"), (int, float)) or lim["divisor"] <= 0:
                add(f"{p}.divisor", "Must be numeric > 0.")
            validate_quantity(lim, "value", f"{p}.value")

    for idx, lim in enumerate(data.get("stress_limits", [])):
        p = f"$.stress_limits[{idx}]"
        if not isinstance(lim, dict):
            add(p, "Must be an object.")
            continue
        t = lim.get("type")
        if t not in {"absolute", "fraction_of_Fy"}:
            add(f"{p}.type", f"Unsupported stress limit type '{t}'.")
        elif t == "absolute":
            validate_quantity(lim, "allowable", f"{p}.allowable")
        else:
            validate_quantity(lim, "Fy", f"{p}.Fy")
            if not isinstance(lim.get("factor"), (int, float)) or lim["factor"] <= 0:
                add(f"{p}.factor", "Must be numeric > 0 for fraction_of_Fy.")

    rail = data.get("rail_eccentricity")
    if rail is not None:
        if not isinstance(rail, dict):
            add("$.rail_eccentricity", "Must be an object.")
        elif bool(rail.get("enabled", False)):
            if not is_non_empty_string(rail.get("model_id")):
                add("$.rail_eccentricity.model_id", "Required when enabled is true.")
            validate_quantity(rail, "vertical_eccentricity_y", "$.rail_eccentricity.vertical_eccentricity_y")
            validate_quantity(rail, "lateral_load_height_z", "$.rail_eccentricity.lateral_load_height_z")
            inc_v = bool(rail.get("include_vertical", True))
            inc_l = bool(rail.get("include_lateral", True))
            if not inc_v and not inc_l:
                add("$.rail_eccentricity", "At least one of include_vertical/include_lateral must be true.")

    warnings = data.get("warnings")
    if warnings is not None:
        if not isinstance(warnings, list) or any(not isinstance(w, str) for w in warnings):
            add("$.warnings", "Must be a list of strings.")
    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        add("$.metadata", "Must be an object.")

    result = CaseSchemaValidationResult(valid=not any(i.severity == "error" for i in issues), issues=issues, metadata={"strict": strict})
    return result


def assert_valid_crane_runway_case_dict(data: Any, strict: bool = True) -> None:
    validate_crane_runway_case_dict(data, strict=strict).raise_for_errors()
