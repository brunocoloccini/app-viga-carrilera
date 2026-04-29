"""Elastic biaxial stress combination for crane runway beams (V1-029)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from section_core.section import GrossElasticProperties

from .errors import CraneRunwayError


class CraneRunwayBiaxialStressError(CraneRunwayError):
    """Base error for runway biaxial stress calculations."""


class InvalidBiaxialStressPropertiesError(CraneRunwayBiaxialStressError):
    """Gross section properties are missing or invalid for biaxial stress calculations."""


class InvalidBiaxialMomentError(CraneRunwayBiaxialStressError):
    """Moment value is invalid for biaxial stress calculations."""


@dataclass(frozen=True)
class BiaxialStressAtPoint:
    point_id: str
    sigma_vertical_MPa: float
    sigma_lateral_MPa: float
    sigma_total_MPa: float
    metadata: dict | None = None


@dataclass(frozen=True)
class ElasticBiaxialStressResult:
    result_id: str
    vertical_moment_Nmm: float
    lateral_moment_Nmm: float
    points: list[BiaxialStressAtPoint]
    max_tension_MPa: float
    max_tension_point_id: str
    max_compression_MPa: float
    max_compression_point_id: str
    max_abs_stress_MPa: float
    max_abs_stress_point_id: str
    x_internal_mm: float | None = None
    metadata: dict | None = None


class ElasticBiaxialStressAnalyzer:
    """Computes elastic stress at representative corner points from My and Mz.

    Sign convention:
    - Tension is positive and compression is negative.
    - Positive vertical sagging moment is handled as top compression and bottom tension
      using absolute My for top/bottom magnitudes.
    - Lateral stress uses signed Mz:
      sigma_left = +Mz / S_z_left, sigma_right = -Mz / S_z_right.
    """

    def __init__(self, gross_properties: GrossElasticProperties) -> None:
        self.gross_properties = gross_properties
        self._validate_gross_properties()

    def _require_float(self, value: float | int, name: str) -> float:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise InvalidBiaxialStressPropertiesError(f"{name} must be a numeric value.")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise InvalidBiaxialStressPropertiesError(f"{name} must be finite.")
        return numeric

    def _validate_gross_properties(self) -> None:
        if self.gross_properties is None:
            raise InvalidBiaxialStressPropertiesError("gross_properties is required.")

        s_y_top = self._require_float(self.gross_properties.S_y_top_mm3, "S_y_top_mm3")
        s_y_bottom = self._require_float(self.gross_properties.S_y_bottom_mm3, "S_y_bottom_mm3")
        s_z_left = self._require_float(self.gross_properties.S_z_left_mm3, "S_z_left_mm3")
        s_z_right = self._require_float(self.gross_properties.S_z_right_mm3, "S_z_right_mm3")
        iyy = self._require_float(self.gross_properties.Iyy_mm4, "Iyy_mm4")
        izz = self._require_float(self.gross_properties.Izz_mm4, "Izz_mm4")

        if s_y_top <= 0:
            raise InvalidBiaxialStressPropertiesError("S_y_top_mm3 must be > 0.")
        if s_y_bottom <= 0:
            raise InvalidBiaxialStressPropertiesError("S_y_bottom_mm3 must be > 0.")
        if s_z_left <= 0:
            raise InvalidBiaxialStressPropertiesError("S_z_left_mm3 must be > 0.")
        if s_z_right <= 0:
            raise InvalidBiaxialStressPropertiesError("S_z_right_mm3 must be > 0.")
        if iyy <= 0:
            raise InvalidBiaxialStressPropertiesError("Iyy_mm4 must be > 0.")
        if izz <= 0:
            raise InvalidBiaxialStressPropertiesError("Izz_mm4 must be > 0.")

    def _validate_moment(self, value: float | int, name: str) -> float:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise InvalidBiaxialMomentError(f"{name} must be a numeric value.")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise InvalidBiaxialMomentError(f"{name} must be finite.")
        return numeric

    def stress_from_moments(
        self,
        vertical_moment_Nmm: float,
        lateral_moment_Nmm: float,
        result_id: str = "biaxial_stress",
        x_internal_mm: float | None = None,
        metadata: dict | None = None,
    ) -> ElasticBiaxialStressResult:
        my = self._validate_moment(vertical_moment_Nmm, "vertical_moment_Nmm")
        mz = self._validate_moment(lateral_moment_Nmm, "lateral_moment_Nmm")

        sigma_v_top = -abs(my) / self.gross_properties.S_y_top_mm3
        sigma_v_bottom = abs(my) / self.gross_properties.S_y_bottom_mm3
        sigma_l_left = mz / self.gross_properties.S_z_left_mm3
        sigma_l_right = -mz / self.gross_properties.S_z_right_mm3

        points = [
            BiaxialStressAtPoint("top_left", sigma_v_top, sigma_l_left, sigma_v_top + sigma_l_left),
            BiaxialStressAtPoint("top_right", sigma_v_top, sigma_l_right, sigma_v_top + sigma_l_right),
            BiaxialStressAtPoint("bottom_left", sigma_v_bottom, sigma_l_left, sigma_v_bottom + sigma_l_left),
            BiaxialStressAtPoint("bottom_right", sigma_v_bottom, sigma_l_right, sigma_v_bottom + sigma_l_right),
        ]

        max_tension = max(points, key=lambda p: p.sigma_total_MPa)
        max_compression = min(points, key=lambda p: p.sigma_total_MPa)
        max_abs = max(points, key=lambda p: abs(p.sigma_total_MPa))

        return ElasticBiaxialStressResult(
            result_id=result_id,
            x_internal_mm=x_internal_mm,
            vertical_moment_Nmm=my,
            lateral_moment_Nmm=mz,
            points=points,
            max_tension_MPa=max_tension.sigma_total_MPa,
            max_tension_point_id=max_tension.point_id,
            max_compression_MPa=max_compression.sigma_total_MPa,
            max_compression_point_id=max_compression.point_id,
            max_abs_stress_MPa=abs(max_abs.sigma_total_MPa),
            max_abs_stress_point_id=max_abs.point_id,
            metadata=metadata,
        )

    def stress_from_vertical_and_lateral_results(
        self,
        vertical_stress_result,
        lateral_stress_result,
        result_id: str = "biaxial_stress",
        metadata: dict | None = None,
    ) -> ElasticBiaxialStressResult:
        vertical_x = getattr(vertical_stress_result, "x_internal_mm", None)
        lateral_x = getattr(lateral_stress_result, "x_internal_mm", None)
        x_internal_mm = vertical_x if vertical_x is not None else lateral_x
        if vertical_x is not None and lateral_x is not None and not math.isclose(vertical_x, lateral_x):
            raise InvalidBiaxialMomentError("vertical and lateral stress results must refer to the same x_internal_mm.")

        return self.stress_from_moments(
            vertical_moment_Nmm=getattr(vertical_stress_result, "moment_Nmm"),
            lateral_moment_Nmm=getattr(lateral_stress_result, "lateral_moment_Nmm"),
            result_id=result_id,
            x_internal_mm=x_internal_mm,
            metadata=metadata,
        )
