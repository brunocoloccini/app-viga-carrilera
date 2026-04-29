"""Steel material model and sample material helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from section_core.units import Dimension
from section_core.units.errors import UnitCompatibilityError, UnitError
from section_core.units.quantity import Quantity

from .errors import InvalidMaterialError


@dataclass(frozen=True)
class SteelMaterial:
    material_id: str
    Fy_internal_MPa: float
    Fu_internal_MPa: float | None = None
    E_internal_MPa: float = 200000.0
    density_internal_kg_per_m3: float | None = None
    source: str | None = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not self.material_id or not self.material_id.strip():
            raise InvalidMaterialError("material_id is required.")
        if self.Fy_internal_MPa <= 0:
            raise InvalidMaterialError("Fy_internal_MPa must be greater than zero.")
        if self.Fu_internal_MPa is not None and self.Fu_internal_MPa <= 0:
            raise InvalidMaterialError("Fu_internal_MPa must be greater than zero when provided.")
        if self.E_internal_MPa <= 0:
            raise InvalidMaterialError("E_internal_MPa must be greater than zero.")
        if self.density_internal_kg_per_m3 is not None and self.density_internal_kg_per_m3 <= 0:
            raise InvalidMaterialError("density_internal_kg_per_m3 must be greater than zero when provided.")
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        else:
            object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_values(
        cls,
        material_id: str,
        Fy: float,
        Fy_unit: str = "MPa",
        Fu: float | None = None,
        Fu_unit: str = "MPa",
        E: float = 200000,
        E_unit: str = "MPa",
        density: float | None = None,
        density_unit: str | None = None,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> "SteelMaterial":
        try:
            fy_internal = Quantity(Fy, Fy_unit, Dimension.STRESS).internal_value
        except (UnitError, UnitCompatibilityError) as exc:
            raise InvalidMaterialError(f"Invalid unit for Fy: {exc}") from exc

        fu_internal = None
        if Fu is not None:
            try:
                fu_internal = Quantity(Fu, Fu_unit, Dimension.STRESS).internal_value
            except (UnitError, UnitCompatibilityError) as exc:
                raise InvalidMaterialError(f"Invalid unit for Fu: {exc}") from exc

        try:
            e_internal = Quantity(E, E_unit, Dimension.STRESS).internal_value
        except (UnitError, UnitCompatibilityError) as exc:
            raise InvalidMaterialError(f"Invalid unit for E: {exc}") from exc

        if density is not None:
            if density_unit not in (None, "kg/m3"):
                raise InvalidMaterialError("Unsupported density unit. For V1-047 only 'kg/m3' is accepted.")
            density_internal = float(density)
        else:
            density_internal = None

        return cls(
            material_id=material_id,
            Fy_internal_MPa=float(fy_internal),
            Fu_internal_MPa=None if fu_internal is None else float(fu_internal),
            E_internal_MPa=float(e_internal),
            density_internal_kg_per_m3=density_internal,
            source=source,
            metadata=metadata,
        )

    def Fy_MPa(self) -> float:
        return self.Fy_internal_MPa

    def Fu_MPa(self) -> float | None:
        return self.Fu_internal_MPa

    def E_MPa(self) -> float:
        return self.E_internal_MPa

    def has_Fu(self) -> bool:
        return self.Fu_internal_MPa is not None

    def to_dict(self) -> dict:
        return asdict(self)


def build_sample_steel_materials() -> dict[str, SteelMaterial]:
    sample_metadata = {
        "sample_material": True,
        "requires_independent_verification_before_design_use": True,
        "not_official_complete_material_library": True,
    }
    return {
        "F24": SteelMaterial.from_values(
            material_id="F24",
            Fy=235,
            Fy_unit="MPa",
            Fu=370,
            Fu_unit="MPa",
            E=200000,
            E_unit="MPa",
            source="sample_data",
            metadata=sample_metadata,
        ),
        "F36": SteelMaterial.from_values(
            material_id="F36",
            Fy=355,
            Fy_unit="MPa",
            Fu=510,
            Fu_unit="MPa",
            E=200000,
            E_unit="MPa",
            source="sample_data",
            metadata=sample_metadata,
        ),
    }
