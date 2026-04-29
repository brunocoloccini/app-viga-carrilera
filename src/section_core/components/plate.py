"""Plate component primitives."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units import Dimension, UnitRegistry

from .rectangle import RectangularElement


@dataclass(frozen=True)
class PlateElement(RectangularElement):
    thickness_internal_mm: float | None = None
    orientation: str = "horizontal"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "element_type", "plate")

    @classmethod
    def horizontal_plate(
        cls,
        *,
        element_id: str,
        width: float,
        width_unit: str,
        thickness: float,
        thickness_unit: str,
        center_y: float,
        center_y_unit: str,
        center_z: float,
        center_z_unit: str,
        name: str | None = None,
        material_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "PlateElement":
        registry = UnitRegistry()
        t_mm = registry.to_internal(float(thickness), thickness_unit, Dimension.LENGTH)
        return cls(
            element_id=element_id,
            name=name,
            material_id=material_id,
            metadata=dict(metadata) if metadata is not None else None,
            width_internal_mm=registry.to_internal(float(width), width_unit, Dimension.LENGTH),
            height_internal_mm=t_mm,
            center_y_internal_mm=registry.to_internal(float(center_y), center_y_unit, Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(center_z), center_z_unit, Dimension.LENGTH),
            thickness_internal_mm=t_mm,
            orientation="horizontal",
        )

    @classmethod
    def vertical_plate(
        cls,
        *,
        element_id: str,
        thickness: float,
        thickness_unit: str,
        height: float,
        height_unit: str,
        center_y: float,
        center_y_unit: str,
        center_z: float,
        center_z_unit: str,
        name: str | None = None,
        material_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "PlateElement":
        registry = UnitRegistry()
        t_mm = registry.to_internal(float(thickness), thickness_unit, Dimension.LENGTH)
        return cls(
            element_id=element_id,
            name=name,
            material_id=material_id,
            metadata=dict(metadata) if metadata is not None else None,
            width_internal_mm=t_mm,
            height_internal_mm=registry.to_internal(float(height), height_unit, Dimension.LENGTH),
            center_y_internal_mm=registry.to_internal(float(center_y), center_y_unit, Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(center_z), center_z_unit, Dimension.LENGTH),
            thickness_internal_mm=t_mm,
            orientation="vertical",
        )
