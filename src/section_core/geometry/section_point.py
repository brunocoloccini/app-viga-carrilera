"""Section point primitive in y-z internal mm coordinates."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units import Dimension, Quantity, UnitRegistry

from .node import Node
from .point import Point2D
from .tolerance import GeometryTolerance


@dataclass(frozen=True)
class SectionPoint(Point2D):
    point_id: str
    name: str | None = None
    source_element_id: str | None = None
    metadata: dict[str, object] | None = None

    @classmethod
    def from_values(
        cls,
        point_id: str,
        y: float,
        z: float,
        unit: str = "mm",
        name: str | None = None,
        source_element_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "SectionPoint":
        registry = UnitRegistry()
        y_mm = registry.to_internal(float(y), unit, Dimension.LENGTH)
        z_mm = registry.to_internal(float(z), unit, Dimension.LENGTH)
        return cls(
            y_internal_mm=y_mm,
            z_internal_mm=z_mm,
            point_id=point_id,
            name=name,
            source_element_id=source_element_id,
            metadata=dict(metadata) if metadata is not None else None,
        )

    @classmethod
    def from_point2d(
        cls,
        point_id: str,
        point: Point2D,
        name: str | None = None,
        source_element_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "SectionPoint":
        return cls(
            y_internal_mm=point.y_internal_mm,
            z_internal_mm=point.z_internal_mm,
            point_id=point_id,
            name=name,
            source_element_id=source_element_id,
            metadata=dict(metadata) if metadata is not None else None,
        )

    @classmethod
    def from_node(
        cls,
        node: Node,
        point_id: str | None = None,
        name: str | None = None,
        source_element_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "SectionPoint":
        return cls(
            y_internal_mm=node.y_internal_mm,
            z_internal_mm=node.z_internal_mm,
            point_id=point_id or node.node_id,
            name=name or node.name,
            source_element_id=source_element_id or node.element_id,
            metadata=dict(metadata) if metadata is not None else None,
        )

    @classmethod
    def from_quantities(
        cls,
        point_id: str,
        y: Quantity,
        z: Quantity,
        name: str | None = None,
        source_element_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "SectionPoint":
        registry = UnitRegistry()
        registry.assert_compatible(y.unit, Dimension.LENGTH)
        registry.assert_compatible(z.unit, Dimension.LENGTH)
        return cls(
            y_internal_mm=float(y.internal_value),
            z_internal_mm=float(z.internal_value),
            point_id=point_id,
            name=name,
            source_element_id=source_element_id,
            metadata=dict(metadata) if metadata is not None else None,
        )

    def distance_to(self, other: "SectionPoint") -> float:
        dy = other.y_internal_mm - self.y_internal_mm
        dz = other.z_internal_mm - self.z_internal_mm
        return (dy * dy + dz * dz) ** 0.5

    def is_close_to(self, other: "SectionPoint", tolerance: GeometryTolerance) -> bool:
        return self.distance_to(other) <= tolerance.point_merge_abs_tol_mm

    def translated(self, dy_mm: float, dz_mm: float) -> "SectionPoint":
        return SectionPoint(
            y_internal_mm=self.y_internal_mm + float(dy_mm),
            z_internal_mm=self.z_internal_mm + float(dz_mm),
            point_id=self.point_id,
            name=self.name,
            source_element_id=self.source_element_id,
            metadata=dict(self.metadata) if self.metadata is not None else None,
        )

    def as_tuple(self) -> tuple[float, float]:
        return (self.y_internal_mm, self.z_internal_mm)
