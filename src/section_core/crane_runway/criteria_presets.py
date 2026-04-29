"""Generic criteria preset infrastructure for crane runway checks (V1-046)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .serviceability import DeflectionLimit
from .stress_criteria import StressLimit


class CriteriaPresetError(ValueError):
    """Base error for generic criteria presets."""


class InvalidCriteriaPresetError(CriteriaPresetError):
    """Invalid criteria preset definition."""


class DuplicateCriteriaPresetError(CriteriaPresetError):
    """Duplicate criteria preset identifier in one registry category."""


class CriteriaPresetNotFoundError(CriteriaPresetError):
    """Requested criteria preset was not found in the registry."""


@dataclass(frozen=True)
class GenericCriteriaPreset:
    preset_id: str
    preset_type: str
    description: str | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.preset_id:
            raise InvalidCriteriaPresetError("preset_id is required.")
        if self.preset_type not in {"deflection", "stress"}:
            raise InvalidCriteriaPresetError(f"Unsupported preset_type: {self.preset_type}")


@dataclass(frozen=True)
class DeflectionLimitPreset(GenericCriteriaPreset):
    limit_type: str = "span_divisor"
    span_divisor: float | None = None
    absolute_limit_internal_mm: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.preset_type != "deflection":
            raise InvalidCriteriaPresetError("DeflectionLimitPreset requires preset_type='deflection'.")
        if self.limit_type not in {"span_divisor", "absolute", "minimum_of_span_divisor_and_absolute"}:
            raise InvalidCriteriaPresetError(f"Unsupported deflection limit_type: {self.limit_type}")
        if self.limit_type in {"span_divisor", "minimum_of_span_divisor_and_absolute"}:
            if self.span_divisor is None or self.span_divisor <= 0:
                raise InvalidCriteriaPresetError("span_divisor must be > 0 for this deflection preset.")
        if self.limit_type in {"absolute", "minimum_of_span_divisor_and_absolute"}:
            if self.absolute_limit_internal_mm is None or self.absolute_limit_internal_mm <= 0:
                raise InvalidCriteriaPresetError("absolute_limit_internal_mm must be > 0 for this deflection preset.")

    def to_deflection_limit(self, limit_id: str | None = None) -> DeflectionLimit:
        return DeflectionLimit(
            limit_id=limit_id or self.preset_id,
            limit_type=self.limit_type,
            span_divisor=self.span_divisor,
            absolute_limit_internal_mm=self.absolute_limit_internal_mm,
            description=self.description,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class StressLimitPreset(GenericCriteriaPreset):
    limit_type: str = "absolute"
    allowable_stress_internal_MPa: float | None = None
    Fy_internal_MPa: float | None = None
    factor: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.preset_type != "stress":
            raise InvalidCriteriaPresetError("StressLimitPreset requires preset_type='stress'.")
        if self.limit_type not in {"absolute", "fraction_of_Fy"}:
            raise InvalidCriteriaPresetError(f"Unsupported stress limit_type: {self.limit_type}")
        if self.limit_type == "absolute":
            if self.allowable_stress_internal_MPa is None or self.allowable_stress_internal_MPa <= 0:
                raise InvalidCriteriaPresetError("allowable_stress_internal_MPa must be > 0 for absolute presets.")
        if self.limit_type == "fraction_of_Fy":
            if self.factor is None or self.factor <= 0:
                raise InvalidCriteriaPresetError("factor must be > 0 for fraction_of_Fy presets.")
            if self.Fy_internal_MPa is not None and self.Fy_internal_MPa <= 0:
                raise InvalidCriteriaPresetError("Fy_internal_MPa must be > 0 when provided.")

    def to_stress_limit(self, limit_id: str | None = None, Fy: float | None = None, Fy_unit: str = "MPa") -> StressLimit:
        if self.limit_type == "absolute":
            return StressLimit(
                limit_id=limit_id or self.preset_id,
                limit_type="absolute",
                allowable_stress_internal_MPa=self.allowable_stress_internal_MPa,
                description=self.description,
                metadata=self.metadata,
            )

        fy = Fy if Fy is not None else self.Fy_internal_MPa
        if fy is None:
            raise InvalidCriteriaPresetError(
                f"Preset '{self.preset_id}' requires Fy for conversion because Fy_internal_MPa is not stored."
            )
        return StressLimit.fraction_of_Fy(
            limit_id=limit_id or self.preset_id,
            Fy=fy,
            factor=float(self.factor),
            Fy_unit=Fy_unit,
            description=self.description,
            metadata=self.metadata,
        )


@dataclass
class CriteriaPresetRegistry:
    deflection_presets: dict[str, DeflectionLimitPreset] = field(default_factory=dict)
    stress_presets: dict[str, StressLimitPreset] = field(default_factory=dict)
    metadata: dict | None = None

    def add_deflection_preset(self, preset: DeflectionLimitPreset) -> None:
        if preset.preset_id in self.deflection_presets:
            raise DuplicateCriteriaPresetError(f"Duplicate deflection preset_id: {preset.preset_id}")
        self.deflection_presets[preset.preset_id] = preset

    def add_stress_preset(self, preset: StressLimitPreset) -> None:
        if preset.preset_id in self.stress_presets:
            raise DuplicateCriteriaPresetError(f"Duplicate stress preset_id: {preset.preset_id}")
        self.stress_presets[preset.preset_id] = preset

    def get_deflection_preset(self, preset_id: str) -> DeflectionLimitPreset:
        if preset_id not in self.deflection_presets:
            raise CriteriaPresetNotFoundError(f"Deflection preset not found: {preset_id}")
        return self.deflection_presets[preset_id]

    def get_stress_preset(self, preset_id: str) -> StressLimitPreset:
        if preset_id not in self.stress_presets:
            raise CriteriaPresetNotFoundError(f"Stress preset not found: {preset_id}")
        return self.stress_presets[preset_id]

    def list_deflection_preset_ids(self) -> list[str]:
        return sorted(self.deflection_presets)

    def list_stress_preset_ids(self) -> list[str]:
        return sorted(self.stress_presets)

    def has_deflection_preset(self, preset_id: str) -> bool:
        return preset_id in self.deflection_presets

    def has_stress_preset(self, preset_id: str) -> bool:
        return preset_id in self.stress_presets

    def to_deflection_limit(self, preset_id: str, limit_id: str | None = None) -> DeflectionLimit:
        return self.get_deflection_preset(preset_id).to_deflection_limit(limit_id=limit_id)

    def to_stress_limit(self, preset_id: str, limit_id: str | None = None, Fy: float | None = None, Fy_unit: str = "MPa") -> StressLimit:
        return self.get_stress_preset(preset_id).to_stress_limit(limit_id=limit_id, Fy=Fy, Fy_unit=Fy_unit)


def build_generic_criteria_preset_registry() -> CriteriaPresetRegistry:
    registry = CriteriaPresetRegistry(
        metadata={"preset_scope": "generic", "note": "No design-code compliance is implied."}
    )
    registry.add_deflection_preset(
        DeflectionLimitPreset(
            preset_id="deflection_L_over_600",
            preset_type="deflection",
            limit_type="span_divisor",
            span_divisor=600,
            description="Generic vertical deflection limit L/600.",
        )
    )
    registry.add_deflection_preset(
        DeflectionLimitPreset(
            preset_id="deflection_L_over_750",
            preset_type="deflection",
            limit_type="span_divisor",
            span_divisor=750,
            description="Generic vertical deflection limit L/750.",
        )
    )
    registry.add_stress_preset(
        StressLimitPreset(
            preset_id="stress_0_66Fy",
            preset_type="stress",
            limit_type="fraction_of_Fy",
            factor=0.66,
            description="Generic elastic stress limit 0.66Fy.",
        )
    )
    registry.add_stress_preset(
        StressLimitPreset(
            preset_id="stress_0_90Fy",
            preset_type="stress",
            limit_type="fraction_of_Fy",
            factor=0.90,
            description="Generic elastic stress limit 0.90Fy.",
        )
    )
    return registry
