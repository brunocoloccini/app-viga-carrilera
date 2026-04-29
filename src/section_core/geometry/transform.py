"""2D transformations in the section Y-Z plane."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

from .point import Point2D
from .section_point import SectionPoint


@dataclass(frozen=True)
class Transform2D:
    translation_dy_mm: float = 0.0
    translation_dz_mm: float = 0.0
    rotation_deg: float = 0.0
    rotation_center_y_mm: float = 0.0
    rotation_center_z_mm: float = 0.0

    def apply_to_coordinates(self, y_mm: float, z_mm: float) -> tuple[float, float]:
        y = float(y_mm)
        z = float(z_mm)
        if self.rotation_deg != 0.0:
            theta = radians(self.rotation_deg)
            cy = self.rotation_center_y_mm
            cz = self.rotation_center_z_mm
            ry = y - cy
            rz = z - cz
            y = cy + (ry * cos(theta) - rz * sin(theta))
            z = cz + (ry * sin(theta) + rz * cos(theta))
        return (y + self.translation_dy_mm, z + self.translation_dz_mm)

    def apply_to_point(self, point: Point2D | SectionPoint) -> Point2D | SectionPoint:
        y, z = self.apply_to_coordinates(point.y_internal_mm, point.z_internal_mm)
        if isinstance(point, SectionPoint):
            return SectionPoint(
                y_internal_mm=y,
                z_internal_mm=z,
                point_id=point.point_id,
                name=point.name,
                source_element_id=point.source_element_id,
                metadata=dict(point.metadata) if point.metadata is not None else None,
            )
        return Point2D(y_internal_mm=y, z_internal_mm=z)

    def combine(self, other: "Transform2D") -> "Transform2D":
        """Return a transform that applies `self` then `other`.

        For reliability in V1-009, composition is limited to pure translations.
        """
        if self.rotation_deg != 0.0 or other.rotation_deg != 0.0:
            raise ValueError("Transform2D.combine currently supports translations only.")
        return Transform2D.translation(
            dy_mm=self.translation_dy_mm + other.translation_dy_mm,
            dz_mm=self.translation_dz_mm + other.translation_dz_mm,
        )

    @classmethod
    def identity(cls) -> "Transform2D":
        return cls()

    @classmethod
    def translation(cls, dy_mm: float, dz_mm: float) -> "Transform2D":
        return cls(translation_dy_mm=float(dy_mm), translation_dz_mm=float(dz_mm))

    @classmethod
    def rotation(cls, rotation_deg: float, center_y_mm: float = 0.0, center_z_mm: float = 0.0) -> "Transform2D":
        return cls(
            rotation_deg=float(rotation_deg),
            rotation_center_y_mm=float(center_y_mm),
            rotation_center_z_mm=float(center_z_mm),
        )
