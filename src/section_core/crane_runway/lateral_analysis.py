"""Simple-span lateral analysis and elastic lateral bending stress (V1-028)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from section_core.section import GrossElasticProperties
from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .analysis import InvalidRunwaySpanError, WheelOutsideSpanError
from .errors import CraneRunwayError
from .loads import CraneWheelGroup


class CraneRunwayLateralAnalysisError(CraneRunwayError):
    """Base error for lateral crane runway analysis."""


class InvalidLateralMomentError(CraneRunwayLateralAnalysisError):
    """Lateral moment value is invalid for stress calculations."""


class InvalidLateralStressPropertiesError(CraneRunwayLateralAnalysisError):
    """Section weak-axis properties are invalid for lateral stress calculations."""


@dataclass(frozen=True)
class LateralAnalysisPoint:
    x_internal_mm: float
    lateral_shear_internal_N: float
    lateral_moment_internal_Nmm: float


@dataclass(frozen=True)
class SimpleSpanLateralAnalysisResult:
    span_internal_mm: float
    left_reaction_N: float
    right_reaction_N: float
    analysis_points: list[LateralAnalysisPoint]
    max_lateral_shear_abs_N: float
    max_lateral_moment_Nmm: float
    max_lateral_moment_x_mm: float
    metadata: dict | None = None

    def equilibrium_lateral_force_residual_N(self) -> float:
        if not self.metadata or "total_lateral_load_N" not in self.metadata:
            raise CraneRunwayLateralAnalysisError("Result metadata is missing 'total_lateral_load_N'.")
        return (self.left_reaction_N + self.right_reaction_N) - float(self.metadata["total_lateral_load_N"])

    def equilibrium_lateral_moment_residual_Nmm(self) -> float:
        if not self.metadata or "total_left_lateral_moment_Nmm" not in self.metadata:
            raise CraneRunwayLateralAnalysisError("Result metadata is missing 'total_left_lateral_moment_Nmm'.")
        return (self.right_reaction_N * self.span_internal_mm) - float(self.metadata["total_left_lateral_moment_Nmm"])


class SimpleSpanRunwayBeamLateralAnalyzer:
    def __init__(self, span_internal_mm: float) -> None:
        if span_internal_mm <= 0:
            raise InvalidRunwaySpanError("Span must be > 0.")
        self.span_internal_mm = span_internal_mm

    @classmethod
    def from_values(cls, span: float, span_unit: str = "mm") -> SimpleSpanRunwayBeamLateralAnalyzer:
        q_span = Quantity(span, span_unit, Dimension.LENGTH)
        return cls(span_internal_mm=q_span.internal_value)

    def _validate_wheels(self, wheel_group: CraneWheelGroup) -> None:
        if not wheel_group.wheels:
            raise CraneRunwayLateralAnalysisError("Wheel group must not be empty.")
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

    def _reactions(self, wheel_group: CraneWheelGroup) -> tuple[float, float]:
        total_lateral = sum(w.lateral_force_internal_N for w in wheel_group.wheels)
        right = sum(w.lateral_force_internal_N * w.position_x_internal_mm for w in wheel_group.wheels) / self.span_internal_mm
        left = total_lateral - right
        return left, right

    def lateral_shear_at(self, x: float, wheel_group: CraneWheelGroup) -> float:
        if not (0 <= x <= self.span_internal_mm):
            raise CraneRunwayLateralAnalysisError("Sample point is outside span.")
        left, _ = self._reactions(wheel_group)
        load_left = sum(w.lateral_force_internal_N for w in wheel_group.wheels if w.position_x_internal_mm <= x)
        return left - load_left

    def lateral_moment_at(self, x: float, wheel_group: CraneWheelGroup) -> float:
        if not (0 <= x <= self.span_internal_mm):
            raise CraneRunwayLateralAnalysisError("Sample point is outside span.")
        left, _ = self._reactions(wheel_group)
        applied = sum(
            w.lateral_force_internal_N * (x - w.position_x_internal_mm)
            for w in wheel_group.wheels
            if w.position_x_internal_mm <= x
        )
        return (left * x) - applied

    def analyze(self, wheel_group: CraneWheelGroup, sample_points: list[float] | None = None, metadata: dict | None = None) -> SimpleSpanLateralAnalysisResult:
        self._validate_wheels(wheel_group)
        points = self._default_sample_points(wheel_group) if sample_points is None else sample_points
        if any((x < 0 or x > self.span_internal_mm) for x in points):
            raise CraneRunwayLateralAnalysisError("All sample points must lie within [0, span].")

        left, right = self._reactions(wheel_group)
        analysis_points = [
            LateralAnalysisPoint(
                x_internal_mm=x,
                lateral_shear_internal_N=self.lateral_shear_at(x, wheel_group),
                lateral_moment_internal_Nmm=self.lateral_moment_at(x, wheel_group),
            )
            for x in sorted(set(points))
        ]
        max_shear_abs = max(abs(p.lateral_shear_internal_N) for p in analysis_points)
        max_moment_point = max(analysis_points, key=lambda p: p.lateral_moment_internal_Nmm)
        return SimpleSpanLateralAnalysisResult(
            span_internal_mm=self.span_internal_mm,
            left_reaction_N=left,
            right_reaction_N=right,
            analysis_points=analysis_points,
            max_lateral_shear_abs_N=max_shear_abs,
            max_lateral_moment_Nmm=max_moment_point.lateral_moment_internal_Nmm,
            max_lateral_moment_x_mm=max_moment_point.x_internal_mm,
            metadata={
                **(metadata or {}),
                "total_lateral_load_N": sum(w.lateral_force_internal_N for w in wheel_group.wheels),
                "total_left_lateral_moment_Nmm": sum(
                    w.lateral_force_internal_N * w.position_x_internal_mm for w in wheel_group.wheels
                ),
            },
        )


@dataclass(frozen=True)
class ElasticLateralBendingStressResult:
    result_id: str
    lateral_moment_Nmm: float
    x_internal_mm: float | None
    sigma_left_MPa: float
    sigma_right_MPa: float
    sigma_left_compression_or_tension_MPa: float
    sigma_right_compression_or_tension_MPa: float
    max_abs_lateral_stress_MPa: float
    S_z_left_mm3: float
    S_z_right_mm3: float
    metadata: dict | None = None


class ElasticLateralBendingStressAnalyzer:
    """Computes elastic normal stress from lateral bending moment about z-axis.

    Convention:
    - Uses weak-axis section moduli S_z_left and S_z_right.
    - Positive and negative moments preserve stress sign at left/right fibers.
    - Compression/tension magnitudes are always positive.
    """

    def __init__(self, gross_properties: GrossElasticProperties) -> None:
        self.gross_properties = gross_properties
        self._validate_gross_properties()

    def _require_float(self, value: float | int, name: str) -> float:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise InvalidLateralStressPropertiesError(f"{name} must be a numeric value.")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise InvalidLateralStressPropertiesError(f"{name} must be finite.")
        return numeric

    def _validate_gross_properties(self) -> None:
        if self.gross_properties is None:
            raise InvalidLateralStressPropertiesError("gross_properties is required.")
        s_left = self._require_float(self.gross_properties.S_z_left_mm3, "S_z_left_mm3")
        s_right = self._require_float(self.gross_properties.S_z_right_mm3, "S_z_right_mm3")
        izz = self._require_float(self.gross_properties.Izz_mm4, "Izz_mm4")
        if s_left <= 0:
            raise InvalidLateralStressPropertiesError("S_z_left_mm3 must be > 0.")
        if s_right <= 0:
            raise InvalidLateralStressPropertiesError("S_z_right_mm3 must be > 0.")
        if izz <= 0:
            raise InvalidLateralStressPropertiesError("Izz_mm4 must be > 0.")

    def _validate_moment(self, lateral_moment_Nmm: float | int) -> float:
        if not isinstance(lateral_moment_Nmm, int | float) or isinstance(lateral_moment_Nmm, bool):
            raise InvalidLateralMomentError("lateral_moment_Nmm must be a numeric value.")
        numeric = float(lateral_moment_Nmm)
        if not math.isfinite(numeric):
            raise InvalidLateralMomentError("lateral_moment_Nmm must be finite.")
        return numeric

    def stress_from_lateral_moment(self, lateral_moment_Nmm: float, result_id: str = "lateral_stress", x_internal_mm: float | None = None, metadata: dict | None = None) -> ElasticLateralBendingStressResult:
        m = self._validate_moment(lateral_moment_Nmm)
        sigma_left = m / self.gross_properties.S_z_left_mm3
        sigma_right = -m / self.gross_properties.S_z_right_mm3
        sigma_left_abs = abs(sigma_left)
        sigma_right_abs = abs(sigma_right)
        return ElasticLateralBendingStressResult(
            result_id=result_id,
            lateral_moment_Nmm=m,
            x_internal_mm=x_internal_mm,
            sigma_left_MPa=sigma_left,
            sigma_right_MPa=sigma_right,
            sigma_left_compression_or_tension_MPa=sigma_left_abs,
            sigma_right_compression_or_tension_MPa=sigma_right_abs,
            max_abs_lateral_stress_MPa=max(sigma_left_abs, sigma_right_abs),
            S_z_left_mm3=self.gross_properties.S_z_left_mm3,
            S_z_right_mm3=self.gross_properties.S_z_right_mm3,
            metadata=metadata,
        )

    def stress_from_lateral_analysis_result(self, analysis_result: SimpleSpanLateralAnalysisResult) -> ElasticLateralBendingStressResult:
        return self.stress_from_lateral_moment(
            lateral_moment_Nmm=analysis_result.max_lateral_moment_Nmm,
            result_id="fixed_lateral_analysis_stress",
            x_internal_mm=analysis_result.max_lateral_moment_x_mm,
            metadata={"analysis_type": "fixed_lateral", "analysis_metadata": analysis_result.metadata},
        )
