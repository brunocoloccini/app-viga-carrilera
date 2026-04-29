"""Rectangular section components."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.geometry import Node, SectionLine, SectionPoint, Transform2D
from section_core.units import Dimension, UnitRegistry

from .base import SectionElement
from .errors import InvalidComponentGeometryError, UnknownReferenceError


@dataclass(frozen=True)
class RectangularElement(SectionElement):
    width_internal_mm: float = 0.0
    height_internal_mm: float = 0.0
    center_y_internal_mm: float = 0.0
    center_z_internal_mm: float = 0.0
    rotation_deg: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "element_type", "rectangle")
        if self.width_internal_mm <= 0.0:
            raise InvalidComponentGeometryError("Rectangle width must be greater than zero.")
        if self.height_internal_mm <= 0.0:
            raise InvalidComponentGeometryError("Rectangle height must be greater than zero.")

    @classmethod
    def from_center(cls, **kwargs):
        registry = UnitRegistry()
        return cls(
            element_id=kwargs["element_id"],
            name=kwargs.get("name"),
            element_type="rectangle",
            material_id=kwargs.get("material_id"),
            metadata=dict(kwargs["metadata"]) if kwargs.get("metadata") is not None else None,
            width_internal_mm=registry.to_internal(float(kwargs["width"]), kwargs["width_unit"], Dimension.LENGTH),
            height_internal_mm=registry.to_internal(float(kwargs["height"]), kwargs["height_unit"], Dimension.LENGTH),
            center_y_internal_mm=registry.to_internal(float(kwargs["center_y"]), kwargs["center_y_unit"], Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(kwargs["center_z"]), kwargs["center_z_unit"], Dimension.LENGTH),
            rotation_deg=float(kwargs.get("rotation_deg", 0.0)),
        )

    @classmethod
    def from_bottom_left(cls, **kwargs):
        registry = UnitRegistry()
        width_mm = registry.to_internal(float(kwargs["width"]), kwargs["width_unit"], Dimension.LENGTH)
        height_mm = registry.to_internal(float(kwargs["height"]), kwargs["height_unit"], Dimension.LENGTH)
        bl_y = registry.to_internal(float(kwargs["bottom_left_y"]), kwargs["bottom_left_y_unit"], Dimension.LENGTH)
        bl_z = registry.to_internal(float(kwargs["bottom_left_z"]), kwargs["bottom_left_z_unit"], Dimension.LENGTH)
        return cls.from_center(
            element_id=kwargs["element_id"],
            width=width_mm,
            width_unit="mm",
            height=height_mm,
            height_unit="mm",
            center_y=bl_y + width_mm / 2.0,
            center_y_unit="mm",
            center_z=bl_z + height_mm / 2.0,
            center_z_unit="mm",
            rotation_deg=float(kwargs.get("rotation_deg", 0.0)),
            name=kwargs.get("name"),
            material_id=kwargs.get("material_id"),
            metadata=kwargs.get("metadata"),
        )

    def _corners(self) -> dict[str, SectionPoint]:
        hw = self.width_internal_mm / 2.0
        hh = self.height_internal_mm / 2.0
        local = {
            "bottom_left": (self.center_y_internal_mm - hw, self.center_z_internal_mm - hh),
            "bottom_right": (self.center_y_internal_mm + hw, self.center_z_internal_mm - hh),
            "top_right": (self.center_y_internal_mm + hw, self.center_z_internal_mm + hh),
            "top_left": (self.center_y_internal_mm - hw, self.center_z_internal_mm + hh),
        }
        transform = Transform2D.rotation(self.rotation_deg, self.center_y_internal_mm, self.center_z_internal_mm)
        return {
            name: SectionPoint.from_values(
                f"{self.element_id}_{name}",
                *transform.apply_to_coordinates(y, z),
                source_element_id=self.element_id,
                name=name,
            )
            for name, (y, z) in local.items()
        }

    def nodes(self) -> list[Node]:
        return [Node(node_id=f"{self.element_id}_{n}", name=n, y_internal_mm=p.y_internal_mm, z_internal_mm=p.z_internal_mm, element_id=self.element_id, node_type="vertex") for n, p in self._corners().items()]

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
        mid_bottom = SectionPoint.from_values(f"{self.element_id}_mid_bottom", (c["bottom_left"].y_internal_mm + c["bottom_right"].y_internal_mm)/2.0, (c["bottom_left"].z_internal_mm + c["bottom_right"].z_internal_mm)/2.0, source_element_id=self.element_id, name="mid_bottom")
        mid_top = SectionPoint.from_values(f"{self.element_id}_mid_top", (c["top_left"].y_internal_mm + c["top_right"].y_internal_mm)/2.0, (c["top_left"].z_internal_mm + c["top_right"].z_internal_mm)/2.0, source_element_id=self.element_id, name="mid_top")
        mid_left = SectionPoint.from_values(f"{self.element_id}_mid_left", (c["bottom_left"].y_internal_mm + c["top_left"].y_internal_mm)/2.0, (c["bottom_left"].z_internal_mm + c["top_left"].z_internal_mm)/2.0, source_element_id=self.element_id, name="mid_left")
        mid_right = SectionPoint.from_values(f"{self.element_id}_mid_right", (c["bottom_right"].y_internal_mm + c["top_right"].y_internal_mm)/2.0, (c["bottom_right"].z_internal_mm + c["top_right"].z_internal_mm)/2.0, source_element_id=self.element_id, name="mid_right")
        return {"center": center, **c, "mid_top": mid_top, "mid_bottom": mid_bottom, "mid_left": mid_left, "mid_right": mid_right}

    def reference_lines(self) -> dict[str, SectionLine]:
        lines = self.lines()
        return {"bottom_edge": lines[0], "right_edge": lines[1], "top_edge": lines[2], "left_edge": lines[3]}

    def area_mm2(self) -> float:
        return self.width_internal_mm * self.height_internal_mm

    def centroid_point(self) -> SectionPoint:
        return SectionPoint.from_values(f"{self.element_id}_center", self.center_y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="center")

    def bounding_box(self) -> tuple[float, float, float, float]:
        pts = list(self._corners().values())
        ys = [p.y_internal_mm for p in pts]
        zs = [p.z_internal_mm for p in pts]
        return (min(ys), min(zs), max(ys), max(zs))

    def transformed(self, transform: Transform2D) -> "RectangularElement":
        y, z = transform.apply_to_coordinates(self.center_y_internal_mm, self.center_z_internal_mm)
        metadata = dict(self.metadata) if self.metadata is not None else {}
        metadata.setdefault("transform_trace", []).append({
            "translation_dy_mm": transform.translation_dy_mm,
            "translation_dz_mm": transform.translation_dz_mm,
            "rotation_deg": transform.rotation_deg,
            "rotation_center_y_mm": transform.rotation_center_y_mm,
            "rotation_center_z_mm": transform.rotation_center_z_mm,
        })
        return RectangularElement(
            element_id=self.element_id,
            name=self.name,
            element_type=self.element_type,
            source=self.source,
            material_id=self.material_id,
            metadata=metadata,
            width_internal_mm=self.width_internal_mm,
            height_internal_mm=self.height_internal_mm,
            center_y_internal_mm=y,
            center_z_internal_mm=z,
            rotation_deg=self.rotation_deg + transform.rotation_deg,
        )

    def translated(self, dy_mm: float, dz_mm: float) -> "RectangularElement":
        return self.transformed(Transform2D.translation(dy_mm, dz_mm))

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
