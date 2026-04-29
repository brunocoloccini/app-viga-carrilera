"""Crane runway load data models (V1-020)."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity
from section_core.units.unit_registry import UnitRegistry

from .errors import DuplicateWheelError, InvalidCraneLoadModelError, InvalidWheelLoadError


@dataclass(frozen=True)
class WheelLoad:
    wheel_id: str
    position_x_internal_mm: float
    vertical_force_internal_N: float
    lateral_force_internal_N: float = 0.0
    longitudinal_force_internal_N: float = 0.0
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.wheel_id:
            raise InvalidWheelLoadError("wheel_id is required.")
        if self.vertical_force_internal_N <= 0:
            raise InvalidWheelLoadError("vertical_force must be positive.")

    @classmethod
    def from_values(
        cls,
        wheel_id: str,
        position_x: float,
        position_x_unit: str,
        vertical_force: float,
        vertical_force_unit: str,
        lateral_force: float = 0.0,
        lateral_force_unit: str = "N",
        longitudinal_force: float = 0.0,
        longitudinal_force_unit: str = "N",
        metadata: dict | None = None,
    ) -> WheelLoad:
        try:
            pos = Quantity(position_x, position_x_unit, Dimension.LENGTH)
            vf = Quantity(vertical_force, vertical_force_unit, Dimension.FORCE)
            lf = Quantity(lateral_force, lateral_force_unit, Dimension.FORCE)
            lnf = Quantity(longitudinal_force, longitudinal_force_unit, Dimension.FORCE)
        except Exception as exc:
            raise InvalidWheelLoadError(str(exc)) from exc
        return cls(
            wheel_id=wheel_id,
            position_x_internal_mm=pos.internal_value,
            vertical_force_internal_N=vf.internal_value,
            lateral_force_internal_N=lf.internal_value,
            longitudinal_force_internal_N=lnf.internal_value,
            metadata=metadata,
        )


@dataclass(frozen=True)
class CraneWheelGroup:
    group_id: str
    wheels: list[WheelLoad]
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.group_id:
            raise InvalidWheelLoadError("group_id is required.")
        if not self.wheels:
            raise InvalidWheelLoadError("At least one wheel is required.")
        ids = [w.wheel_id for w in self.wheels]
        if len(ids) != len(set(ids)):
            raise DuplicateWheelError("Duplicate wheel_id in crane wheel group.")

    def total_vertical_force_N(self) -> float:
        return sum(w.vertical_force_internal_N for w in self.wheels)

    def total_lateral_force_N(self) -> float:
        return sum(w.lateral_force_internal_N for w in self.wheels)

    def total_longitudinal_force_N(self) -> float:
        return sum(w.longitudinal_force_internal_N for w in self.wheels)

    def wheel_positions_mm(self) -> list[float]:
        return [w.position_x_internal_mm for w in self.wheels]

    def translated(self, dx_mm: float) -> CraneWheelGroup:
        reg = UnitRegistry()
        reg.assert_compatible("mm", Dimension.LENGTH)
        shifted = [
            WheelLoad(
                wheel_id=w.wheel_id,
                position_x_internal_mm=w.position_x_internal_mm + dx_mm,
                vertical_force_internal_N=w.vertical_force_internal_N,
                lateral_force_internal_N=w.lateral_force_internal_N,
                longitudinal_force_internal_N=w.longitudinal_force_internal_N,
                metadata=w.metadata,
            )
            for w in self.wheels
        ]
        return CraneWheelGroup(group_id=self.group_id, wheels=shifted, metadata=self.metadata)

    def bounding_x(self) -> tuple[float, float]:
        xs = self.wheel_positions_mm()
        return (min(xs), max(xs))


@dataclass(frozen=True)
class CraneLoadCase:
    case_id: str
    case_type: str
    wheel_group: CraneWheelGroup
    description: str | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise InvalidCraneLoadModelError("case_id is required.")
        if not self.case_type:
            raise InvalidCraneLoadModelError("case_type is required.")
        if self.wheel_group is None:
            raise InvalidCraneLoadModelError("wheel_group is required.")


@dataclass(frozen=True)
class CraneLoadModel:
    crane_id: str
    wheel_group: CraneWheelGroup
    name: str | None = None
    vertical_impact_factor: float = 0.0
    lateral_force_factor: float | None = None
    longitudinal_force_factor: float | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.crane_id:
            raise InvalidCraneLoadModelError("crane_id is required.")
        if self.vertical_impact_factor < 0:
            raise InvalidCraneLoadModelError("vertical_impact_factor must be >= 0.")
        if self.lateral_force_factor is not None and self.lateral_force_factor < 0:
            raise InvalidCraneLoadModelError("lateral_force_factor must be >= 0.")
        if self.longitudinal_force_factor is not None and self.longitudinal_force_factor < 0:
            raise InvalidCraneLoadModelError("longitudinal_force_factor must be >= 0.")

    def nominal_wheel_group(self) -> CraneWheelGroup:
        return self.wheel_group

    def factored_vertical_wheel_group(self) -> CraneWheelGroup:
        factor = 1.0 + self.vertical_impact_factor
        wheels = [
            WheelLoad(
                wheel_id=w.wheel_id,
                position_x_internal_mm=w.position_x_internal_mm,
                vertical_force_internal_N=w.vertical_force_internal_N * factor,
                lateral_force_internal_N=w.lateral_force_internal_N,
                longitudinal_force_internal_N=w.longitudinal_force_internal_N,
                metadata=w.metadata,
            )
            for w in self.wheel_group.wheels
        ]
        return CraneWheelGroup(group_id=f"{self.wheel_group.group_id}_vertical_impact", wheels=wheels)

    def generated_lateral_wheel_group(self) -> CraneWheelGroup:
        factor = self.lateral_force_factor or 0.0
        wheels = [
            WheelLoad(
                wheel_id=w.wheel_id,
                position_x_internal_mm=w.position_x_internal_mm,
                vertical_force_internal_N=w.vertical_force_internal_N,
                lateral_force_internal_N=factor * w.vertical_force_internal_N,
                longitudinal_force_internal_N=w.longitudinal_force_internal_N,
                metadata=w.metadata,
            )
            for w in self.wheel_group.wheels
        ]
        return CraneWheelGroup(group_id=f"{self.wheel_group.group_id}_lateral", wheels=wheels)

    def generated_longitudinal_wheel_group(self) -> CraneWheelGroup:
        factor = self.longitudinal_force_factor or 0.0
        total = self.wheel_group.total_vertical_force_N()
        per_wheel = factor * total / len(self.wheel_group.wheels)
        wheels = [
            WheelLoad(
                wheel_id=w.wheel_id,
                position_x_internal_mm=w.position_x_internal_mm,
                vertical_force_internal_N=w.vertical_force_internal_N,
                lateral_force_internal_N=w.lateral_force_internal_N,
                longitudinal_force_internal_N=per_wheel,
                metadata=w.metadata,
            )
            for w in self.wheel_group.wheels
        ]
        return CraneWheelGroup(group_id=f"{self.wheel_group.group_id}_longitudinal", wheels=wheels)

    def load_cases(self) -> list[CraneLoadCase]:
        return [
            CraneLoadCase("vertical_nominal", "vertical_nominal", self.nominal_wheel_group()),
            CraneLoadCase("vertical_with_impact", "vertical_with_impact", self.factored_vertical_wheel_group()),
            CraneLoadCase("lateral", "lateral", self.generated_lateral_wheel_group()),
            CraneLoadCase("longitudinal", "longitudinal", self.generated_longitudinal_wheel_group()),
        ]
