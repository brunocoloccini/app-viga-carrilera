"""Quantity model."""

from dataclasses import dataclass

from .unit_registry import UnitRegistry


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    dimension: str
    original_text: str | None = None
    internal_value: float | None = None
    internal_unit: str | None = None

    def __post_init__(self) -> None:
        registry = UnitRegistry()
        ivalue = registry.to_internal(float(self.value), self.unit, self.dimension)
        iunit = registry.internal_unit_for(self.dimension)
        object.__setattr__(self, "internal_value", ivalue)
        object.__setattr__(self, "internal_unit", iunit)
        if self.original_text is None:
            object.__setattr__(self, "original_text", f"{self.value} {self.unit}")
