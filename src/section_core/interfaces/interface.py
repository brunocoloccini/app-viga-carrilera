"""Component interface models for weld/contact/shared-boundary relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import InvalidInterfaceError

SUPPORTED_INTERFACE_TYPES = {
    "weld",
    "contact",
    "shared_boundary",
    "construction_joint",
    "bolt_group",
}


@dataclass
class ComponentInterface:
    interface_id: str
    interface_type: str
    component_a_id: str
    component_b_id: str
    line_a_name: str | None = None
    line_b_name: str | None = None
    length_mm: float | None = None
    structural_action_assumed: bool = False
    verified: bool = False
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.interface_id:
            raise InvalidInterfaceError("interface_id is required.")
        if not self.component_a_id:
            raise InvalidInterfaceError("component_a_id is required.")
        if not self.component_b_id:
            raise InvalidInterfaceError("component_b_id is required.")
        if self.component_a_id == self.component_b_id:
            raise InvalidInterfaceError("component_a_id and component_b_id must be different.")
        if self.interface_type not in SUPPORTED_INTERFACE_TYPES:
            raise InvalidInterfaceError(
                f"Unsupported interface_type '{self.interface_type}'. Supported values: {sorted(SUPPORTED_INTERFACE_TYPES)}."
            )
        if self.length_mm is not None and float(self.length_mm) <= 0.0:
            raise InvalidInterfaceError("length_mm must be positive when provided.")


@dataclass
class WeldInterface(ComponentInterface):
    interface_type: str = field(init=False, default="weld")
    weld_type: str = "fillet"
    weld_size_mm: float | None = None
    continuous: bool = True
    both_sides: bool = False

    def __post_init__(self) -> None:
        self.interface_type = "weld"
        super().__post_init__()
        if self.weld_size_mm is not None and float(self.weld_size_mm) <= 0.0:
            raise InvalidInterfaceError("weld_size_mm must be positive when provided.")


@dataclass
class ContactInterface(ComponentInterface):
    interface_type: str = field(init=False, default="contact")
    contact_type: str = "bearing"
    friction_assumed: bool = False

    def __post_init__(self) -> None:
        self.interface_type = "contact"
        super().__post_init__()
