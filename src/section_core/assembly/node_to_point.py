"""Node-to-point geometric assembly operation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from section_core.components import SectionElement
from section_core.geometry import Node, Point2D, SectionPoint
from section_core.section import Section
from section_core.section.errors import DuplicateComponentError, UnsupportedComponentTypeError
from section_core.units import Dimension, UnitRegistry
from section_core.units.errors import UnitCompatibilityError, UnitError

from .errors import AssemblyGeometryError, AssemblyReferenceError
from .operation import AssemblyOperation


@dataclass(frozen=True)
class NodeToPointJoin(AssemblyOperation):
    source_component: SectionElement | object = None
    source_node_name: str = ""
    target_point: SectionPoint | Point2D | Node | object = None
    create_connection: bool = False
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_type", "node_to_point_join")

    @classmethod
    def to_coordinates(
        cls,
        *,
        operation_id: str,
        source_component: SectionElement,
        source_node_name: str,
        y: float,
        y_unit: str,
        z: float,
        z_unit: str,
        create_connection: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "NodeToPointJoin":
        registry = UnitRegistry()
        try:
            registry.assert_compatible(y_unit, Dimension.LENGTH)
            registry.assert_compatible(z_unit, Dimension.LENGTH)
            y_mm = registry.to_internal(float(y), y_unit, Dimension.LENGTH)
            z_mm = registry.to_internal(float(z), z_unit, Dimension.LENGTH)
        except (UnitCompatibilityError, UnitError) as exc:
            raise AssemblyGeometryError(f"Invalid coordinate units: {exc}") from exc

        return cls(
            operation_id=operation_id,
            operation_type="ignored",
            source_component=source_component,
            source_node_name=source_node_name,
            target_point=Point2D(y_internal_mm=y_mm, z_internal_mm=z_mm),
            create_connection=create_connection,
            metadata=metadata,
        )

    def _resolve_target_point(self) -> tuple[float, float, str | None]:
        if isinstance(self.target_point, SectionPoint):
            return (
                self.target_point.y_internal_mm,
                self.target_point.z_internal_mm,
                self.target_point.point_id,
            )
        if isinstance(self.target_point, (Point2D, Node)):
            return (
                self.target_point.y_internal_mm,
                self.target_point.z_internal_mm,
                getattr(self.target_point, "node_id", None),
            )
        raise AssemblyGeometryError(
            "Invalid target point; expected SectionPoint, Point2D, Node, or explicit coordinates via to_coordinates()."
        )

    def apply(self, section: Section) -> Section:
        if not isinstance(self.source_component, SectionElement):
            raise AssemblyGeometryError("Invalid source component type; expected SectionElement.")

        try:
            source_node = self.source_component.get_node(self.source_node_name)
        except Exception as exc:  # noqa: BLE001
            raise AssemblyReferenceError(
                f"Missing source node '{self.source_node_name}' in component '{self.source_component.element_id}'."
            ) from exc

        target_y_mm, target_z_mm, target_point_id = self._resolve_target_point()

        dy_mm = target_y_mm - source_node.y_internal_mm
        dz_mm = target_z_mm - source_node.z_internal_mm

        translated = self.source_component.translated(dy_mm, dz_mm)
        trace = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "source_component_id": self.source_component.element_id,
            "source_node_name": self.source_node_name,
            "target_y_internal_mm": target_y_mm,
            "target_z_internal_mm": target_z_mm,
            "translation_dy_mm": dy_mm,
            "translation_dz_mm": dz_mm,
            "create_connection": self.create_connection,
            "target_point_id": target_point_id,
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
