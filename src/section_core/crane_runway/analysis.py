"""Simple-span crane runway beam analysis (V1-021)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .errors import CraneRunwayError
from .loads import CraneWheelGroup


class CraneRunwayAnalysisError(CraneRunwayError):
    """Base error for crane runway beam analysis."""


class InvalidRunwaySpanError(CraneRunwayAnalysisError):
    """Invalid runway span definition."""


class WheelOutsideSpanError(CraneRunwayAnalysisError):
    """Wheel position falls outside the analyzed span."""


@dataclass(frozen=True)
class BeamAnalysisPoint:
    x_internal_mm: float
    shear_internal_N: float
    moment_internal_Nmm: float


@dataclass(frozen=True)
class SimpleSpanAnalysisResult:
    span_internal_mm: float
    left_reaction_N: float
    right_reaction_N: float
    analysis_points: list[BeamAnalysisPoint]
    max_shear_abs_N: float
    max_moment_Nmm: float
    max_moment_x_mm: float
    metadata: dict | None = None

    def equilibrium_vertical_force_residual_N(self) -> float:
        if not self.metadata or "total_vertical_load_N" not in self.metadata:
            raise CraneRunwayAnalysisError("Result metadata is missing 'total_vertical_load_N'.")
        return (self.left_reaction_N + self.right_reaction_N) - float(self.metadata["total_vertical_load_N"])

    def equilibrium_moment_residual_Nmm(self) -> float:
        if not self.metadata or "total_left_moment_Nmm" not in self.metadata:
            raise CraneRunwayAnalysisError("Result metadata is missing 'total_left_moment_Nmm'.")
        return (self.right_reaction_N * self.span_internal_mm) - float(self.metadata["total_left_moment_Nmm"])


class SimpleSpanRunwayBeamAnalyzer:
    def __init__(self, span_internal_mm: float, include_only_vertical: bool = True) -> None:
        if span_internal_mm <= 0:
            raise InvalidRunwaySpanError("Span must be > 0.")
        self.span_internal_mm = span_internal_mm
        self.include_only_vertical = include_only_vertical

    @classmethod
    def from_values(
        cls,
        span: float,
        span_unit: str = "mm",
        include_only_vertical: bool = True,
    ) -> SimpleSpanRunwayBeamAnalyzer:
        q_span = Quantity(span, span_unit, Dimension.LENGTH)
        return cls(span_internal_mm=q_span.internal_value, include_only_vertical=include_only_vertical)

    def _validate_wheels(self, wheel_group: CraneWheelGroup) -> None:
        if not wheel_group.wheels:
            raise CraneRunwayAnalysisError("Wheel group must not be empty.")
        for wheel in wheel_group.wheels:
            if not (0 <= wheel.position_x_internal_mm <= self.span_internal_mm):
                raise WheelOutsideSpanError(
                    f"Wheel '{wheel.wheel_id}' at x={wheel.position_x_internal_mm} mm is outside span [0, {self.span_internal_mm}] mm."
                )

    def _default_sample_points(self, wheel_group: CraneWheelGroup) -> list[float]:
        eps = 1e-6
        points: set[float] = {0.0, self.span_internal_mm}
        for wheel in wheel_group.wheels:
            x = wheel.position_x_internal_mm
            points.add(x)
            if x > 0:
                points.add(max(0.0, x - eps))
            if x < self.span_internal_mm:
                points.add(min(self.span_internal_mm, x + eps))
        return sorted(points)

    def _vertical_force(self, wheel) -> float:
        if self.include_only_vertical:
            return wheel.vertical_force_internal_N
        return wheel.vertical_force_internal_N

    def shear_at(self, x_internal_mm: float, wheel_group: CraneWheelGroup) -> float:
        if not (0 <= x_internal_mm <= self.span_internal_mm):
            raise CraneRunwayAnalysisError("Sample point is outside span.")
        r_left, _ = self._reactions(wheel_group)
        loads_left = sum(
            self._vertical_force(w) for w in wheel_group.wheels if w.position_x_internal_mm <= x_internal_mm
        )
        return r_left - loads_left

    def moment_at(self, x_internal_mm: float, wheel_group: CraneWheelGroup) -> float:
        if not (0 <= x_internal_mm <= self.span_internal_mm):
            raise CraneRunwayAnalysisError("Sample point is outside span.")
        r_left, _ = self._reactions(wheel_group)
        applied = sum(
            self._vertical_force(w) * (x_internal_mm - w.position_x_internal_mm)
            for w in wheel_group.wheels
            if w.position_x_internal_mm <= x_internal_mm
        )
        return r_left * x_internal_mm - applied

    def _reactions(self, wheel_group: CraneWheelGroup) -> tuple[float, float]:
        total_vertical = sum(self._vertical_force(w) for w in wheel_group.wheels)
        right = sum(self._vertical_force(w) * w.position_x_internal_mm for w in wheel_group.wheels) / self.span_internal_mm
        left = total_vertical - right
        return left, right

    def analyze(
        self,
        wheel_group: CraneWheelGroup,
        sample_points: list[float] | None = None,
        metadata: dict | None = None,
    ) -> SimpleSpanAnalysisResult:
        self._validate_wheels(wheel_group)
        points = self._default_sample_points(wheel_group) if sample_points is None else sample_points
        if any((x < 0 or x > self.span_internal_mm) for x in points):
            raise CraneRunwayAnalysisError("All sample points must lie within [0, span].")

        left, right = self._reactions(wheel_group)
        analysis_points = [
            BeamAnalysisPoint(
                x_internal_mm=x,
                shear_internal_N=self.shear_at(x, wheel_group),
                moment_internal_Nmm=self.moment_at(x, wheel_group),
            )
            for x in sorted(set(points))
        ]

        max_shear_abs = max(abs(p.shear_internal_N) for p in analysis_points)
        max_moment_point = max(analysis_points, key=lambda p: p.moment_internal_Nmm)

        return SimpleSpanAnalysisResult(
            span_internal_mm=self.span_internal_mm,
            left_reaction_N=left,
            right_reaction_N=right,
            analysis_points=analysis_points,
            max_shear_abs_N=max_shear_abs,
            max_moment_Nmm=max_moment_point.moment_internal_Nmm,
            max_moment_x_mm=max_moment_point.x_internal_mm,
            metadata={
                **(metadata or {}),
                "total_vertical_load_N": sum(self._vertical_force(w) for w in wheel_group.wheels),
                "total_left_moment_Nmm": sum(
                    self._vertical_force(w) * w.position_x_internal_mm for w in wheel_group.wheels
                ),
            },
        )
