"""Geometry tolerance configuration for section primitives."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import InvalidToleranceError


@dataclass(frozen=True)
class GeometryTolerance:
    """Absolute tolerances in internal mm-based coordinates."""

    point_merge_abs_tol_mm: float
    line_merge_abs_tol_mm: float
    parallel_abs_tol: float
    collinear_abs_tol_mm: float
    min_segment_length_mm: float

    def __post_init__(self) -> None:
        fields = {
            "point_merge_abs_tol_mm": self.point_merge_abs_tol_mm,
            "line_merge_abs_tol_mm": self.line_merge_abs_tol_mm,
            "parallel_abs_tol": self.parallel_abs_tol,
            "collinear_abs_tol_mm": self.collinear_abs_tol_mm,
            "min_segment_length_mm": self.min_segment_length_mm,
        }
        for name, value in fields.items():
            if value <= 0.0:
                raise InvalidToleranceError(f"{name} must be positive. Got: {value}")

    @classmethod
    def default(cls) -> "GeometryTolerance":
        return cls(
            point_merge_abs_tol_mm=1e-6,
            line_merge_abs_tol_mm=1e-6,
            parallel_abs_tol=1e-12,
            collinear_abs_tol_mm=1e-6,
            min_segment_length_mm=1e-9,
        )
