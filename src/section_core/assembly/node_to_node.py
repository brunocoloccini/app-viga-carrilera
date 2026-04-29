"""Node-to-node geometric assembly operation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from section_core.components import SectionElement
from section_core.section import Section
from section_core.section.errors import DuplicateComponentError, UnsupportedComponentTypeError

from .errors import AssemblyGeometryError, AssemblyReferenceError
from .operation import AssemblyOperation


@dataclass(frozen=True)
class NodeToNodeJoin(AssemblyOperation):
    source_component: SectionElement | object = None
    source_node_name: str = ""
    target_component_id: str = ""
    target_node_name: str = ""
    create_connection: bool = False
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_type", "node_to_node_join")

    def apply(self, section: Section) -> Section:
        if not isinstance(self.source_component, SectionElement):
            raise AssemblyGeometryError("Invalid source component type; expected SectionElement.")

        try:
            source_node = self.source_component.get_node(self.source_node_name)
        except Exception as exc:  # noqa: BLE001
            raise AssemblyReferenceError(
                f"Missing source node '{self.source_node_name}' in component '{self.source_component.element_id}'."
            ) from exc

        if not section.has_component(self.target_component_id):
            raise AssemblyReferenceError(
                f"Missing target component '{self.target_component_id}' in section '{section.section_id}'."
            )

        target_component = section.get_component(self.target_component_id)
        try:
            target_node = target_component.get_node(self.target_node_name)
        except Exception as exc:  # noqa: BLE001
            raise AssemblyReferenceError(
                f"Missing target node '{self.target_node_name}' in component '{self.target_component_id}'."
            ) from exc

        dy_mm = target_node.y_internal_mm - source_node.y_internal_mm
        dz_mm = target_node.z_internal_mm - source_node.z_internal_mm

        translated = self.source_component.translated(dy_mm, dz_mm)
        trace = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "source_component_id": self.source_component.element_id,
            "source_node_name": self.source_node_name,
            "target_component_id": self.target_component_id,
            "target_node_name": self.target_node_name,
            "translation_dy_mm": dy_mm,
            "translation_dz_mm": dz_mm,
            "create_connection": self.create_connection,
        }
        merged_metadata = dict(translated.metadata) if translated.metadata is not None else {}
        merged_metadata["assembly"] = trace
        translated = translated.__class__(**{**translated.__dict__, "metadata": merged_metadata})

        new_section = Section(
            section_id=section.section_id,
            name=section.name,
            components=list(section.components),
            metadata=dict(section.metadata) if section.metadata is not None else None,
        )
        try:
            new_section.add_component(translated)
        except DuplicateComponentError as exc:
            raise AssemblyReferenceError(
                f"Duplicate component id '{translated.element_id}' when adding translated component."
            ) from exc
        except UnsupportedComponentTypeError as exc:
            raise AssemblyGeometryError(str(exc)) from exc

        return new_section
