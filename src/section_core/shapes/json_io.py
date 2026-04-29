"""JSON import/export helpers for tabulated shape libraries."""

from __future__ import annotations

import json
from pathlib import Path

from .errors import DuplicateShapeError, InvalidShapeRecordError, ShapeLibraryError
from .registry import ShapeLibraryRegistry
from .shape_record import ShapeRecord


class InvalidShapeLibraryFileError(ShapeLibraryError):
    """Raised when a JSON file/dict does not match expected library structure."""


def _require_dict(data: object, context: str) -> dict:
    if not isinstance(data, dict):
        raise InvalidShapeLibraryFileError(f"{context} must be a JSON object.")
    return data


def _require_quantity(record: dict, field_name: str) -> tuple[float, str]:
    raw_value = record.get(field_name)
    value_obj = _require_dict(raw_value, f"'{field_name}'")
    if "value" not in value_obj or "unit" not in value_obj:
        raise InvalidShapeLibraryFileError(f"'{field_name}' must include 'value' and 'unit'.")
    return value_obj["value"], value_obj["unit"]


def _record_from_json_dict(record_data: object) -> ShapeRecord:
    record = _require_dict(record_data, "Each shape record")
    required_fields = ["shape_id", "shape_family", "shape_name", "source", "depth", "width", "area", "Iyy", "Izz"]
    for field in required_fields:
        if field not in record:
            raise InvalidShapeLibraryFileError(f"Record is missing required field '{field}'.")

    depth_value, depth_unit = _require_quantity(record, "depth")
    width_value, width_unit = _require_quantity(record, "width")
    area_value, area_unit = _require_quantity(record, "area")
    Iyy_value, Iyy_unit = _require_quantity(record, "Iyy")
    Izz_value, Izz_unit = _require_quantity(record, "Izz")

    Iyz_value, Iyz_unit = (0.0, "mm4")
    if "Iyz" in record:
        Iyz_value, Iyz_unit = _require_quantity(record, "Iyz")

    J_value = J_unit = None
    if "J" in record and record["J"] is not None:
        J_value, J_unit = _require_quantity(record, "J")

    Cw_value = Cw_unit = None
    if "Cw" in record and record["Cw"] is not None:
        Cw_value, Cw_unit = _require_quantity(record, "Cw")

    try:
        return ShapeRecord.from_values(
            shape_id=record["shape_id"],
            shape_family=record["shape_family"],
            shape_name=record["shape_name"],
            source=record["source"],
            depth=depth_value,
            depth_unit=depth_unit,
            width=width_value,
            width_unit=width_unit,
            area=area_value,
            area_unit=area_unit,
            Iyy=Iyy_value,
            Iyy_unit=Iyy_unit,
            Izz=Izz_value,
            Izz_unit=Izz_unit,
            Iyz=Iyz_value,
            Iyz_unit=Iyz_unit,
            J=J_value,
            J_unit=J_unit,
            Cw=Cw_value,
            Cw_unit=Cw_unit,
            metadata=record.get("metadata"),
        )
    except InvalidShapeRecordError as exc:
        raise InvalidShapeLibraryFileError(f"Invalid record '{record.get('shape_id', '<unknown>')}': {exc}") from exc


def _quantity_dict(value: float | None, unit: str) -> dict | None:
    if value is None:
        return None
    return {"value": value, "unit": unit}


def registry_from_json_dict(data: object) -> ShapeLibraryRegistry:
    top = _require_dict(data, "Top-level shape library")
    if "records" not in top:
        raise InvalidShapeLibraryFileError("Top-level 'records' field is required.")
    records = top["records"]
    if not isinstance(records, list):
        raise InvalidShapeLibraryFileError("Top-level 'records' must be a list.")

    registry = ShapeLibraryRegistry()
    for record_data in records:
        try:
            registry.add(_record_from_json_dict(record_data))
        except DuplicateShapeError as exc:
            raise InvalidShapeLibraryFileError(str(exc)) from exc
    return registry


def registry_to_json_dict(registry: ShapeLibraryRegistry, library_metadata: dict | None = None) -> dict:
    if not isinstance(registry, ShapeLibraryRegistry):
        raise InvalidShapeLibraryFileError("registry must be a ShapeLibraryRegistry.")

    metadata = dict(library_metadata or {})
    result = {
        "library_id": metadata.get("library_id", "shape_library"),
        "name": metadata.get("name", "Shape Library"),
        "source": metadata.get("source", "unknown"),
        "version": metadata.get("version", "0.1.0"),
        "unit_system": metadata.get("unit_system", "mixed_explicit"),
        "description": metadata.get("description", ""),
        "records": [],
    }

    for record in registry.list_shapes():
        result["records"].append(
            {
                "shape_id": record.shape_id,
                "shape_family": record.shape_family,
                "shape_name": record.shape_name,
                "source": record.source,
                "depth": {"value": record.depth_mm, "unit": "mm"},
                "width": {"value": record.width_mm, "unit": "mm"},
                "area": {"value": record.area_mm2, "unit": "mm2"},
                "Iyy": {"value": record.Iyy_mm4, "unit": "mm4"},
                "Izz": {"value": record.Izz_mm4, "unit": "mm4"},
                "Iyz": {"value": record.Iyz_mm4, "unit": "mm4"},
                "J": _quantity_dict(record.J_mm4, "mm4"),
                "Cw": _quantity_dict(record.Cw_mm6, "mm6"),
                "metadata": dict(record.metadata) if record.metadata is not None else None,
            }
        )
    return result


def load_shape_library_json(path: str | Path) -> ShapeLibraryRegistry:
    path_obj = Path(path)
    try:
        data = json.loads(path_obj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidShapeLibraryFileError(f"Invalid JSON in '{path_obj}': {exc}") from exc
    return registry_from_json_dict(data)


def dump_shape_library_json(registry: ShapeLibraryRegistry, path: str | Path, library_metadata: dict | None = None) -> None:
    path_obj = Path(path)
    payload = registry_to_json_dict(registry, library_metadata=library_metadata)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
