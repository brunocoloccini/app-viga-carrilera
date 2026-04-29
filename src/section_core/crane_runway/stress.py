"""Elastic vertical bending stress utilities for crane runway beams (V1-027)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from section_core.section import GrossElasticProperties

from .analysis import SimpleSpanAnalysisResult
from .envelope import MovingLoadEnvelopeResult
from .envelope_curves import EnvelopeCurvePoint, EnvelopeCurveResult
from .errors import CraneRunwayError


class CraneRunwayStressError(CraneRunwayError):
    """Base error for runway stress calculations."""


class InvalidSectionStressPropertiesError(CraneRunwayStressError):
    """Gross section properties are missing or invalid for stress calculations."""


class InvalidMomentForStressError(CraneRunwayStressError):
    """Moment value is invalid for stress calculations."""


@dataclass(frozen=True)
class ElasticBendingStressResult:
    result_id: str
    moment_Nmm: float
    x_internal_mm: float | None
    sigma_top_MPa: float
    sigma_bottom_MPa: float
    sigma_top_compression_MPa: float
    sigma_bottom_tension_MPa: float
    max_abs_stress_MPa: float
    S_y_top_mm3: float
    S_y_bottom_mm3: float
    metadata: dict | None = None


@dataclass(frozen=True)
class ElasticStressEnvelopePoint:
    x_internal_mm: float
    max_moment_Nmm: float
    max_moment_offset_x_mm: float
    sigma_top_compression_MPa: float
    sigma_bottom_tension_MPa: float
    max_abs_stress_MPa: float
    metadata: dict | None = None


@dataclass(frozen=True)
class ElasticStressEnvelopeResult:
    envelope_id: str
    station_points: list[ElasticStressEnvelopePoint]
    global_max_abs_stress_MPa: float
    global_max_abs_stress_x_mm: float
    global_max_abs_stress_offset_x_mm: float
    metadata: dict | None = None

    def station_count(self) -> int:
        return len(self.station_points)

    def global_critical_point(self) -> ElasticStressEnvelopePoint:
        return next(
            point
            for point in self.station_points
            if point.x_internal_mm == self.global_max_abs_stress_x_mm
            and point.max_moment_offset_x_mm == self.global_max_abs_stress_offset_x_mm
            and point.max_abs_stress_MPa == self.global_max_abs_stress_MPa
        )


class ElasticVerticalBendingStressAnalyzer:
    """Computes elastic normal stress from vertical bending moment and gross section modulus.

    Convention:
    - Positive moment (sagging) => top compression, bottom tension.
    - Signed stresses preserve this convention (top negative in compression).
    - Magnitudes are always returned as positive values.
    """

    def __init__(self, gross_properties: GrossElasticProperties) -> None:
        self.gross_properties = gross_properties
        self._validate_gross_properties()

    def _require_float(self, value: float | int, name: str) -> float:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise InvalidSectionStressPropertiesError(f"{name} must be a numeric value.")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise InvalidSectionStressPropertiesError(f"{name} must be finite.")
        return numeric

    def _validate_gross_properties(self) -> None:
        if self.gross_properties is None:
            raise InvalidSectionStressPropertiesError("gross_properties is required.")

        gp = self.gross_properties
        s_top = self._require_float(gp.S_y_top_mm3, "S_y_top_mm3")
        s_bottom = self._require_float(gp.S_y_bottom_mm3, "S_y_bottom_mm3")
        iyy = self._require_float(gp.Iyy_mm4, "Iyy_mm4")
        y_min = self._require_float(gp.y_min_mm, "y_min_mm")
        y_max = self._require_float(gp.y_max_mm, "y_max_mm")
        centroid = self._require_float(gp.centroid_y_mm, "centroid_y_mm")

        if s_top <= 0:
            raise InvalidSectionStressPropertiesError("S_y_top_mm3 must be > 0.")
        if s_bottom <= 0:
            raise InvalidSectionStressPropertiesError("S_y_bottom_mm3 must be > 0.")
        if iyy <= 0:
            raise InvalidSectionStressPropertiesError("Iyy_mm4 must be > 0.")
        if y_min >= y_max:
            raise InvalidSectionStressPropertiesError("Section y-extents are invalid: y_min_mm must be < y_max_mm.")
        if not (y_min <= centroid <= y_max):
            raise InvalidSectionStressPropertiesError("centroid_y_mm must lie within [y_min_mm, y_max_mm].")

    def _validate_moment(self, moment_Nmm: float | int) -> float:
        if not isinstance(moment_Nmm, int | float) or isinstance(moment_Nmm, bool):
            raise InvalidMomentForStressError("moment_Nmm must be a numeric value.")
        numeric = float(moment_Nmm)
        if not math.isfinite(numeric):
            raise InvalidMomentForStressError("moment_Nmm must be finite.")
        return numeric

    def stress_from_moment(
        self,
        moment_Nmm: float,
        result_id: str = "stress",
        x_internal_mm: float | None = None,
        metadata: dict | None = None,
    ) -> ElasticBendingStressResult:
        m = self._validate_moment(moment_Nmm)
        m_abs = abs(m)

        sigma_top_compression = m_abs / self.gross_properties.S_y_top_mm3
        sigma_bottom_tension = m_abs / self.gross_properties.S_y_bottom_mm3

        if m >= 0:
            sigma_top = -sigma_top_compression
            sigma_bottom = sigma_bottom_tension
        else:
            sigma_top = sigma_top_compression
            sigma_bottom = -sigma_bottom_tension

        return ElasticBendingStressResult(
            result_id=result_id,
            moment_Nmm=m,
            x_internal_mm=x_internal_mm,
            sigma_top_MPa=sigma_top,
            sigma_bottom_MPa=sigma_bottom,
            sigma_top_compression_MPa=sigma_top_compression,
            sigma_bottom_tension_MPa=sigma_bottom_tension,
            max_abs_stress_MPa=max(sigma_top_compression, sigma_bottom_tension),
            S_y_top_mm3=self.gross_properties.S_y_top_mm3,
            S_y_bottom_mm3=self.gross_properties.S_y_bottom_mm3,
            metadata=metadata,
        )

    def stress_from_fixed_analysis_result(self, analysis_result: SimpleSpanAnalysisResult) -> ElasticBendingStressResult:
        return self.stress_from_moment(
            moment_Nmm=analysis_result.max_moment_Nmm,
            result_id="fixed_analysis_stress",
            x_internal_mm=analysis_result.max_moment_x_mm,
            metadata={"analysis_type": "fixed", "analysis_metadata": analysis_result.metadata},
        )

    def stress_from_moving_envelope_result(self, envelope_result: MovingLoadEnvelopeResult) -> ElasticBendingStressResult:
        return self.stress_from_moment(
            moment_Nmm=envelope_result.max_moment_Nmm,
            result_id="moving_envelope_stress",
            x_internal_mm=envelope_result.max_moment_x_mm,
            metadata={
                "analysis_type": "moving_envelope",
                "max_moment_offset_x_mm": envelope_result.max_moment_offset_x_mm,
                "envelope_metadata": envelope_result.metadata,
            },
        )

    def _point_from_curve_station(self, point: EnvelopeCurvePoint) -> ElasticStressEnvelopePoint:
        stress = self.stress_from_moment(moment_Nmm=point.max_moment_Nmm, x_internal_mm=point.x_internal_mm)
        return ElasticStressEnvelopePoint(
            x_internal_mm=point.x_internal_mm,
            max_moment_Nmm=point.max_moment_Nmm,
            max_moment_offset_x_mm=point.max_moment_offset_x_mm,
            sigma_top_compression_MPa=stress.sigma_top_compression_MPa,
            sigma_bottom_tension_MPa=stress.sigma_bottom_tension_MPa,
            max_abs_stress_MPa=stress.max_abs_stress_MPa,
            metadata={"source": "envelope_curve_station"},
        )

    def stress_envelope_from_curve_result(
        self,
        curve_result: EnvelopeCurveResult,
        envelope_id: str = "stress_envelope",
    ) -> ElasticStressEnvelopeResult:
        station_points = [self._point_from_curve_station(p) for p in curve_result.station_points]
        critical = max(station_points, key=lambda p: p.max_abs_stress_MPa)
        return ElasticStressEnvelopeResult(
            envelope_id=envelope_id,
            station_points=station_points,
            global_max_abs_stress_MPa=critical.max_abs_stress_MPa,
            global_max_abs_stress_x_mm=critical.x_internal_mm,
            global_max_abs_stress_offset_x_mm=critical.max_moment_offset_x_mm,
            metadata={"curve_metadata": curve_result.metadata},
        )
