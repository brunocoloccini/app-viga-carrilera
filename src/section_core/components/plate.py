"""Plate component primitives."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.geometry import Transform2D
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
    def horizontal_plate(cls, *, rotation_deg: float = 0.0, **kwargs) -> "PlateElement":
        registry = UnitRegistry()
        t_mm = registry.to_internal(float(kwargs["thickness"]), kwargs["thickness_unit"], Dimension.LENGTH)
        return cls(
            element_id=kwargs["element_id"],
            name=kwargs.get("name"),
            material_id=kwargs.get("material_id"),
            metadata=dict(kwargs["metadata"]) if kwargs.get("metadata") is not None else None,
            width_internal_mm=registry.to_internal(float(kwargs["width"]), kwargs["width_unit"], Dimension.LENGTH),
            height_internal_mm=t_mm,
            center_y_internal_mm=registry.to_internal(float(kwargs["center_y"]), kwargs["center_y_unit"], Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(kwargs["center_z"]), kwargs["center_z_unit"], Dimension.LENGTH),
            thickness_internal_mm=t_mm,
            orientation="horizontal",
            rotation_deg=float(rotation_deg),
        )

    @classmethod
    def vertical_plate(cls, *, rotation_deg: float = 0.0, **kwargs) -> "PlateElement":
        registry = UnitRegistry()
        t_mm = registry.to_internal(float(kwargs["thickness"]), kwargs["thickness_unit"], Dimension.LENGTH)
        return cls(
            element_id=kwargs["element_id"],
            name=kwargs.get("name"),
            material_id=kwargs.get("material_id"),
            metadata=dict(kwargs["metadata"]) if kwargs.get("metadata") is not None else None,
            width_internal_mm=t_mm,
            height_internal_mm=registry.to_internal(float(kwargs["height"]), kwargs["height_unit"], Dimension.LENGTH),
            center_y_internal_mm=registry.to_internal(float(kwargs["center_y"]), kwargs["center_y_unit"], Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(kwargs["center_z"]), kwargs["center_z_unit"], Dimension.LENGTH),
            thickness_internal_mm=t_mm,
            orientation="vertical",
            rotation_deg=float(rotation_deg),
        )

    def transformed(self, transform: Transform2D) -> "PlateElement":
        transformed_rectangle = super().transformed(transform)
        return PlateElement(
            element_id=transformed_rectangle.element_id,
            element_type="plate",
            name=transformed_rectangle.name,
            source=transformed_rectangle.source,
            material_id=transformed_rectangle.material_id,
            metadata=transformed_rectangle.metadata,
            width_internal_mm=transformed_rectangle.width_internal_mm,
            height_internal_mm=transformed_rectangle.height_internal_mm,
            center_y_internal_mm=transformed_rectangle.center_y_internal_mm,
            center_z_internal_mm=transformed_rectangle.center_z_internal_mm,
            rotation_deg=transformed_rectangle.rotation_deg,
            thickness_internal_mm=self.thickness_internal_mm,
            orientation=self.orientation,
        )
