"""Tabulated structural shape component.

This component stores trusted library properties (area/inertias/etc.) while exposing a
simple bounding-box reference geometry for assembly workflows.
"""

from __future__ import annotations

from dataclasses import dataclass

from section_core.geometry import Node, SectionLine, SectionPoint, Transform2D
from section_core.units import Dimension, UnitRegistry

from .base import SectionElement
from .errors import (
    InvalidComponentGeometryError,
    UnknownReferenceError,
    UnsupportedComponentOperationError,
)


@dataclass(frozen=True)
class LibraryShapeComponent(SectionElement):
    shape_family: str = ""
    shape_name: str = ""
    center_y_internal_mm: float = 0.0
    center_z_internal_mm: float = 0.0
    depth_internal_mm: float = 0.0
    width_internal_mm: float = 0.0
    area_tabulated_mm2: float = 0.0
    Iyy_tabulated_mm4: float = 0.0
    Izz_tabulated_mm4: float = 0.0
    Iyz_tabulated_mm4: float = 0.0
    weight_per_length: float | None = None
    J_mm4: float | None = None
    Cw_mm6: float | None = None
    S_y_top_mm3: float | None = None
    S_y_bottom_mm3: float | None = None
    S_z_left_mm3: float | None = None
    S_z_right_mm3: float | None = None
    rotation_deg: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "element_type", "library_shape")
        if self.source == "user_defined":
            object.__setattr__(self, "source", "library")
        if self.area_tabulated_mm2 <= 0.0:
            raise InvalidComponentGeometryError("Library shape area must be greater than zero.")
        if self.Iyy_tabulated_mm4 < 0.0:
            raise InvalidComponentGeometryError("Library shape Iyy must be non-negative.")
        if self.Izz_tabulated_mm4 < 0.0:
            raise InvalidComponentGeometryError("Library shape Izz must be non-negative.")
        if self.depth_internal_mm <= 0.0:
            raise InvalidComponentGeometryError("Library shape depth must be greater than zero.")
        if self.width_internal_mm <= 0.0:
            raise InvalidComponentGeometryError("Library shape width must be greater than zero.")
        if self.rotation_deg != 0.0:
            raise UnsupportedComponentOperationError(
                "LibraryShapeComponent rotation is not supported in V1-014. Use rotation_deg=0.0."
            )

    @classmethod
    def from_tabulated(cls, **kwargs) -> "LibraryShapeComponent":
        registry = UnitRegistry()
        return cls(
            element_id=kwargs["element_id"],
            name=kwargs.get("name"),
            source=kwargs.get("source", "library"),
            material_id=kwargs.get("material_id"),
            metadata=dict(kwargs["metadata"]) if kwargs.get("metadata") is not None else None,
            shape_family=kwargs["shape_family"],
            shape_name=kwargs["shape_name"],
            center_y_internal_mm=registry.to_internal(float(kwargs.get("center_y", 0.0)), kwargs.get("center_unit", "mm"), Dimension.LENGTH),
            center_z_internal_mm=registry.to_internal(float(kwargs.get("center_z", 0.0)), kwargs.get("center_unit", "mm"), Dimension.LENGTH),
            depth_internal_mm=registry.to_internal(float(kwargs["depth"]), kwargs["depth_unit"], Dimension.LENGTH),
            width_internal_mm=registry.to_internal(float(kwargs["width"]), kwargs["width_unit"], Dimension.LENGTH),
            area_tabulated_mm2=registry.to_internal(float(kwargs["area"]), kwargs["area_unit"], Dimension.AREA),
            Iyy_tabulated_mm4=registry.to_internal(float(kwargs["Iyy"]), kwargs["Iyy_unit"], Dimension.INERTIA),
            Izz_tabulated_mm4=registry.to_internal(float(kwargs["Izz"]), kwargs["Izz_unit"], Dimension.INERTIA),
            Iyz_tabulated_mm4=registry.to_internal(float(kwargs.get("Iyz", 0.0)), kwargs.get("Iyz_unit", "mm4"), Dimension.INERTIA),
            weight_per_length=kwargs.get("weight_per_length"),
            J_mm4=kwargs.get("J_mm4"),
            Cw_mm6=kwargs.get("Cw_mm6"),
            S_y_top_mm3=kwargs.get("S_y_top_mm3"),
            S_y_bottom_mm3=kwargs.get("S_y_bottom_mm3"),
            S_z_left_mm3=kwargs.get("S_z_left_mm3"),
            S_z_right_mm3=kwargs.get("S_z_right_mm3"),
            rotation_deg=float(kwargs.get("rotation_deg", 0.0)),
        )

    def _corners(self) -> dict[str, SectionPoint]:
        half_depth = self.depth_internal_mm / 2.0
        half_width = self.width_internal_mm / 2.0
        return {
            "bottom_left": SectionPoint.from_values(f"{self.element_id}_bottom_left", self.center_y_internal_mm - half_width, self.center_z_internal_mm - half_depth, source_element_id=self.element_id, name="bottom_left"),
            "bottom_right": SectionPoint.from_values(f"{self.element_id}_bottom_right", self.center_y_internal_mm + half_width, self.center_z_internal_mm - half_depth, source_element_id=self.element_id, name="bottom_right"),
            "top_right": SectionPoint.from_values(f"{self.element_id}_top_right", self.center_y_internal_mm + half_width, self.center_z_internal_mm + half_depth, source_element_id=self.element_id, name="top_right"),
            "top_left": SectionPoint.from_values(f"{self.element_id}_top_left", self.center_y_internal_mm - half_width, self.center_z_internal_mm + half_depth, source_element_id=self.element_id, name="top_left"),
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
        return {
            "center": self.centroid_point(),
            **c,
            "mid_top": SectionPoint.from_values(f"{self.element_id}_mid_top", self.center_y_internal_mm, c["top_left"].z_internal_mm, source_element_id=self.element_id, name="mid_top"),
            "mid_bottom": SectionPoint.from_values(f"{self.element_id}_mid_bottom", self.center_y_internal_mm, c["bottom_left"].z_internal_mm, source_element_id=self.element_id, name="mid_bottom"),
            "mid_left": SectionPoint.from_values(f"{self.element_id}_mid_left", c["bottom_left"].y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="mid_left"),
            "mid_right": SectionPoint.from_values(f"{self.element_id}_mid_right", c["bottom_right"].y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="mid_right"),
        }

    def reference_lines(self) -> dict[str, SectionLine]:
        refs = self.lines()
        return {
            "bottom_edge": refs[0],
            "right_edge": refs[1],
            "top_edge": refs[2],
            "left_edge": refs[3],
            "vertical_centerline": SectionLine(
                f"{self.element_id}_vertical_centerline",
                self.get_reference_point("mid_bottom"),
                self.get_reference_point("mid_top"),
                element_id=self.element_id,
            ),
            "horizontal_centerline": SectionLine(
                f"{self.element_id}_horizontal_centerline",
                self.get_reference_point("mid_left"),
                self.get_reference_point("mid_right"),
                element_id=self.element_id,
            ),
        }

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

    def bounding_box(self) -> tuple[float, float, float, float]:
        c = self._corners()
        return (c["bottom_left"].y_internal_mm, c["bottom_left"].z_internal_mm, c["top_right"].y_internal_mm, c["top_right"].z_internal_mm)

    def centroid_point(self) -> SectionPoint:
        return SectionPoint.from_values(f"{self.element_id}_center", self.center_y_internal_mm, self.center_z_internal_mm, source_element_id=self.element_id, name="center")

    def area_mm2(self) -> float:
        return self.area_tabulated_mm2

    def translated(self, dy_mm: float, dz_mm: float) -> "LibraryShapeComponent":
        return self.transformed(Transform2D.translation(dy_mm, dz_mm))

    def transformed(self, transform: Transform2D) -> "LibraryShapeComponent":
        if transform.rotation_deg != 0.0:
            raise UnsupportedComponentOperationError(
                "LibraryShapeComponent.transform supports translation only in V1-014 (rotation_deg must be 0.0)."
            )
        y, z = transform.apply_to_coordinates(self.center_y_internal_mm, self.center_z_internal_mm)
        return LibraryShapeComponent(
            element_id=self.element_id,
            name=self.name,
            source=self.source,
            material_id=self.material_id,
            metadata=dict(self.metadata) if self.metadata is not None else None,
            shape_family=self.shape_family,
            shape_name=self.shape_name,
            center_y_internal_mm=y,
            center_z_internal_mm=z,
            depth_internal_mm=self.depth_internal_mm,
            width_internal_mm=self.width_internal_mm,
            area_tabulated_mm2=self.area_tabulated_mm2,
            Iyy_tabulated_mm4=self.Iyy_tabulated_mm4,
            Izz_tabulated_mm4=self.Izz_tabulated_mm4,
            Iyz_tabulated_mm4=self.Iyz_tabulated_mm4,
            weight_per_length=self.weight_per_length,
            J_mm4=self.J_mm4,
            Cw_mm6=self.Cw_mm6,
            S_y_top_mm3=self.S_y_top_mm3,
            S_y_bottom_mm3=self.S_y_bottom_mm3,
            S_z_left_mm3=self.S_z_left_mm3,
            S_z_right_mm3=self.S_z_right_mm3,
            rotation_deg=0.0,
        )

    def local_reference(self) -> SectionPoint:
        return self.centroid_point()
