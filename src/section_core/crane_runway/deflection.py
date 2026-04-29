"""Simple-span crane runway beam deflection analysis (V1-024).

Sign convention:
- Positive vertical wheel load is downward.
- Positive deflection is downward.
"""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .analysis import InvalidRunwaySpanError, WheelOutsideSpanError
from .errors import CraneRunwayError
from .loads import CraneWheelGroup


class CraneRunwayDeflectionError(CraneRunwayError):
    """Base error for crane runway beam deflection analysis."""


class InvalidFlexuralRigidityError(CraneRunwayDeflectionError):
    """Invalid E or I used for beam deflection analysis."""


class DeflectionSamplePointError(CraneRunwayDeflectionError):
    """Requested/sample deflection position is outside the beam span."""


@dataclass(frozen=True)
class DeflectionAnalysisPoint:
    x_internal_mm: float
    deflection_internal_mm: float


@dataclass(frozen=True)
class SimpleSpanDeflectionResult:
    span_internal_mm: float
    E_internal_MPa: float
    I_internal_mm4: float
    deflection_points: list[DeflectionAnalysisPoint]
    max_deflection_mm: float
    max_deflection_x_mm: float
    metadata: dict | None = None

    def deflection_at(self, x_mm: float) -> float:
        for point in self.deflection_points:
            if point.x_internal_mm == x_mm:
                return point.deflection_internal_mm

        calc_fn = (self.metadata or {}).get("deflection_at_calculator")
        if calc_fn is None:
            raise CraneRunwayDeflectionError(
                "No exact deflection point stored at this x and no calculator is available in result metadata."
            )
        return float(calc_fn(x_mm))


class SimpleSpanRunwayBeamDeflectionAnalyzer:
    def __init__(self, span_internal_mm: float, E_internal_MPa: float, I_internal_mm4: float) -> None:
        if span_internal_mm <= 0:
            raise InvalidRunwaySpanError("Span must be > 0.")
        if E_internal_MPa <= 0:
            raise InvalidFlexuralRigidityError("E must be > 0.")
        if I_internal_mm4 <= 0:
            raise InvalidFlexuralRigidityError("I must be > 0.")

        self.span_internal_mm = span_internal_mm
        self.E_internal_MPa = E_internal_MPa
        self.I_internal_mm4 = I_internal_mm4

    @classmethod
    def from_values(
        cls,
        span: float,
        span_unit: str = "mm",
        E: float = 0.0,
        E_unit: str = "MPa",
        I: float = 0.0,
        I_unit: str = "mm4",
    ) -> SimpleSpanRunwayBeamDeflectionAnalyzer:
        q_span = Quantity(span, span_unit, Dimension.LENGTH)
        q_e = Quantity(E, E_unit, Dimension.STRESS)
        q_i = Quantity(I, I_unit, Dimension.INERTIA)
        return cls(
            span_internal_mm=q_span.internal_value,
            E_internal_MPa=q_e.internal_value,
            I_internal_mm4=q_i.internal_value,
        )

    def _validate_wheels(self, wheel_group: CraneWheelGroup) -> None:
        if not wheel_group.wheels:
            raise CraneRunwayDeflectionError("Wheel group must not be empty.")
        for wheel in wheel_group.wheels:
            if not (0 <= wheel.position_x_internal_mm <= self.span_internal_mm):
                raise WheelOutsideSpanError(
                    f"Wheel '{wheel.wheel_id}' at x={wheel.position_x_internal_mm} mm is outside span [0, {self.span_internal_mm}] mm."
                )

    def _validate_x(self, x_internal_mm: float) -> None:
        if not (0 <= x_internal_mm <= self.span_internal_mm):
            raise DeflectionSamplePointError(
                f"Deflection sample point x={x_internal_mm} mm is outside span [0, {self.span_internal_mm}] mm."
            )

    def _point_load_deflection(self, P_N: float, a_mm: float, x_mm: float) -> float:
        L = self.span_internal_mm
        b = L - a_mm
        denom = 6.0 * L * self.E_internal_MPa * self.I_internal_mm4

        if x_mm <= a_mm:
            return (P_N * b * x_mm / denom) * (L * L - b * b - x_mm * x_mm)
        return (P_N * a_mm * (L - x_mm) / denom) * (L * L - a_mm * a_mm - (L - x_mm) * (L - x_mm))

    def deflection_at(self, x_internal_mm: float, wheel_group: CraneWheelGroup) -> float:
        self._validate_wheels(wheel_group)
        self._validate_x(x_internal_mm)
        return sum(
            self._point_load_deflection(w.vertical_force_internal_N, w.position_x_internal_mm, x_internal_mm)
            for w in wheel_group.wheels
        )

    def _default_sample_points(self, wheel_group: CraneWheelGroup) -> list[float]:
        L = self.span_internal_mm
        stations = [i * L / 20.0 for i in range(21)]
        points = set(stations)
        points.update([0.0, L, L / 2.0])
        points.update(w.position_x_internal_mm for w in wheel_group.wheels)
        return sorted(points)

    def analyze(self, wheel_group: CraneWheelGroup, sample_points: list[float] | None = None) -> SimpleSpanDeflectionResult:
        self._validate_wheels(wheel_group)
        points = self._default_sample_points(wheel_group) if sample_points is None else sorted(set(sample_points))
        for x in points:
            self._validate_x(x)

        deflection_points = [
            DeflectionAnalysisPoint(x_internal_mm=x, deflection_internal_mm=self.deflection_at(x, wheel_group)) for x in points
        ]
        max_point = max(deflection_points, key=lambda p: p.deflection_internal_mm)

        return SimpleSpanDeflectionResult(
            span_internal_mm=self.span_internal_mm,
            E_internal_MPa=self.E_internal_MPa,
            I_internal_mm4=self.I_internal_mm4,
            deflection_points=deflection_points,
            max_deflection_mm=max_point.deflection_internal_mm,
            max_deflection_x_mm=max_point.x_internal_mm,
            metadata={
                "wheel_group_id": wheel_group.group_id,
                "deflection_at_calculator": lambda x_mm: self.deflection_at(float(x_mm), wheel_group),
            },
        )
