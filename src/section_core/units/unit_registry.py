"""Unit registry and conversions."""

from __future__ import annotations

from dataclasses import dataclass

from .dimensions import Dimension
from .errors import UnitError, UnitCompatibilityError


@dataclass(frozen=True)
class UnitDef:
    dimension: str
    to_internal: float


class UnitRegistry:
    """Registry for unit compatibility and conversion factors."""

    INTERNAL_UNITS = {
        Dimension.LENGTH: "mm",
        Dimension.AREA: "mm2",
        Dimension.INERTIA: "mm4",
        Dimension.WARPING_CONSTANT: "mm6",
        Dimension.SECTION_MODULUS: "mm3",
        Dimension.FORCE: "N",
        Dimension.MOMENT: "Nmm",
        Dimension.STRESS: "MPa",
        Dimension.MASS: "kg",
        Dimension.LINE_FORCE: "N/mm",
        Dimension.MASS_PER_LENGTH: "kg/m",
        Dimension.DIMENSIONLESS: "-",
    }

    def __init__(self) -> None:
        in_to_mm = 25.4
        ft_to_mm = 304.8
        yd_to_mm = 914.4
        lbf_to_n = 4.4482216152605
        kip_to_n = 4448.2216152605
        kgf_to_n = 9.80665
        tf_to_n = 9806.65

        self.units: dict[str, UnitDef] = {
            "-": UnitDef(Dimension.DIMENSIONLESS, 1.0),
            # length
            "mm": UnitDef(Dimension.LENGTH, 1.0),
            "cm": UnitDef(Dimension.LENGTH, 10.0),
            "m": UnitDef(Dimension.LENGTH, 1000.0),
            "in": UnitDef(Dimension.LENGTH, in_to_mm),
            "ft": UnitDef(Dimension.LENGTH, ft_to_mm),
            "yd": UnitDef(Dimension.LENGTH, yd_to_mm),
            # area
            "mm2": UnitDef(Dimension.AREA, 1.0),
            "cm2": UnitDef(Dimension.AREA, 100.0),
            "m2": UnitDef(Dimension.AREA, 1_000_000.0),
            "in2": UnitDef(Dimension.AREA, in_to_mm**2),
            "ft2": UnitDef(Dimension.AREA, ft_to_mm**2),
            # inertia
            "mm4": UnitDef(Dimension.INERTIA, 1.0),
            "cm4": UnitDef(Dimension.INERTIA, 10_000.0),
            "m4": UnitDef(Dimension.INERTIA, 1_000_000_000_000.0),
            "in4": UnitDef(Dimension.INERTIA, in_to_mm**4),
            "ft4": UnitDef(Dimension.INERTIA, ft_to_mm**4),
            # warping constant
            "mm6": UnitDef(Dimension.WARPING_CONSTANT, 1.0),
            "cm6": UnitDef(Dimension.WARPING_CONSTANT, 1_000_000.0),
            "m6": UnitDef(Dimension.WARPING_CONSTANT, 1_000_000_000_000_000_000.0),
            "in6": UnitDef(Dimension.WARPING_CONSTANT, in_to_mm**6),
            "ft6": UnitDef(Dimension.WARPING_CONSTANT, ft_to_mm**6),
            # section modulus
            "mm3": UnitDef(Dimension.SECTION_MODULUS, 1.0),
            "cm3": UnitDef(Dimension.SECTION_MODULUS, 1000.0),
            "m3": UnitDef(Dimension.SECTION_MODULUS, 1_000_000_000.0),
            "in3": UnitDef(Dimension.SECTION_MODULUS, in_to_mm**3),
            "ft3": UnitDef(Dimension.SECTION_MODULUS, ft_to_mm**3),
            # force
            "N": UnitDef(Dimension.FORCE, 1.0),
            "kN": UnitDef(Dimension.FORCE, 1000.0),
            "MN": UnitDef(Dimension.FORCE, 1_000_000.0),
            "kgf": UnitDef(Dimension.FORCE, kgf_to_n),
            "tf": UnitDef(Dimension.FORCE, tf_to_n),
            "lbf": UnitDef(Dimension.FORCE, lbf_to_n),
            "kip": UnitDef(Dimension.FORCE, kip_to_n),
            # moment
            "Nmm": UnitDef(Dimension.MOMENT, 1.0),
            "Nm": UnitDef(Dimension.MOMENT, 1000.0),
            "kNm": UnitDef(Dimension.MOMENT, 1_000_000.0),
            "kgfm": UnitDef(Dimension.MOMENT, kgf_to_n * 1000.0),
            "tfm": UnitDef(Dimension.MOMENT, tf_to_n * 1000.0),
            "lbfin": UnitDef(Dimension.MOMENT, lbf_to_n * in_to_mm),
            "lbfft": UnitDef(Dimension.MOMENT, lbf_to_n * ft_to_mm),
            "kipin": UnitDef(Dimension.MOMENT, kip_to_n * in_to_mm),
            "kipft": UnitDef(Dimension.MOMENT, kip_to_n * ft_to_mm),
            # stress (internal MPa)
            "Pa": UnitDef(Dimension.STRESS, 1e-6),
            "kPa": UnitDef(Dimension.STRESS, 1e-3),
            "MPa": UnitDef(Dimension.STRESS, 1.0),
            "GPa": UnitDef(Dimension.STRESS, 1000.0),
            "psi": UnitDef(Dimension.STRESS, 0.006894757293168361),
            "ksi": UnitDef(Dimension.STRESS, 6.894757293168361),
            "kgf_cm2": UnitDef(Dimension.STRESS, kgf_to_n / 100.0),
            # mass
            "g": UnitDef(Dimension.MASS, 0.001),
            "kg": UnitDef(Dimension.MASS, 1.0),
            "tonne": UnitDef(Dimension.MASS, 1000.0),
            "lbm": UnitDef(Dimension.MASS, 0.45359237),
            # line force
            "N/mm": UnitDef(Dimension.LINE_FORCE, 1.0),
            "N/m": UnitDef(Dimension.LINE_FORCE, 0.001),
            "kN/m": UnitDef(Dimension.LINE_FORCE, 1.0),
            "lbf/ft": UnitDef(Dimension.LINE_FORCE, lbf_to_n / ft_to_mm),
            "kip/ft": UnitDef(Dimension.LINE_FORCE, kip_to_n / ft_to_mm),
            "lb/yd": UnitDef(Dimension.LINE_FORCE, lbf_to_n / yd_to_mm),
            # mass per length
            "kg/m": UnitDef(Dimension.MASS_PER_LENGTH, 1.0),
            "lbm/ft": UnitDef(Dimension.MASS_PER_LENGTH, 0.45359237 / 0.3048),
            "lbm/yd": UnitDef(Dimension.MASS_PER_LENGTH, 0.45359237 / 0.9144),
        }

    def assert_compatible(self, unit: str, expected_dimension: str) -> None:
        unit_def = self.units.get(unit)
        if unit_def is None:
            raise UnitError(f"Unknown unit: {unit}")
        if unit == "lb/yd" and expected_dimension != Dimension.LINE_FORCE:
            raise UnitCompatibilityError("Unit 'lb/yd' is only valid for line_force.")
        if unit_def.dimension != expected_dimension:
            raise UnitCompatibilityError(
                f"Unit '{unit}' belongs to '{unit_def.dimension}', expected '{expected_dimension}'."
            )

    def to_internal(self, value: float, unit: str, expected_dimension: str) -> float:
        self.assert_compatible(unit, expected_dimension)
        return value * self.units[unit].to_internal

    def internal_unit_for(self, dimension: str) -> str:
        return self.INTERNAL_UNITS[dimension]
