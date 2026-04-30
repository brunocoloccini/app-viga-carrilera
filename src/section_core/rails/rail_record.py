"""Crane rail record model for tabulated rail properties."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from section_core.units import Dimension, UnitRegistry
from section_core.units.errors import UnitCompatibilityError, UnitError

from .errors import InvalidRailRecordError


@dataclass(frozen=True)
class CraneRailRecord:
    rail_id: str
    rail_name: str
    rail_family: str
    source: str
    height_internal_mm: float
    head_width_internal_mm: float
    base_width_internal_mm: float
    area_internal_mm2: float
    weight_per_length_internal_kg_per_m: float
    Ixx_internal_mm4: float | None = None
    Iyy_internal_mm4: float | None = None
    Sxx_head_internal_mm3: float | None = None
    Sxx_base_internal_mm3: float | None = None
    Syy_internal_mm3: float | None = None
    centroid_from_base_internal_mm: float | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in ("rail_id", "rail_name", "rail_family", "source"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidRailRecordError(f"{field_name} is required.")

        for field_name in (
            "height_internal_mm",
            "head_width_internal_mm",
            "base_width_internal_mm",
            "area_internal_mm2",
            "weight_per_length_internal_kg_per_m",
        ):
            if getattr(self, field_name) <= 0:
                raise InvalidRailRecordError(f"{field_name} must be greater than zero.")

        for field_name in (
            "Ixx_internal_mm4",
            "Iyy_internal_mm4",
            "Sxx_head_internal_mm3",
            "Sxx_base_internal_mm3",
            "Syy_internal_mm3",
            "centroid_from_base_internal_mm",
        ):
            value = getattr(self, field_name)
            if value is not None and value <= 0:
                raise InvalidRailRecordError(f"{field_name} must be greater than zero when provided.")

        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        elif not isinstance(self.metadata, dict):
            raise InvalidRailRecordError("metadata must be a dict.")

    @classmethod
    def from_values(
        cls,
        rail_id,
        rail_name,
        rail_family,
        source,
        height,
        height_unit,
        head_width,
        head_width_unit,
        base_width,
        base_width_unit,
        area,
        area_unit,
        weight_per_length,
        weight_per_length_unit,
        Ixx=None,
        Ixx_unit="mm4",
        Iyy=None,
        Iyy_unit="mm4",
        Sxx_head=None,
        Sxx_head_unit="mm3",
        Sxx_base=None,
        Sxx_base_unit="mm3",
        Syy=None,
        Syy_unit="mm3",
        centroid_from_base=None,
        centroid_from_base_unit="mm",
        metadata=None,
    ) -> "CraneRailRecord":
        registry = UnitRegistry()

        def _convert(value: float | None, unit: str, dimension: str, field_name: str) -> float | None:
            if value is None:
                return None
            try:
                return registry.to_internal(float(value), unit, dimension)
            except (TypeError, ValueError, UnitError, UnitCompatibilityError) as exc:
                raise InvalidRailRecordError(f"Invalid unit for {field_name}: {exc}") from exc

        return cls(
            rail_id=rail_id,
            rail_name=rail_name,
            rail_family=rail_family,
            source=source,
            height_internal_mm=_convert(height, height_unit, Dimension.LENGTH, "height"),
            head_width_internal_mm=_convert(head_width, head_width_unit, Dimension.LENGTH, "head_width"),
            base_width_internal_mm=_convert(base_width, base_width_unit, Dimension.LENGTH, "base_width"),
            area_internal_mm2=_convert(area, area_unit, Dimension.AREA, "area"),
            weight_per_length_internal_kg_per_m=_convert(
                weight_per_length, weight_per_length_unit, Dimension.MASS_PER_LENGTH, "weight_per_length"
            ),
            Ixx_internal_mm4=_convert(Ixx, Ixx_unit, Dimension.INERTIA, "Ixx"),
            Iyy_internal_mm4=_convert(Iyy, Iyy_unit, Dimension.INERTIA, "Iyy"),
            Sxx_head_internal_mm3=_convert(Sxx_head, Sxx_head_unit, Dimension.SECTION_MODULUS, "Sxx_head"),
            Sxx_base_internal_mm3=_convert(Sxx_base, Sxx_base_unit, Dimension.SECTION_MODULUS, "Sxx_base"),
            Syy_internal_mm3=_convert(Syy, Syy_unit, Dimension.SECTION_MODULUS, "Syy"),
            centroid_from_base_internal_mm=_convert(
                centroid_from_base, centroid_from_base_unit, Dimension.LENGTH, "centroid_from_base"
            ),
            metadata=dict(metadata) if metadata is not None else {},
        )

    def is_sample(self) -> bool:
        return bool(self.metadata.get("sample_rail", False))

    def requires_verification(self) -> bool:
        return bool(self.metadata.get("requires_independent_verification_before_design_use", False))

    def to_dict(self) -> dict:
        return asdict(self)
