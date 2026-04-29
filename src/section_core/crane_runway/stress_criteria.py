"""Generic elastic stress utilization criteria/checking for crane runway stress results (V1-030)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity


class StressCriteriaError(ValueError):
    """Base error for stress criteria/checking."""


class InvalidStressLimitError(StressCriteriaError):
    """Invalid stress limit definition."""


class DuplicateStressLimitError(StressCriteriaError):
    """Duplicate stress limit identifiers in one criteria set."""


@dataclass(frozen=True)
class StressLimit:
    limit_id: str
    limit_type: str
    description: str | None = None
    allowable_stress_internal_MPa: float | None = None
    Fy_internal_MPa: float | None = None
    factor: float | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.limit_id:
            raise InvalidStressLimitError("limit_id is required.")
        if self.limit_type not in {"absolute", "fraction_of_Fy"}:
            raise InvalidStressLimitError(f"Unsupported limit_type: {self.limit_type}")
        if self.limit_type == "absolute":
            if self.allowable_stress_internal_MPa is None or self.allowable_stress_internal_MPa <= 0:
                raise InvalidStressLimitError("allowable_stress_internal_MPa must be > 0 for absolute limits.")
        if self.limit_type == "fraction_of_Fy":
            if self.Fy_internal_MPa is None or self.Fy_internal_MPa <= 0:
                raise InvalidStressLimitError("Fy_internal_MPa must be > 0 for fraction_of_Fy limits.")
            if self.factor is None or self.factor <= 0:
                raise InvalidStressLimitError("factor must be > 0 for fraction_of_Fy limits.")

    @classmethod
    def absolute(
        cls,
        limit_id: str,
        value: float,
        unit: str = "MPa",
        description: str | None = None,
        metadata: dict | None = None,
    ) -> "StressLimit":
        stress_mpa = Quantity(value, unit, Dimension.STRESS).internal_value
        return cls(
            limit_id=limit_id,
            limit_type="absolute",
            allowable_stress_internal_MPa=stress_mpa,
            description=description,
            metadata=metadata,
        )

    @classmethod
    def fraction_of_Fy(
        cls,
        limit_id: str,
        Fy: float,
        factor: float,
        Fy_unit: str = "MPa",
        description: str | None = None,
        metadata: dict | None = None,
    ) -> "StressLimit":
        fy_mpa = Quantity(Fy, Fy_unit, Dimension.STRESS).internal_value
        return cls(
            limit_id=limit_id,
            limit_type="fraction_of_Fy",
            Fy_internal_MPa=fy_mpa,
            factor=factor,
            description=description,
            metadata=metadata,
        )

    def allowable_stress_MPa(self) -> float:
        if self.limit_type == "absolute":
            return float(self.allowable_stress_internal_MPa)
        return float(self.Fy_internal_MPa) * float(self.factor)


@dataclass(frozen=True)
class StressUtilizationResult:
    check_id: str
    limit_id: str
    demand_stress_MPa: float
    allowable_stress_MPa: float
    utilization_ratio: float
    passed: bool
    demand_source: str
    critical_point_id: str | None = None
    x_internal_mm: float | None = None
    offset_x_internal_mm: float | None = None
    metadata: dict | None = None


class ElasticStressCriteriaChecker:
    def _build_result(
        self,
        *,
        check_id: str,
        stress_limit: StressLimit,
        demand: float,
        demand_source: str,
        critical_point_id: str | None,
        x_internal_mm: float | None,
        offset_x_internal_mm: float | None,
        metadata: dict | None,
    ) -> StressUtilizationResult:
        allowable = stress_limit.allowable_stress_MPa()
        utilization = abs(demand) / allowable
        return StressUtilizationResult(
            check_id=check_id,
            limit_id=stress_limit.limit_id,
            demand_stress_MPa=demand,
            allowable_stress_MPa=allowable,
            utilization_ratio=utilization,
            passed=abs(demand) <= allowable,
            demand_source=demand_source,
            critical_point_id=critical_point_id,
            x_internal_mm=x_internal_mm,
            offset_x_internal_mm=offset_x_internal_mm,
            metadata=metadata,
        )

    def check_vertical_stress_result(self, vertical_stress_result, stress_limit: StressLimit, check_id: str | None = None) -> StressUtilizationResult:
        offset = None
        if getattr(vertical_stress_result, "metadata", None):
            offset = vertical_stress_result.metadata.get("max_moment_offset_x_mm")
        return self._build_result(
            check_id=check_id or f"vertical:{stress_limit.limit_id}",
            stress_limit=stress_limit,
            demand=getattr(vertical_stress_result, "max_abs_stress_MPa"),
            demand_source="vertical_bending",
            critical_point_id=None,
            x_internal_mm=getattr(vertical_stress_result, "x_internal_mm", None),
            offset_x_internal_mm=offset,
            metadata=getattr(vertical_stress_result, "metadata", None),
        )

    def check_lateral_stress_result(self, lateral_stress_result, stress_limit: StressLimit, check_id: str | None = None) -> StressUtilizationResult:
        return self._build_result(
            check_id=check_id or f"lateral:{stress_limit.limit_id}",
            stress_limit=stress_limit,
            demand=getattr(lateral_stress_result, "max_abs_lateral_stress_MPa"),
            demand_source="lateral_bending",
            critical_point_id=None,
            x_internal_mm=getattr(lateral_stress_result, "x_internal_mm", None),
            offset_x_internal_mm=None,
            metadata=getattr(lateral_stress_result, "metadata", None),
        )

    def check_biaxial_stress_result(self, biaxial_stress_result, stress_limit: StressLimit, check_id: str | None = None) -> StressUtilizationResult:
        offset = None
        if getattr(biaxial_stress_result, "metadata", None):
            offset = biaxial_stress_result.metadata.get("max_moment_offset_x_mm")
        return self._build_result(
            check_id=check_id or f"biaxial:{stress_limit.limit_id}",
            stress_limit=stress_limit,
            demand=getattr(biaxial_stress_result, "max_abs_stress_MPa"),
            demand_source="biaxial_elastic",
            critical_point_id=getattr(biaxial_stress_result, "max_abs_stress_point_id", None),
            x_internal_mm=getattr(biaxial_stress_result, "x_internal_mm", None),
            offset_x_internal_mm=offset,
            metadata=getattr(biaxial_stress_result, "metadata", None),
        )


@dataclass(frozen=True)
class StressCriteriaSet:
    criteria_id: str
    limits: list[StressLimit]
    description: str | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.criteria_id:
            raise StressCriteriaError("criteria_id is required.")
        if not self.limits:
            raise StressCriteriaError("At least one stress limit is required.")
        limit_ids = [limit.limit_id for limit in self.limits]
        if len(set(limit_ids)) != len(limit_ids):
            raise DuplicateStressLimitError("Duplicate limit_id values are not allowed in one criteria set.")

    def check_vertical_stress_result(self, vertical_stress_result) -> list[StressUtilizationResult]:
        checker = ElasticStressCriteriaChecker()
        return [checker.check_vertical_stress_result(vertical_stress_result, limit) for limit in self.limits]

    def check_lateral_stress_result(self, lateral_stress_result) -> list[StressUtilizationResult]:
        checker = ElasticStressCriteriaChecker()
        return [checker.check_lateral_stress_result(lateral_stress_result, limit) for limit in self.limits]

    def check_biaxial_stress_result(self, biaxial_stress_result) -> list[StressUtilizationResult]:
        checker = ElasticStressCriteriaChecker()
        return [checker.check_biaxial_stress_result(biaxial_stress_result, limit) for limit in self.limits]
