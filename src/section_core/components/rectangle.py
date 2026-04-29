"""Rectangular section components."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.geometry import Node, SectionLine, SectionPoint
from section_core.units import Dimension, UnitRegistry

from .base import SectionElement
from .errors import InvalidComponentGeometryError, UnknownReferenceError, UnsupportedComponentOperationError


@dataclass(frozen=True)
class RectangularElement(SectionElement):
    width_internal_mm: float = 0.0
    height_internal_mm: float = 0.0
    center_y_internal_mm: float = 0.0
    center_z_internal_mm: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "element_type", "rectangle")
        if self.width_internal_mm <= 0.0:
            raise InvalidComponentGeometryError("Rectangle width must be greater than zero.")
        if self.height_internal_mm <= 0.0:
            raise InvalidComponentGeometryError("Rectangle height must be greater than zero.")

    @classmethod
    def from_center(
        cls,
        *,
        element_id: str,
        width: float,
        width_unit: str,
        height: float,
        height_unit: str,
        center_y: float,
        center_y_unit: str,
        center_z: float,
        center_z_unit: str,
        rotation_deg: float = 0.0,
        name: str | None = None,
        material_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "RectangularElement":
        if float(rotation_deg) != 0.0:
            raise UnsupportedComponentOperationError("RectangularElement rotation is not supported in V1-004; use rotation_deg=0.")
        registry = UnitRegistry()
        return cls(
            element_id=element_id,
            name=name,
            element_type="rectangle",
            material_id=material_id,
            metadata=dict(metadata) if metadata is not None else None,
            width_internal_mm=registry.to_internal(float(width), width_unit, Dimension.LENGTH),
            height_internal_mm=registry.to_internal(float(height), height_unit, Dimension.LENGTH),
            center_y_internal_mm=registry.to_internal(float(center_y), center_y_unit, Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(center_z), center_z_unit, Dimension.LENGTH),
        )

    @classmethod
    def from_bottom_left(
        cls,
        *,
        element_id: str,
        width: float,
        width_unit: str,
        height: float,
        height_unit: str,
        bottom_left_y: float,
        bottom_left_y_unit: str,
        bottom_left_z: float,
        bottom_left_z_unit: str,
        rotation_deg: float = 0.0,
        name: str | None = None,
        material_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "RectangularElement":
        registry = UnitRegistry()
        width_mm = registry.to_internal(float(width), width_unit, Dimension.LENGTH)
        height_mm = registry.to_internal(float(height), height_unit, Dimension.LENGTH)
        bl_y = registry.to_internal(float(bottom_left_y), bottom_left_y_unit, Dimension.LENGTH)
        bl_z = registry.to_internal(float(bottom_left_z), bottom_left_z_unit, Dimension.LENGTH)
        return cls.from_center(
            element_id=element_id,
            width=width_mm,
            width_unit="mm",
            height=height_mm,
            height_unit="mm",
            center_y=bl_y + width_mm / 2.0,
            center_y_unit="mm",
            center_z=bl_z + height_mm / 2.0,
            center_z_unit="mm",
            rotation_deg=rotation_deg,
            name=name,
            material_id=material_id,
            metadata=metadata,
        )

    def _corners(self) -> dict[str, SectionPoint]:
        half_w = self.width_internal_mm / 2.0
        half_h = self.height_internal_mm / 2.0
        y0 = self.center_y_internal_mm - half_w
        y1 = self.center_y_internal_mm + half_w
        z0 = self.center_z_internal_mm - half_h
        z1 = self.center_z_internal_mm + half_h
        return {
            "bottom_left": SectionPoint.from_values(f"{self.element_id}_bottom_left", y0, z0, source_element_id=self.element_id, name="bottom_left"),
            "bottom_right": SectionPoint.from_values(f"{self.element_id}_bottom_right", y1, z0, source_element_id=self.element_id, name="bottom_right"),
            "top_right": SectionPoint.from_values(f"{self.element_id}_top_right", y1, z1, source_element_id=self.element_id, name="top_right"),
            "top_left": SectionPoint.from_values(f"{self.element_id}_top_left", y0, z1, source_element_id=self.element_id, name="top_left"),
        }

    def nodes(self) -> list[Node]:
        return [
            Node(node_id=f"{self.element_id}_{name}", name=name, y_internal_mm=point.y_internal_mm, z_internal_mm=point.z_internal_mm, element_id=self.element_id, node_type="vertex")
            for name, point in self._corners().items()
        ]

    def lines(self) -> list[SectionLine]:
        c = self._corners()
        return [
            SectionLine(f"{self.element_id}_bottom_edge", c["bottom_left"], c["bottom_right"], element_id=self.element_id),
            SectionLine(f"{self.element_id}_right_edge", c["bottom_right"], c["top_right"], element_id=self.element_id),
            SectionLine(f"{self.element_id}_top_edge", c["top_right"], c["top_left"], element_id=self.element_id),
            SectionLine(f"{self.element_id}_left_edge", c["top_left"], c["bottom_left"], element_id=self.element_id),
        ]

    def reference_points(self) -> dict[str, SectionPoint]:
        c = self._corners()
        center = self.centroid_point()
        return {
            "center": center,
            **c,
            "mid_top": SectionPoint.from_values(f"{self.element_id}_mid_top", self.center_y_internal_mm, c["top_left"].z_internal_mm, source_element_id=self.element_id, name="mid_top"),
            "mid_bottom": SectionPoint.from_values(f"{self.element_id}_mid_bottom", self.center_y_internal_mm, c["bottom_left"].z_internal_mm, source_element_id=self.element_id, name="mid_bottom"),
            "mid_left": SectionPoint.from_values(f"{self.element_id}_mid_left", c["bottom_left"].y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="mid_left"),
            "mid_right": SectionPoint.from_values(f"{self.element_id}_mid_right", c["bottom_right"].y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="mid_right"),
        }

    def reference_lines(self) -> dict[str, SectionLine]:
        lines = self.lines()
        return {"bottom_edge": lines[0], "right_edge": lines[1], "top_edge": lines[2], "left_edge": lines[3]}

    def area_mm2(self) -> float:
        return self.width_internal_mm * self.height_internal_mm

    def centroid_point(self) -> SectionPoint:
        return SectionPoint.from_values(f"{self.element_id}_center", self.center_y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="center")

    def bounding_box(self) -> tuple[float, float, float, float]:
        c = self._corners()
        return (c["bottom_left"].y_internal_mm, c["bottom_left"].z_internal_mm, c["top_right"].y_internal_mm, c["top_right"].z_internal_mm)

    def translated(self, dy_mm: float, dz_mm: float) -> "RectangularElement":
        return RectangularElement(
            element_id=self.element_id,
            name=self.name,
            element_type=self.element_type,
            source=self.source,
            material_id=self.material_id,
            metadata=dict(self.metadata) if self.metadata is not None else None,
            width_internal_mm=self.width_internal_mm,
            height_internal_mm=self.height_internal_mm,
            center_y_internal_mm=self.center_y_internal_mm + float(dy_mm),
            center_z_internal_mm=self.center_z_internal_mm + float(dz_mm),
        )

    def local_reference(self) -> SectionPoint:
        return self.centroid_point()

    def as_points_counterclockwise(self) -> list[SectionPoint]:
        c = self._corners()
        return [c["bottom_left"], c["bottom_right"], c["top_right"], c["top_left"]]

    def get_node(self, node_name: str) -> Node:
        for node in self.nodes():
            if node.name == node_name:
                return node
        raise UnknownReferenceError(f"Unknown node '{node_name}' for element '{self.element_id}'.")

    def get_reference_point(self, name: str) -> SectionPoint:
        refs = self.reference_points()
        if name not in refs:
            raise UnknownReferenceError(f"Unknown reference point '{name}' for element '{self.element_id}'.")
        return refs[name]

    def get_reference_line(self, name: str) -> SectionLine:
        refs = self.reference_lines()
        if name not in refs:
            raise UnknownReferenceError(f"Unknown reference line '{name}' for element '{self.element_id}'.")
        return refs[name]
