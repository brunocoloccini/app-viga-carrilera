"""Station-based moving-load envelope curves for simple-span crane runway beams (V1-023)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .analysis import SimpleSpanRunwayBeamAnalyzer
from .envelope import InvalidEnvelopeStepError, WheelGroupLongerThanSpanError
from .errors import CraneRunwayError
from .loads import CraneWheelGroup


class EnvelopeCurveError(CraneRunwayError):
    """Base error for station-based envelope curve analysis."""


class InvalidEnvelopeStationError(EnvelopeCurveError):
    """Invalid station coordinate definition."""


@dataclass(frozen=True)
class EnvelopeCurvePoint:
    x_internal_mm: float
    max_shear_N: float
    max_shear_offset_x_mm: float
    min_shear_N: float
    min_shear_offset_x_mm: float
    max_shear_abs_N: float
    max_shear_abs_offset_x_mm: float
    max_moment_Nmm: float
    max_moment_offset_x_mm: float
    min_moment_Nmm: float
    min_moment_offset_x_mm: float


@dataclass(frozen=True)
class EnvelopeCurveResult:
    span_internal_mm: float
    station_points: list[EnvelopeCurvePoint]
    moving_offsets_mm: list[float]
    metadata: dict | None = None

    def station_count(self) -> int:
        return len(self.station_points)

    def global_max_moment(self) -> float:
        return max(point.max_moment_Nmm for point in self.station_points)

    def global_max_moment_point(self) -> EnvelopeCurvePoint:
        return max(self.station_points, key=lambda point: point.max_moment_Nmm)

    def global_max_shear_abs(self) -> float:
        return max(point.max_shear_abs_N for point in self.station_points)

    def global_max_shear_abs_point(self) -> EnvelopeCurvePoint:
        return max(self.station_points, key=lambda point: point.max_shear_abs_N)


class SimpleSpanEnvelopeCurveAnalyzer:
    def __init__(
        self,
        span_internal_mm: float,
        movement_step_internal_mm: float,
        station_step_internal_mm: float | None = None,
        station_internal_mm: list[float] | None = None,
        include_only_vertical: bool = True,
    ) -> None:
        if span_internal_mm <= 0:
            raise EnvelopeCurveError("Span must be > 0.")
        if movement_step_internal_mm <= 0:
            raise InvalidEnvelopeStepError("Movement step must be > 0.")
        if station_step_internal_mm is not None and station_step_internal_mm <= 0:
            raise InvalidEnvelopeStepError("Station step must be > 0.")

        self.span_internal_mm = span_internal_mm
        self.movement_step_internal_mm = movement_step_internal_mm
        self.station_step_internal_mm = station_step_internal_mm
        self.station_internal_mm = station_internal_mm
        self.include_only_vertical = include_only_vertical
        self.simple_span_analyzer = SimpleSpanRunwayBeamAnalyzer(
            span_internal_mm=span_internal_mm,
            include_only_vertical=include_only_vertical,
        )

    @classmethod
    def from_values(
        cls,
        span: float,
        span_unit: str = "mm",
        movement_step: float = 1.0,
        movement_step_unit: str = "mm",
        station_step: float | None = None,
        station_step_unit: str = "mm",
        stations: list[float] | None = None,
        station_unit: str = "mm",
        include_only_vertical: bool = True,
    ) -> SimpleSpanEnvelopeCurveAnalyzer:
        q_span = Quantity(span, span_unit, Dimension.LENGTH)
        q_movement_step = Quantity(movement_step, movement_step_unit, Dimension.LENGTH)
        q_station_step = Quantity(station_step, station_step_unit, Dimension.LENGTH) if station_step is not None else None
        q_stations = [Quantity(value, station_unit, Dimension.LENGTH).internal_value for value in stations] if stations else None

        return cls(
            span_internal_mm=q_span.internal_value,
            movement_step_internal_mm=q_movement_step.internal_value,
            station_step_internal_mm=q_station_step.internal_value if q_station_step is not None else None,
            station_internal_mm=q_stations,
            include_only_vertical=include_only_vertical,
        )

    def _offsets(self, offset_min: float, offset_max: float) -> list[float]:
        offsets: list[float] = []
        current = offset_min
        while current <= offset_max:
            offsets.append(current)
            current += self.movement_step_internal_mm
        if not offsets or offsets[-1] != offset_max:
            offsets.append(offset_max)
        return sorted(set(offsets))

    def _resolve_stations(self) -> list[float]:
        if self.station_internal_mm is not None:
            stations = sorted(set(self.station_internal_mm))
        else:
            step = self.station_step_internal_mm
            if step is None:
                step = self.span_internal_mm / 20.0
            stations = []
            current = 0.0
            while current <= self.span_internal_mm:
                stations.append(current)
                current += step
            if not stations or stations[-1] != self.span_internal_mm:
                stations.append(self.span_internal_mm)
            stations = sorted(set(stations))

        for station in stations:
            if station < 0 or station > self.span_internal_mm:
                raise InvalidEnvelopeStationError(
                    f"Station x={station} mm is outside span [0, {self.span_internal_mm}] mm."
                )
        return stations

    def analyze_curves(self, wheel_group: CraneWheelGroup) -> EnvelopeCurveResult:
        if not wheel_group.wheels:
            raise EnvelopeCurveError("Wheel group must not be empty.")

        x_min_group, x_max_group = wheel_group.bounding_x()
        group_length = x_max_group - x_min_group
        if group_length > self.span_internal_mm:
            raise WheelGroupLongerThanSpanError(
                f"Wheel group length {group_length} mm exceeds span {self.span_internal_mm} mm."
            )

        stations = self._resolve_stations()
        offset_min = -x_min_group
        offset_max = self.span_internal_mm - x_max_group
        offsets = self._offsets(offset_min, offset_max)

        points: list[EnvelopeCurvePoint] = []
        for station in stations:
            max_shear = float("-inf")
            min_shear = float("inf")
            max_shear_offset = offset_min
            min_shear_offset = offset_min
            max_shear_abs = float("-inf")
            max_shear_abs_offset = offset_min
            max_moment = float("-inf")
            min_moment = float("inf")
            max_moment_offset = offset_min
            min_moment_offset = offset_min

            for offset in offsets:
                shifted = wheel_group.translated(offset)
                shear = self.simple_span_analyzer.shear_at(station, shifted)
                moment = self.simple_span_analyzer.moment_at(station, shifted)

                if shear > max_shear:
                    max_shear = shear
                    max_shear_offset = offset
                if shear < min_shear:
                    min_shear = shear
                    min_shear_offset = offset

                shear_abs = abs(shear)
                if shear_abs > max_shear_abs:
                    max_shear_abs = shear_abs
                    max_shear_abs_offset = offset

                if moment > max_moment:
                    max_moment = moment
                    max_moment_offset = offset
                if moment < min_moment:
                    min_moment = moment
                    min_moment_offset = offset

            points.append(
                EnvelopeCurvePoint(
                    x_internal_mm=station,
                    max_shear_N=max_shear,
                    max_shear_offset_x_mm=max_shear_offset,
                    min_shear_N=min_shear,
                    min_shear_offset_x_mm=min_shear_offset,
                    max_shear_abs_N=max_shear_abs,
                    max_shear_abs_offset_x_mm=max_shear_abs_offset,
                    max_moment_Nmm=max_moment,
                    max_moment_offset_x_mm=max_moment_offset,
                    min_moment_Nmm=min_moment,
                    min_moment_offset_x_mm=min_moment_offset,
                )
            )

        return EnvelopeCurveResult(
            span_internal_mm=self.span_internal_mm,
            station_points=points,
            moving_offsets_mm=offsets,
            metadata={
                "movement_step_internal_mm": self.movement_step_internal_mm,
                "station_step_internal_mm": self.station_step_internal_mm,
                "offset_min_internal_mm": offset_min,
                "offset_max_internal_mm": offset_max,
                "include_only_vertical": self.include_only_vertical,
            },
        )
