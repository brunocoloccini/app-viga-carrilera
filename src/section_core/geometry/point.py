"""2D geometry point objects in internal coordinates."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units import Dimension, Quantity, UnitRegistry


@dataclass(frozen=True)
class Point2D:
    """Point in the section y-z plane, stored in internal mm units."""

    y_internal_mm: float
    z_internal_mm: float

    @classmethod
    def from_values(cls, y: float, z: float, units: str = "mm") -> "Point2D":
        registry = UnitRegistry()
        y_mm = registry.to_internal(float(y), units, Dimension.LENGTH)
        z_mm = registry.to_internal(float(z), units, Dimension.LENGTH)
        return cls(y_internal_mm=y_mm, z_internal_mm=z_mm)

    @classmethod
    def from_quantities(cls, y: Quantity, z: Quantity) -> "Point2D":
        registry = UnitRegistry()
        registry.assert_compatible(y.unit, Dimension.LENGTH)
        registry.assert_compatible(z.unit, Dimension.LENGTH)
        return cls(y_internal_mm=float(y.internal_value), z_internal_mm=float(z.internal_value))
