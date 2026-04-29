"""Section line segment primitive."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import DegenerateGeometryError, GeometryMergeError
from .section_point import SectionPoint
from .tolerance import GeometryTolerance


@dataclass(frozen=True)
class SectionLine:
    line_id: str
    start: SectionPoint
    end: SectionPoint
    element_id: str | None = None
    metadata: dict[str, object] | None = None

    def __post_init__(self) -> None:
        tol = GeometryTolerance.default()
        if self.length_mm <= tol.min_segment_length_mm:
            raise DegenerateGeometryError(
                f"Line '{self.line_id}' is degenerate or too short (length={self.length_mm} mm)."
            )

    @property
    def length_mm(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def direction(self) -> tuple[float, float]:
        length = self.length_mm
        return (
            (self.end.y_internal_mm - self.start.y_internal_mm) / length,
            (self.end.z_internal_mm - self.start.z_internal_mm) / length,
        )

    @property
    def midpoint(self) -> SectionPoint:
        return SectionPoint(
            point_id=f"{self.line_id}_mid",
            y_internal_mm=(self.start.y_internal_mm + self.end.y_internal_mm) / 2.0,
            z_internal_mm=(self.start.z_internal_mm + self.end.z_internal_mm) / 2.0,
        )

    def contains_point(self, point: SectionPoint, tolerance: GeometryTolerance) -> bool:
        sy, sz = self.start.as_tuple()
        ey, ez = self.end.as_tuple()
        py, pz = point.as_tuple()

        vy, vz = ey - sy, ez - sz
        wy, wz = py - sy, pz - sz

        cross = abs(vy * wz - vz * wy)
        if cross > tolerance.collinear_abs_tol_mm * self.length_mm:
            return False

        dot = vy * wy + vz * wz
        if dot < -tolerance.line_merge_abs_tol_mm:
            return False
        if dot > (self.length_mm * self.length_mm) + tolerance.line_merge_abs_tol_mm:
            return False
        return True

    def is_parallel_to(self, other: "SectionLine", tolerance: GeometryTolerance) -> bool:
        dy1, dz1 = self.direction
        dy2, dz2 = other.direction
        return abs(dy1 * dz2 - dz1 * dy2) <= tolerance.parallel_abs_tol

    def is_collinear_with(self, other: "SectionLine", tolerance: GeometryTolerance) -> bool:
        if not self.is_parallel_to(other, tolerance):
            return False
        return self.contains_point(other.start, tolerance) or self.contains_point(other.end, tolerance)

    def can_merge_with(self, other: "SectionLine", tolerance: GeometryTolerance) -> bool:
        if not self.is_collinear_with(other, tolerance):
            return False
        oy = abs(self.direction[0]) >= abs(self.direction[1])
        a0 = self.start.y_internal_mm if oy else self.start.z_internal_mm
        a1 = self.end.y_internal_mm if oy else self.end.z_internal_mm
        b0 = other.start.y_internal_mm if oy else other.start.z_internal_mm
        b1 = other.end.y_internal_mm if oy else other.end.z_internal_mm
        amin, amax = min(a0, a1), max(a0, a1)
        bmin, bmax = min(b0, b1), max(b0, b1)
        return not (amax < bmin - tolerance.line_merge_abs_tol_mm or bmax < amin - tolerance.line_merge_abs_tol_mm)

    def merged_with(self, other: "SectionLine", tolerance: GeometryTolerance) -> "SectionLine":
        if not self.can_merge_with(other, tolerance):
            raise GeometryMergeError(f"Lines '{self.line_id}' and '{other.line_id}' cannot be merged.")

        points = [self.start, self.end, other.start, other.end]
        dy, dz = self.direction
        origin = self.start

        def scalar_projection(p: SectionPoint) -> float:
            return (p.y_internal_mm - origin.y_internal_mm) * dy + (p.z_internal_mm - origin.z_internal_mm) * dz

        ordered = sorted(points, key=scalar_projection)
        return SectionLine(
            line_id=f"{self.line_id}_merged_{other.line_id}",
            start=ordered[0],
            end=ordered[-1],
            element_id=self.element_id,
        )
