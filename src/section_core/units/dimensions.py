"""Dimension model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    """Represents a physical dimension category."""

    name: str

    LENGTH = "length"
    AREA = "area"
    INERTIA = "inertia"
    WARPING_CONSTANT = "warping_constant"
    SECTION_MODULUS = "section_modulus"
    FORCE = "force"
    MOMENT = "moment"
    STRESS = "stress"
    MASS = "mass"
    LINE_FORCE = "line_force"
    MASS_PER_LENGTH = "mass_per_length"
    DIMENSIONLESS = "dimensionless"
