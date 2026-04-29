"""Rail/load eccentricity torsional input model (V1-031)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity
from section_core.units.unit_registry import UnitRegistry

from .loads import CraneWheelGroup, WheelLoad


class RailEccentricityError(ValueError):
    """Base error for rail eccentricity torsional input modeling."""


class InvalidRailEccentricityError(RailEccentricityError):
    """Invalid rail eccentricity model data or units."""


class InvalidTorsionalLoadError(RailEccentricityError):
    """Invalid torsional wheel load data."""


class DuplicateTorsionalWheelError(RailEccentricityError):
    """Duplicate wheel identifiers inside one torsional load group."""


@dataclass(frozen=True)
class WheelTorsionalLoad:
    wheel_id: str
    position_x_internal_mm: float
    torsional_moment_internal_Nmm: float
    source_vertical_force_internal_N: float | None = None
    vertical_eccentricity_y_internal_mm: float | None = None
    source_lateral_force_internal_N: float | None = None
    lateral_load_height_z_internal_mm: float | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.wheel_id:
            raise InvalidTorsionalLoadError("wheel_id is required.")
        if not math.isfinite(self.position_x_internal_mm):
            raise InvalidTorsionalLoadError("position_x_internal_mm must be finite.")
        if not math.isfinite(self.torsional_moment_internal_Nmm):
            raise InvalidTorsionalLoadError("torsional_moment_internal_Nmm must be finite.")
        optional_numeric_fields = {
            "source_vertical_force_internal_N": self.source_vertical_force_internal_N,
            "vertical_eccentricity_y_internal_mm": self.vertical_eccentricity_y_internal_mm,
            "source_lateral_force_internal_N": self.source_lateral_force_internal_N,
            "lateral_load_height_z_internal_mm": self.lateral_load_height_z_internal_mm,
        }
        for field_name, value in optional_numeric_fields.items():
            if value is not None and not math.isfinite(value):
                raise InvalidTorsionalLoadError(f"{field_name} must be finite when provided.")


@dataclass(frozen=True)
class WheelTorsionalLoadGroup:
    group_id: str
    torsional_loads: list[WheelTorsionalLoad]
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.group_id:
            raise InvalidTorsionalLoadError("group_id is required.")
        if not self.torsional_loads:
            raise InvalidTorsionalLoadError("At least one torsional load is required.")
        ids = [w.wheel_id for w in self.torsional_loads]
        if len(ids) != len(set(ids)):
            raise DuplicateTorsionalWheelError("Duplicate wheel_id in torsional wheel group.")

    def total_torsional_moment_Nmm(self) -> float:
        return sum(w.torsional_moment_internal_Nmm for w in self.torsional_loads)

    def torsional_positions_mm(self) -> list[float]:
        return [w.position_x_internal_mm for w in self.torsional_loads]

    def translated(self, dx_mm: float) -> WheelTorsionalLoadGroup:
        reg = UnitRegistry()
        reg.assert_compatible("mm", Dimension.LENGTH)
        if not math.isfinite(dx_mm):
            raise InvalidTorsionalLoadError("dx_mm must be finite.")
        shifted = [
            WheelTorsionalLoad(
                wheel_id=w.wheel_id,
                position_x_internal_mm=w.position_x_internal_mm + dx_mm,
                torsional_moment_internal_Nmm=w.torsional_moment_internal_Nmm,
                source_vertical_force_internal_N=w.source_vertical_force_internal_N,
                vertical_eccentricity_y_internal_mm=w.vertical_eccentricity_y_internal_mm,
                source_lateral_force_internal_N=w.source_lateral_force_internal_N,
                lateral_load_height_z_internal_mm=w.lateral_load_height_z_internal_mm,
                metadata=w.metadata,
            )
            for w in self.torsional_loads
        ]
        return WheelTorsionalLoadGroup(group_id=self.group_id, torsional_loads=shifted, metadata=self.metadata)

    def bounding_x(self) -> tuple[float, float]:
        xs = self.torsional_positions_mm()
        return (min(xs), max(xs))


@dataclass(frozen=True)
class RailEccentricityModel:
    model_id: str
    vertical_eccentricity_y_internal_mm: float
    lateral_load_height_z_internal_mm: float = 0.0
    include_vertical: bool = True
    include_lateral: bool = False
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise InvalidRailEccentricityError("model_id is required.")
        if not math.isfinite(self.vertical_eccentricity_y_internal_mm):
            raise InvalidRailEccentricityError("vertical_eccentricity_y_internal_mm must be finite.")
        if not math.isfinite(self.lateral_load_height_z_internal_mm):
            raise InvalidRailEccentricityError("lateral_load_height_z_internal_mm must be finite.")
        if not (self.include_vertical or self.include_lateral):
            raise InvalidRailEccentricityError("At least one of include_vertical or include_lateral must be True.")

    @classmethod
    def from_values(
        cls,
        model_id: str,
        vertical_eccentricity_y: float,
        vertical_eccentricity_y_unit: str = "mm",
        lateral_load_height_z: float = 0,
        lateral_load_height_z_unit: str = "mm",
        include_vertical: bool = True,
        include_lateral: bool = False,
        metadata: dict | None = None,
    ) -> RailEccentricityModel:
        try:
            ey = Quantity(vertical_eccentricity_y, vertical_eccentricity_y_unit, Dimension.LENGTH)
            hz = Quantity(lateral_load_height_z, lateral_load_height_z_unit, Dimension.LENGTH)
        except Exception as exc:
            raise InvalidRailEccentricityError(str(exc)) from exc
        return cls(
            model_id=model_id,
            vertical_eccentricity_y_internal_mm=ey.internal_value,
            lateral_load_height_z_internal_mm=hz.internal_value,
            include_vertical=include_vertical,
            include_lateral=include_lateral,
            metadata=metadata,
        )

    def torsional_load_from_wheel(self, wheel: WheelLoad) -> WheelTorsionalLoad:
        t = 0.0
        source_vertical = None
        source_lateral = None
        ey = None
        hz = None
        if self.include_vertical:
            source_vertical = wheel.vertical_force_internal_N
            ey = self.vertical_eccentricity_y_internal_mm
            t += source_vertical * ey
        if self.include_lateral:
            source_lateral = wheel.lateral_force_internal_N
            hz = self.lateral_load_height_z_internal_mm
            t += source_lateral * hz
        return WheelTorsionalLoad(
            wheel_id=wheel.wheel_id,
            position_x_internal_mm=wheel.position_x_internal_mm,
            torsional_moment_internal_Nmm=t,
            source_vertical_force_internal_N=source_vertical,
            vertical_eccentricity_y_internal_mm=ey,
            source_lateral_force_internal_N=source_lateral,
            lateral_load_height_z_internal_mm=hz,
            metadata={"model_id": self.model_id},
        )

    def torsional_group_from_wheel_group(
        self,
        wheel_group: CraneWheelGroup,
        group_id: str | None = None,
    ) -> WheelTorsionalLoadGroup:
        loads = [self.torsional_load_from_wheel(w) for w in wheel_group.wheels]
        return WheelTorsionalLoadGroup(
            group_id=group_id or f"{wheel_group.group_id}_torsional",
            torsional_loads=loads,
            metadata={"source_wheel_group_id": wheel_group.group_id, "model_id": self.model_id},
        )
