"""Moving-load envelope for simple-span crane runway beams (V1-022)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .analysis import SimpleSpanAnalysisResult, SimpleSpanRunwayBeamAnalyzer
from .errors import CraneRunwayError
from .loads import CraneWheelGroup


class MovingLoadEnvelopeError(CraneRunwayError):
    """Base error for moving-load envelope analysis."""


class InvalidEnvelopeStepError(MovingLoadEnvelopeError):
    """Invalid movement step definition."""


class WheelGroupLongerThanSpanError(MovingLoadEnvelopeError):
    """Wheel group does not fit inside analyzed span."""


@dataclass(frozen=True)
class MovingLoadPositionResult:
    offset_x_internal_mm: float
    shifted_wheel_group: CraneWheelGroup
    analysis_result: SimpleSpanAnalysisResult


@dataclass(frozen=True)
class MovingLoadEnvelopeResult:
    span_internal_mm: float
    position_results: list[MovingLoadPositionResult]
    max_left_reaction_N: float
    max_left_reaction_offset_x_mm: float
    max_right_reaction_N: float
    max_right_reaction_offset_x_mm: float
    max_shear_abs_N: float
    max_shear_abs_offset_x_mm: float
    max_moment_Nmm: float
    max_moment_x_mm: float
    max_moment_offset_x_mm: float
    metadata: dict | None = None

    def number_of_positions(self) -> int:
        return len(self.position_results)

    def critical_result_for_max_moment(self) -> MovingLoadPositionResult:
        return next(r for r in self.position_results if r.offset_x_internal_mm == self.max_moment_offset_x_mm)

    def critical_result_for_max_left_reaction(self) -> MovingLoadPositionResult:
        return next(r for r in self.position_results if r.offset_x_internal_mm == self.max_left_reaction_offset_x_mm)

    def critical_result_for_max_right_reaction(self) -> MovingLoadPositionResult:
        return next(r for r in self.position_results if r.offset_x_internal_mm == self.max_right_reaction_offset_x_mm)


class SimpleSpanMovingLoadEnvelopeAnalyzer:
    def __init__(
        self,
        span_internal_mm: float,
        step_internal_mm: float,
        simple_span_analyzer: SimpleSpanRunwayBeamAnalyzer | None = None,
        include_only_vertical: bool = True,
    ) -> None:
        if span_internal_mm <= 0:
            raise MovingLoadEnvelopeError("Span must be > 0.")
        if step_internal_mm <= 0:
            raise InvalidEnvelopeStepError("Step must be > 0.")

        self.span_internal_mm = span_internal_mm
        self.step_internal_mm = step_internal_mm
        self.include_only_vertical = include_only_vertical
        self.simple_span_analyzer = simple_span_analyzer or SimpleSpanRunwayBeamAnalyzer(
            span_internal_mm=span_internal_mm,
            include_only_vertical=include_only_vertical,
        )

    @classmethod
    def from_values(
        cls,
        span: float,
        span_unit: str = "mm",
        step: float = 1.0,
        step_unit: str = "mm",
        simple_span_analyzer: SimpleSpanRunwayBeamAnalyzer | None = None,
        include_only_vertical: bool = True,
    ) -> SimpleSpanMovingLoadEnvelopeAnalyzer:
        q_span = Quantity(span, span_unit, Dimension.LENGTH)
        q_step = Quantity(step, step_unit, Dimension.LENGTH)
        return cls(
            span_internal_mm=q_span.internal_value,
            step_internal_mm=q_step.internal_value,
            simple_span_analyzer=simple_span_analyzer,
            include_only_vertical=include_only_vertical,
        )

    def _offsets(self, offset_min: float, offset_max: float) -> list[float]:
        offsets: list[float] = []
        current = offset_min
        while current <= offset_max:
            offsets.append(current)
            current += self.step_internal_mm
        if not offsets or offsets[-1] != offset_max:
            offsets.append(offset_max)
        return sorted(set(offsets))

    def analyze_envelope(self, wheel_group: CraneWheelGroup) -> MovingLoadEnvelopeResult:
        if not wheel_group.wheels:
            raise MovingLoadEnvelopeError("Wheel group must not be empty.")

        x_min_group, x_max_group = wheel_group.bounding_x()
        group_length = x_max_group - x_min_group
        if group_length > self.span_internal_mm:
            raise WheelGroupLongerThanSpanError(
                f"Wheel group length {group_length} mm exceeds span {self.span_internal_mm} mm."
            )

        offset_min = -x_min_group
        offset_max = self.span_internal_mm - x_max_group
        offsets = self._offsets(offset_min, offset_max)

        position_results: list[MovingLoadPositionResult] = []
        for offset in offsets:
            shifted = wheel_group.translated(offset)
            result = self.simple_span_analyzer.analyze(shifted, metadata={"offset_x_internal_mm": offset})
            position_results.append(
                MovingLoadPositionResult(
                    offset_x_internal_mm=offset,
                    shifted_wheel_group=shifted,
                    analysis_result=result,
                )
            )

        max_left = max(position_results, key=lambda p: p.analysis_result.left_reaction_N)
        max_right = max(position_results, key=lambda p: p.analysis_result.right_reaction_N)
        max_shear = max(position_results, key=lambda p: p.analysis_result.max_shear_abs_N)
        max_moment = max(position_results, key=lambda p: p.analysis_result.max_moment_Nmm)

        return MovingLoadEnvelopeResult(
            span_internal_mm=self.span_internal_mm,
            position_results=position_results,
            max_left_reaction_N=max_left.analysis_result.left_reaction_N,
            max_left_reaction_offset_x_mm=max_left.offset_x_internal_mm,
            max_right_reaction_N=max_right.analysis_result.right_reaction_N,
            max_right_reaction_offset_x_mm=max_right.offset_x_internal_mm,
            max_shear_abs_N=max_shear.analysis_result.max_shear_abs_N,
            max_shear_abs_offset_x_mm=max_shear.offset_x_internal_mm,
            max_moment_Nmm=max_moment.analysis_result.max_moment_Nmm,
            max_moment_x_mm=max_moment.analysis_result.max_moment_x_mm,
            max_moment_offset_x_mm=max_moment.offset_x_internal_mm,
            metadata={
                "step_internal_mm": self.step_internal_mm,
                "offset_min_internal_mm": offset_min,
                "offset_max_internal_mm": offset_max,
                "include_only_vertical": self.include_only_vertical,
            },
        )
