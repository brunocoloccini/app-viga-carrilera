"""JSON case-file I/O and workflow orchestration for crane runway calculations (V1-036)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from section_core import LineToLineJoin
from section_core.components import PlateElement
from section_core.section import Section
from section_core.shapes import load_shape_library_json
from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .loads import CraneLoadModel, CraneWheelGroup, WheelLoad
from .rail_eccentricity import RailEccentricityModel
from .serviceability import DeflectionLimit
from .stress_criteria import StressLimit
from .workflow import CraneRunwayCalculationWorkflow, CraneRunwayWorkflowInput, CraneRunwayWorkflowResult
from .case_schema import InvalidCraneRunwayCaseSchemaError, assert_valid_crane_runway_case_dict


class CraneRunwayCaseIOError(ValueError):
    """Base error for crane runway case file loading/saving."""


class InvalidCraneRunwayCaseError(CraneRunwayCaseIOError):
    """Invalid crane runway case JSON structure or content."""


class CraneRunwayCaseExecutionError(CraneRunwayCaseIOError):
    """Error while converting or running a crane runway case."""


@dataclass(frozen=True)
class CraneRunwayCaseInput:
    case_id: str
    shape_library_path: str
    base_shape_id: str
    description: str | None = None
    raw_data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class CraneRunwayCaseResult:
    case_id: str
    workflow_result: CraneRunwayWorkflowResult
    summary_dict: dict[str, Any]
    text_report: str
    markdown_report: str
    metadata: dict[str, Any] | None = None


def _require_dict(data: object, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InvalidCraneRunwayCaseError(f"{context} must be a JSON object.")
    return data


def _require_field(d: dict[str, Any], field: str) -> Any:
    if field not in d:
        raise InvalidCraneRunwayCaseError(f"Missing required field '{field}'.")
    return d[field]


def _quantity_value(parent: dict[str, Any], field: str, dimension: Dimension) -> float:
    q = _require_dict(_require_field(parent, field), f"'{field}'")
    if "value" not in q or "unit" not in q:
        raise InvalidCraneRunwayCaseError(f"'{field}' must include 'value' and 'unit'.")
    try:
        return Quantity(q["value"], q["unit"], dimension).internal_value
    except Exception as exc:
        raise InvalidCraneRunwayCaseError(f"Invalid quantity for '{field}': {exc}") from exc


def load_crane_runway_case_json(path: str | Path) -> dict[str, Any]:
    path_obj = Path(path)
    try:
        data = json.loads(path_obj.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CraneRunwayCaseIOError(f"Case file not found: '{path_obj}'.") from exc
    except json.JSONDecodeError as exc:
        raise CraneRunwayCaseIOError(f"Invalid JSON in '{path_obj}': {exc}") from exc
    return _require_dict(data, "Top-level case")


def dump_crane_runway_case_json(data: dict[str, Any], path: str | Path) -> None:
    payload = _require_dict(data, "Case data")
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def crane_runway_case_from_json_dict(data: dict[str, Any]) -> CraneRunwayCaseInput:
    top = _require_dict(data, "Top-level case")
    return CraneRunwayCaseInput(
        case_id=str(_require_field(top, "case_id")),
        description=top.get("description"),
        shape_library_path=str(_require_field(top, "shape_library_path")),
        base_shape_id=str(_require_field(top, "base_shape_id")),
        raw_data=dict(top),
        metadata=top.get("metadata") or {},
    )


def crane_runway_case_to_json_dict(case_input: CraneRunwayCaseInput) -> dict[str, Any]:
    if case_input.raw_data is not None:
        return dict(case_input.raw_data)
    return {
        "case_id": case_input.case_id,
        "description": case_input.description,
        "shape_library_path": case_input.shape_library_path,
        "base_shape_id": case_input.base_shape_id,
        "metadata": case_input.metadata or {},
    }


def _build_section(data: dict[str, Any]):
    section_data = _require_dict(data.get("section") or {}, "'section'")
    library_path = str(_require_field(data, "shape_library_path"))
    base_shape_id = str(_require_field(data, "base_shape_id"))

    try:
        registry = load_shape_library_json(library_path)
    except FileNotFoundError as exc:
        raise InvalidCraneRunwayCaseError(f"Shape library file not found: '{library_path}'.") from exc
    except Exception as exc:
        raise InvalidCraneRunwayCaseError(f"Could not load shape library '{library_path}': {exc}") from exc

    base_component_id = section_data.get("base_component_id", "base_shape")
    base_center_y_mm = _quantity_value(section_data, "base_center_y", Dimension.LENGTH)
    base_center_z_mm = _quantity_value(section_data, "base_center_z", Dimension.LENGTH)

    try:
        base = registry.to_component(
            base_shape_id,
            element_id=base_component_id,
            center_y=base_center_y_mm,
            center_z=base_center_z_mm,
            center_unit="mm",
        )
    except KeyError as exc:
        raise InvalidCraneRunwayCaseError(f"Unknown base_shape_id '{base_shape_id}' in shape library '{library_path}'.") from exc

    section = Section(section_id=section_data.get("section_id", data["case_id"]), components=[base])
    cover = _require_dict(section_data.get("cover_plate") or {"enabled": False}, "'section.cover_plate'")
    if cover.get("enabled", False):
        width = _quantity_value(cover, "width", Dimension.LENGTH)
        thickness = _quantity_value(cover, "thickness", Dimension.LENGTH)
        weld_size = _quantity_value(cover, "weld_size", Dimension.LENGTH)
        if width <= 0 or thickness <= 0 or weld_size <= 0:
            raise InvalidCraneRunwayCaseError("Cover plate width, thickness, and weld_size must be positive when enabled.")
        plate = PlateElement.horizontal_plate(
            element_id=cover.get("element_id", "cover_plate"),
            width=width,
            width_unit="mm",
            thickness=thickness,
            thickness_unit="mm",
            center_y=0,
            center_y_unit="mm",
            center_z=0,
            center_z_unit="mm",
        )
        section = LineToLineJoin(
            operation_id=f"join_{plate.element_id}_to_{base_component_id}",
            operation_type="ignored",
            source_component=plate,
            source_line_name="bottom_edge",
            target_component_id=base_component_id,
            target_line_name="top_edge",
            create_connection=True,
            interface_type="weld",
            weld_type=cover.get("weld_type", "fillet"),
            weld_size_mm=weld_size,
        ).apply(section)
    return section


def _build_serviceability_limits(data: dict[str, Any]) -> list[DeflectionLimit]:
    limits = []
    for item in data.get("serviceability_limits", []):
        row = _require_dict(item, "serviceability limit")
        limit_type = row.get("type")
        if limit_type == "span_over":
            limits.append(DeflectionLimit.span_over(row["limit_id"], row["divisor"]))
        else:
            raise InvalidCraneRunwayCaseError(f"Unsupported serviceability limit type: {limit_type}")
    return limits


def _build_stress_limits(data: dict[str, Any]) -> list[StressLimit]:
    limits = []
    for item in data.get("stress_limits", []):
        row = _require_dict(item, "stress limit")
        limit_type = row.get("type")
        if limit_type == "fraction_of_Fy":
            fy = _quantity_value(row, "Fy", Dimension.STRESS)
            limits.append(StressLimit.fraction_of_Fy(row["limit_id"], Fy=fy, factor=row["factor"], Fy_unit="MPa"))
        elif limit_type == "absolute":
            allowable = _quantity_value(row, "allowable", Dimension.STRESS)
            limits.append(StressLimit.absolute(row["limit_id"], value=allowable, unit="MPa"))
        else:
            raise InvalidCraneRunwayCaseError(f"Unsupported stress limit type: {limit_type}")
    return limits


def build_workflow_input_from_case_dict(data: dict[str, Any], *, validate: bool = True, strict: bool = True) -> CraneRunwayWorkflowInput:
    if validate:
        try:
            assert_valid_crane_runway_case_dict(data, strict=strict)
        except InvalidCraneRunwayCaseSchemaError as exc:
            raise InvalidCraneRunwayCaseError(str(exc)) from exc
    top = _require_dict(data, "Top-level case")
    for req in ["case_id", "shape_library_path", "base_shape_id", "span", "analysis", "crane"]:
        _require_field(top, req)
    crane = _require_dict(top["crane"], "'crane'")
    wheels_data = crane.get("wheels")
    if not isinstance(wheels_data, list) or not wheels_data:
        raise InvalidCraneRunwayCaseError("'crane.wheels' must be a non-empty list.")

    wheel_ids = [str(_require_field(_require_dict(w, "wheel"), "wheel_id")) for w in wheels_data]
    if len(wheel_ids) != len(set(wheel_ids)):
        raise InvalidCraneRunwayCaseError("Duplicate wheel_id values are not allowed.")

    wheels = [
        WheelLoad.from_values(
            wheel_id=str(w["wheel_id"]),
            position_x=_quantity_value(w, "position_x", Dimension.LENGTH),
            position_x_unit="mm",
            vertical_force=_quantity_value(w, "vertical_force", Dimension.FORCE),
            vertical_force_unit="N",
        )
        for w in wheels_data
    ]
    wheel_group = CraneWheelGroup(group_id=f"{crane.get('crane_id', top['case_id'])}_wheels", wheels=wheels)
    model = CraneLoadModel(
        crane_id=crane.get("crane_id", top["case_id"]),
        name=crane.get("name"),
        wheel_group=wheel_group,
        vertical_impact_factor=float(crane.get("vertical_impact_factor", 0.0)),
        lateral_force_factor=float(crane.get("lateral_force_factor", 0.0)),
        longitudinal_force_factor=float(crane.get("longitudinal_force_factor", 0.0)),
    )

    rail = _require_dict(top.get("rail_eccentricity") or {"enabled": False}, "'rail_eccentricity'")
    rail_model = None
    if rail.get("enabled", False):
        rail_model = RailEccentricityModel.from_values(
            rail.get("model_id", "rail_eccentricity"),
            vertical_eccentricity_y=_quantity_value(rail, "vertical_eccentricity_y", Dimension.LENGTH),
            vertical_eccentricity_y_unit="mm",
            lateral_load_height_z=_quantity_value(rail, "lateral_load_height_z", Dimension.LENGTH),
            lateral_load_height_z_unit="mm",
            include_vertical=bool(rail.get("include_vertical", True)),
            include_lateral=bool(rail.get("include_lateral", True)),
        )

    analysis = _require_dict(top["analysis"], "'analysis'")
    return CraneRunwayWorkflowInput(
        workflow_id=str(top["case_id"]),
        span_internal_mm=_quantity_value(top, "span", Dimension.LENGTH),
        section=_build_section(top),
        crane_load_model=model,
        movement_step_internal_mm=_quantity_value(analysis, "movement_step", Dimension.LENGTH),
        station_step_internal_mm=_quantity_value(analysis, "station_step", Dimension.LENGTH),
        E_internal_MPa=_quantity_value(analysis, "E", Dimension.STRESS),
        serviceability_limits=_build_serviceability_limits(top),
        stress_limits=_build_stress_limits(top),
        rail_eccentricity_model=rail_model,
        warnings=list(top.get("warnings") or []),
        metadata=dict(top.get("metadata") or {}),
    )


def run_crane_runway_case_dict(data: dict[str, Any]) -> CraneRunwayCaseResult:
    try:
        case_input = crane_runway_case_from_json_dict(data)
        assert_valid_crane_runway_case_dict(data, strict=True)
        wi = build_workflow_input_from_case_dict(data, validate=False)
        wr = CraneRunwayCalculationWorkflow(wi).run()
        return CraneRunwayCaseResult(
            case_id=case_input.case_id,
            workflow_result=wr,
            summary_dict=wr.summary.to_dict(),
            text_report=wr.text_report,
            markdown_report=wr.markdown_report,
            metadata=case_input.metadata or {},
        )
    except (CraneRunwayCaseIOError, InvalidCraneRunwayCaseSchemaError) as exc:
        raise InvalidCraneRunwayCaseError(str(exc)) from exc
    except Exception as exc:
        raise CraneRunwayCaseExecutionError(f"Failed to run case '{data.get('case_id', '<unknown>')}': {exc}") from exc


def run_crane_runway_case_json(path: str | Path) -> CraneRunwayCaseResult:
    return run_crane_runway_case_dict(load_crane_runway_case_json(path))
