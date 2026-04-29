"""Shape record model for tabulated structural profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from section_core.units import Dimension, UnitRegistry
from section_core.units.errors import UnitCompatibilityError, UnitError

from .errors import InvalidShapeRecordError


@dataclass(frozen=True)
class ShapeRecord:
    shape_id: str
    shape_family: str
    shape_name: str
    source: str
    depth_mm: float
    width_mm: float
    area_mm2: float
    Iyy_mm4: float
    Izz_mm4: float
    Iyz_mm4: float = 0.0
    weight_per_length: float | None = None
    J_mm4: float | None = None
    Cw_mm6: float | None = None
    S_y_top_mm3: float | None = None
    S_y_bottom_mm3: float | None = None
    S_z_left_mm3: float | None = None
    S_z_right_mm3: float | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.shape_id:
            raise InvalidShapeRecordError("shape_id is required.")
        if not self.shape_family:
            raise InvalidShapeRecordError("shape_family is required.")
        if not self.shape_name:
            raise InvalidShapeRecordError("shape_name is required.")
        if self.depth_mm <= 0:
            raise InvalidShapeRecordError("depth_mm must be greater than zero.")
        if self.width_mm <= 0:
            raise InvalidShapeRecordError("width_mm must be greater than zero.")
        if self.area_mm2 <= 0:
            raise InvalidShapeRecordError("area_mm2 must be greater than zero.")
        if self.Iyy_mm4 < 0:
            raise InvalidShapeRecordError("Iyy_mm4 must be non-negative.")
        if self.Izz_mm4 < 0:
            raise InvalidShapeRecordError("Izz_mm4 must be non-negative.")

    @classmethod
    def from_values(cls, **kwargs) -> "ShapeRecord":
        reg = UnitRegistry()

        def _convert(value: float | None, unit: str | None, dimension: str, field_name: str) -> float | None:
            if value is None:
                return None
            used_unit = unit or reg.internal_unit_for(dimension)
            try:
                return reg.to_internal(float(value), used_unit, dimension)
            except (UnitError, UnitCompatibilityError) as exc:
                raise InvalidShapeRecordError(f"Invalid unit for {field_name}: {exc}") from exc

        return cls(
            shape_id=kwargs["shape_id"],
            shape_family=kwargs["shape_family"],
            shape_name=kwargs["shape_name"],
            source=kwargs["source"],
            depth_mm=_convert(kwargs["depth"], kwargs.get("depth_unit"), Dimension.LENGTH, "depth"),
            width_mm=_convert(kwargs["width"], kwargs.get("width_unit"), Dimension.LENGTH, "width"),
            area_mm2=_convert(kwargs["area"], kwargs.get("area_unit"), Dimension.AREA, "area"),
            Iyy_mm4=_convert(kwargs["Iyy"], kwargs.get("Iyy_unit"), Dimension.INERTIA, "Iyy"),
            Izz_mm4=_convert(kwargs["Izz"], kwargs.get("Izz_unit"), Dimension.INERTIA, "Izz"),
            Iyz_mm4=_convert(kwargs.get("Iyz", 0.0), kwargs.get("Iyz_unit", "mm4"), Dimension.INERTIA, "Iyz") or 0.0,
            weight_per_length=_convert(
                kwargs.get("weight_per_length"), kwargs.get("weight_per_length_unit"), Dimension.MASS_PER_LENGTH, "weight_per_length"
            ),
            J_mm4=_convert(kwargs.get("J"), kwargs.get("J_unit"), Dimension.INERTIA, "J"),
            Cw_mm6=_convert(kwargs.get("Cw"), kwargs.get("Cw_unit"), Dimension.WARPING_CONSTANT, "Cw"),
            S_y_top_mm3=_convert(kwargs.get("S_y_top"), kwargs.get("S_y_top_unit"), Dimension.SECTION_MODULUS, "S_y_top"),
            S_y_bottom_mm3=_convert(kwargs.get("S_y_bottom"), kwargs.get("S_y_bottom_unit"), Dimension.SECTION_MODULUS, "S_y_bottom"),
            S_z_left_mm3=_convert(kwargs.get("S_z_left"), kwargs.get("S_z_left_unit"), Dimension.SECTION_MODULUS, "S_z_left"),
            S_z_right_mm3=_convert(kwargs.get("S_z_right"), kwargs.get("S_z_right_unit"), Dimension.SECTION_MODULUS, "S_z_right"),
            metadata=dict(kwargs["metadata"]) if kwargs.get("metadata") is not None else None,
        )

    def to_dict(self) -> dict:
        return asdict(self)
