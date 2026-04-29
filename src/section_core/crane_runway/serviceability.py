"""Generic serviceability criteria/checking for crane runway deflection results (V1-026)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity


class ServiceabilityError(ValueError):
    """Base error for serviceability criteria/checking."""


class InvalidDeflectionLimitError(ServiceabilityError):
    """Invalid deflection limit definition."""


class DuplicateServiceabilityLimitError(ServiceabilityError):
    """Duplicate serviceability limit identifiers in one criteria set."""


@dataclass(frozen=True)
class DeflectionLimit:
    limit_id: str
    limit_type: str
    description: str | None = None
    span_divisor: float | None = None
    absolute_limit_internal_mm: float | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.limit_id:
            raise InvalidDeflectionLimitError("limit_id is required.")

        supported = {"span_divisor", "absolute", "minimum_of_span_divisor_and_absolute"}
        if self.limit_type not in supported:
            raise InvalidDeflectionLimitError(f"Unsupported limit_type: {self.limit_type}")

        if self.limit_type == "span_divisor":
            if self.span_divisor is None or self.span_divisor <= 0:
                raise InvalidDeflectionLimitError("span_divisor must be > 0 for span_divisor limits.")
        elif self.limit_type == "absolute":
            if self.absolute_limit_internal_mm is None or self.absolute_limit_internal_mm <= 0:
                raise InvalidDeflectionLimitError("absolute_limit_internal_mm must be > 0 for absolute limits.")
        elif self.limit_type == "minimum_of_span_divisor_and_absolute":
            if self.span_divisor is None or self.span_divisor <= 0:
                raise InvalidDeflectionLimitError("span_divisor must be > 0 for minimum combined limits.")
            if self.absolute_limit_internal_mm is None or self.absolute_limit_internal_mm <= 0:
                raise InvalidDeflectionLimitError("absolute_limit_internal_mm must be > 0 for minimum combined limits.")

    @classmethod
    def span_over(cls, limit_id: str, divisor: float, description: str | None = None, metadata: dict | None = None) -> "DeflectionLimit":
        return cls(
            limit_id=limit_id,
            limit_type="span_divisor",
            span_divisor=divisor,
            description=description,
            metadata=metadata,
        )

    @classmethod
    def absolute(
        cls,
        limit_id: str,
        value: float,
        unit: str = "mm",
        description: str | None = None,
        metadata: dict | None = None,
    ) -> "DeflectionLimit":
        absolute_mm = Quantity(value, unit, Dimension.LENGTH).internal_value
        return cls(
            limit_id=limit_id,
            limit_type="absolute",
            absolute_limit_internal_mm=absolute_mm,
            description=description,
            metadata=metadata,
        )

    @classmethod
    def minimum_of_span_over_and_absolute(
        cls,
        limit_id: str,
        divisor: float,
        value: float,
        unit: str = "mm",
        description: str | None = None,
        metadata: dict | None = None,
    ) -> "DeflectionLimit":
        absolute_mm = Quantity(value, unit, Dimension.LENGTH).internal_value
        return cls(
            limit_id=limit_id,
            limit_type="minimum_of_span_divisor_and_absolute",
            span_divisor=divisor,
            absolute_limit_internal_mm=absolute_mm,
            description=description,
            metadata=metadata,
        )

    def allowable_deflection_mm(self, span_internal_mm: float) -> float:
        if span_internal_mm <= 0:
            raise InvalidDeflectionLimitError("span_internal_mm must be > 0.")

        if self.limit_type == "span_divisor":
            return span_internal_mm / float(self.span_divisor)
        if self.limit_type == "absolute":
            return float(self.absolute_limit_internal_mm)
        span_based = span_internal_mm / float(self.span_divisor)
        absolute = float(self.absolute_limit_internal_mm)
        return min(span_based, absolute)


@dataclass(frozen=True)
class ServiceabilityCheckResult:
    check_id: str
    limit_id: str
    demand_deflection_mm: float
    allowable_deflection_mm: float
    utilization_ratio: float
    passed: bool
    demand_x_mm: float | None = None
    demand_offset_x_mm: float | None = None
    metadata: dict | None = None


class DeflectionServiceabilityChecker:
    def check_moving_deflection_envelope(self, envelope_result, deflection_limit: DeflectionLimit, check_id: str | None = None) -> ServiceabilityCheckResult:
        demand = envelope_result.max_deflection_mm
        allowable = deflection_limit.allowable_deflection_mm(envelope_result.span_internal_mm)
        return ServiceabilityCheckResult(
            check_id=check_id or f"moving:{deflection_limit.limit_id}",
            limit_id=deflection_limit.limit_id,
            demand_deflection_mm=demand,
            allowable_deflection_mm=allowable,
            utilization_ratio=demand / allowable,
            passed=demand <= allowable,
            demand_x_mm=envelope_result.max_deflection_x_mm,
            demand_offset_x_mm=envelope_result.max_deflection_offset_x_mm,
        )

    def check_fixed_deflection_result(self, deflection_result, deflection_limit: DeflectionLimit, check_id: str | None = None) -> ServiceabilityCheckResult:
        demand = deflection_result.max_deflection_mm
        allowable = deflection_limit.allowable_deflection_mm(deflection_result.span_internal_mm)
        return ServiceabilityCheckResult(
            check_id=check_id or f"fixed:{deflection_limit.limit_id}",
            limit_id=deflection_limit.limit_id,
            demand_deflection_mm=demand,
            allowable_deflection_mm=allowable,
            utilization_ratio=demand / allowable,
            passed=demand <= allowable,
            demand_x_mm=deflection_result.max_deflection_x_mm,
            demand_offset_x_mm=None,
        )


@dataclass(frozen=True)
class DeflectionCriteriaSet:
    criteria_id: str
    limits: list[DeflectionLimit]
    description: str | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.criteria_id:
            raise ServiceabilityError("criteria_id is required.")
        if not self.limits:
            raise ServiceabilityError("At least one deflection limit is required.")
        limit_ids = [limit.limit_id for limit in self.limits]
        if len(set(limit_ids)) != len(limit_ids):
            raise DuplicateServiceabilityLimitError("Duplicate limit_id values are not allowed in one criteria set.")

    def check_moving_deflection_envelope(self, envelope_result) -> list[ServiceabilityCheckResult]:
        checker = DeflectionServiceabilityChecker()
        return [checker.check_moving_deflection_envelope(envelope_result, limit) for limit in self.limits]

    def check_fixed_deflection_result(self, deflection_result) -> list[ServiceabilityCheckResult]:
        checker = DeflectionServiceabilityChecker()
        return [checker.check_fixed_deflection_result(deflection_result, limit) for limit in self.limits]
