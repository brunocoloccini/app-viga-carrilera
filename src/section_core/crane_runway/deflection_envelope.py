"""Moving-load deflection envelope for simple-span crane runway beams (V1-025)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .deflection import SimpleSpanDeflectionResult, SimpleSpanRunwayBeamDeflectionAnalyzer
from .envelope import WheelGroupLongerThanSpanError
from .errors import CraneRunwayError
from .loads import CraneWheelGroup


class DeflectionEnvelopeError(CraneRunwayError):
    """Base error for moving-load deflection envelope analysis."""


class InvalidDeflectionEnvelopeStepError(DeflectionEnvelopeError):
    """Invalid movement/station step definition."""


class InvalidDeflectionEnvelopeStationError(DeflectionEnvelopeError):
    """Invalid station position for deflection envelope analysis."""


@dataclass(frozen=True)
class MovingDeflectionPositionResult:
    offset_x_internal_mm: float
    shifted_wheel_group: CraneWheelGroup
    deflection_result: SimpleSpanDeflectionResult


@dataclass(frozen=True)
class DeflectionEnvelopeStationPoint:
    x_internal_mm: float
    max_deflection_mm: float
    max_deflection_offset_x_mm: float
    min_deflection_mm: float
    min_deflection_offset_x_mm: float


@dataclass(frozen=True)
class MovingDeflectionEnvelopeResult:
    span_internal_mm: float
    E_internal_MPa: float
    I_internal_mm4: float
    position_results: list[MovingDeflectionPositionResult]
    station_points: list[DeflectionEnvelopeStationPoint]
    moving_offsets_mm: list[float]
    max_deflection_mm: float
    max_deflection_x_mm: float
    max_deflection_offset_x_mm: float
    metadata: dict | None = None

    def number_of_positions(self) -> int:
        return len(self.position_results)

    def station_count(self) -> int:
        return len(self.station_points)

    def critical_result_for_max_deflection(self) -> MovingDeflectionPositionResult:
        return next(r for r in self.position_results if r.offset_x_internal_mm == self.max_deflection_offset_x_mm)

    def global_max_deflection_point(self) -> DeflectionEnvelopeStationPoint:
        return next(p for p in self.station_points if p.x_internal_mm == self.max_deflection_x_mm)


class SimpleSpanMovingDeflectionEnvelopeAnalyzer:
    def __init__(
        self,
        span_internal_mm: float,
        E_internal_MPa: float,
        I_internal_mm4: float,
        movement_step_internal_mm: float,
        station_step_internal_mm: float | None = None,
        stations_internal_mm: list[float] | None = None,
        include_only_vertical: bool = True,
    ) -> None:
        if span_internal_mm <= 0:
            raise DeflectionEnvelopeError("Span must be > 0.")
        if E_internal_MPa <= 0:
            raise DeflectionEnvelopeError("E must be > 0.")
        if I_internal_mm4 <= 0:
            raise DeflectionEnvelopeError("I must be > 0.")
        if movement_step_internal_mm <= 0:
            raise InvalidDeflectionEnvelopeStepError("Movement step must be > 0.")
        if station_step_internal_mm is not None and station_step_internal_mm <= 0:
            raise InvalidDeflectionEnvelopeStepError("Station step must be > 0.")

        self.span_internal_mm = span_internal_mm
        self.E_internal_MPa = E_internal_MPa
        self.I_internal_mm4 = I_internal_mm4
        self.movement_step_internal_mm = movement_step_internal_mm
        self.station_step_internal_mm = station_step_internal_mm
        self.stations_internal_mm = stations_internal_mm
        self.include_only_vertical = include_only_vertical
        self.deflection_analyzer = SimpleSpanRunwayBeamDeflectionAnalyzer(
            span_internal_mm=span_internal_mm,
            E_internal_MPa=E_internal_MPa,
            I_internal_mm4=I_internal_mm4,
        )

    @classmethod
    def from_values(
        cls,
        span: float,
        span_unit: str = "mm",
        E: float = 200000,
        E_unit: str = "MPa",
        I: float | None = None,
        I_unit: str = "mm4",
        movement_step: float | None = None,
        movement_step_unit: str = "mm",
        station_step: float | None = None,
        station_step_unit: str = "mm",
        stations: list[float] | None = None,
        station_unit: str = "mm",
    ) -> SimpleSpanMovingDeflectionEnvelopeAnalyzer:
        if I is None:
            raise DeflectionEnvelopeError("I is required.")
        if movement_step is None:
            raise DeflectionEnvelopeError("movement_step is required.")

        q_span = Quantity(span, span_unit, Dimension.LENGTH)
        q_E = Quantity(E, E_unit, Dimension.STRESS)
        q_I = Quantity(I, I_unit, Dimension.INERTIA)
        q_move = Quantity(movement_step, movement_step_unit, Dimension.LENGTH)
        q_station_step = Quantity(station_step, station_step_unit, Dimension.LENGTH) if station_step is not None else None
        q_stations = [Quantity(x, station_unit, Dimension.LENGTH).internal_value for x in stations] if stations is not None else None

        return cls(
            span_internal_mm=q_span.internal_value,
            E_internal_MPa=q_E.internal_value,
            I_internal_mm4=q_I.internal_value,
            movement_step_internal_mm=q_move.internal_value,
            station_step_internal_mm=q_station_step.internal_value if q_station_step is not None else None,
            stations_internal_mm=q_stations,
        )

    def _generate_positions(self, start_mm: float, end_mm: float, step_mm: float) -> list[float]:
        points: list[float] = []
        current = start_mm
        while current <= end_mm:
            points.append(current)
            current += step_mm
        if not points or points[-1] != end_mm:
            points.append(end_mm)
        return sorted(set(points))

    def _stations(self) -> list[float]:
        if self.stations_internal_mm is not None:
            stations = sorted(set(self.stations_internal_mm))
            for x in stations:
                if not (0 <= x <= self.span_internal_mm):
                    raise InvalidDeflectionEnvelopeStationError(
                        f"Station x={x} mm is outside span [0, {self.span_internal_mm}] mm."
                    )
            return stations

        step = self.station_step_internal_mm if self.station_step_internal_mm is not None else self.span_internal_mm / 20.0
        if step <= 0:
            raise InvalidDeflectionEnvelopeStepError("Station step must be > 0.")
        return self._generate_positions(0.0, self.span_internal_mm, step)

    def analyze_envelope(self, wheel_group: CraneWheelGroup) -> MovingDeflectionEnvelopeResult:
        x_min_group, x_max_group = wheel_group.bounding_x()
        group_length = x_max_group - x_min_group
        if group_length > self.span_internal_mm:
            raise WheelGroupLongerThanSpanError(
                f"Wheel group length {group_length} mm exceeds span {self.span_internal_mm} mm."
            )

        offset_min = -x_min_group
        offset_max = self.span_internal_mm - x_max_group
        offsets = self._generate_positions(offset_min, offset_max, self.movement_step_internal_mm)
        stations = self._stations()

        position_results: list[MovingDeflectionPositionResult] = []
        for offset in offsets:
            shifted = wheel_group.translated(offset)
            defl = self.deflection_analyzer.analyze(shifted, sample_points=stations)
            position_results.append(MovingDeflectionPositionResult(offset, shifted, defl))

        station_points: list[DeflectionEnvelopeStationPoint] = []
        for x in stations:
            values = [(pr.offset_x_internal_mm, pr.deflection_result.deflection_at(x)) for pr in position_results]
            max_offset, max_defl = max(values, key=lambda t: t[1])
            min_offset, min_defl = min(values, key=lambda t: t[1])
            station_points.append(
                DeflectionEnvelopeStationPoint(
                    x_internal_mm=x,
                    max_deflection_mm=max_defl,
                    max_deflection_offset_x_mm=max_offset,
                    min_deflection_mm=min_defl,
                    min_deflection_offset_x_mm=min_offset,
                )
            )

        max_station = max(station_points, key=lambda p: p.max_deflection_mm)
        return MovingDeflectionEnvelopeResult(
            span_internal_mm=self.span_internal_mm,
            E_internal_MPa=self.E_internal_MPa,
            I_internal_mm4=self.I_internal_mm4,
            position_results=position_results,
            station_points=station_points,
            moving_offsets_mm=offsets,
            max_deflection_mm=max_station.max_deflection_mm,
            max_deflection_x_mm=max_station.x_internal_mm,
            max_deflection_offset_x_mm=max_station.max_deflection_offset_x_mm,
            metadata={
                "movement_step_internal_mm": self.movement_step_internal_mm,
                "station_step_internal_mm": self.station_step_internal_mm,
                "offset_min_internal_mm": offset_min,
                "offset_max_internal_mm": offset_max,
                "include_only_vertical": self.include_only_vertical,
            },
        )
