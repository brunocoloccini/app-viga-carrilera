"""Line-to-line geometric assembly operation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from section_core.components import SectionElement
from section_core.geometry import GeometryTolerance, SectionLine
from section_core.section import Section
from section_core.section.errors import DuplicateComponentError, UnsupportedComponentTypeError

from .errors import AssemblyGeometryError, AssemblyReferenceError
from .operation import AssemblyOperation


@dataclass(frozen=True)
class LineToLineJoin(AssemblyOperation):
    source_component: SectionElement | object = None
    source_line_name: str = ""
    target_component_id: str = ""
    target_line_name: str = ""
    alignment_mode: str = "midpoint_to_midpoint"
    normal_offset_mm: float = 0.0
    tangential_offset_mm: float = 0.0
    reverse_source_direction: bool = False
    create_connection: bool = False
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_type", "line_to_line_join")

    def _resolve_source_line(self) -> SectionLine:
        try:
            return self.source_component.get_reference_line(self.source_line_name)
        except Exception as exc:  # noqa: BLE001
            raise AssemblyReferenceError(
                f"Missing source line '{self.source_line_name}' in component '{self.source_component.element_id}'."
            ) from exc

    def _resolve_target_line(self, section: Section) -> SectionLine:
        if not section.has_component(self.target_component_id):
            raise AssemblyReferenceError(
                f"Missing target component '{self.target_component_id}' in section '{section.section_id}'."
            )
        target_component = section.get_component(self.target_component_id)
        try:
            return target_component.get_reference_line(self.target_line_name)
        except Exception as exc:  # noqa: BLE001
            raise AssemblyReferenceError(
                f"Missing target line '{self.target_line_name}' in component '{self.target_component_id}'."
            ) from exc

    def _alignment_point(self, line: SectionLine) -> tuple[float, float]:
        if self.alignment_mode == "midpoint_to_midpoint":
            mid = line.midpoint
            return mid.y_internal_mm, mid.z_internal_mm
        raise AssemblyGeometryError(
            f"Unsupported alignment mode '{self.alignment_mode}' for V1-008; only 'midpoint_to_midpoint' is supported."
        )

    def apply(self, section: Section) -> Section:
        if not isinstance(self.source_component, SectionElement):
            raise AssemblyGeometryError("Invalid source component type; expected SectionElement.")

        source_line = self._resolve_source_line()
        target_line = self._resolve_target_line(section)
        tolerance = GeometryTolerance.default()

        if not source_line.is_parallel_to(target_line, tolerance):
            raise AssemblyGeometryError(
                "Source and target lines are not parallel/anti-parallel; rotation is not implemented in V1-008."
            )

        source_y, source_z = self._alignment_point(source_line)
        target_y, target_z = self._alignment_point(target_line)

        ty, tz = target_line.direction
        ny, nz = -tz, ty

        target_align_y = target_y + float(self.tangential_offset_mm) * ty + float(self.normal_offset_mm) * ny
        target_align_z = target_z + float(self.tangential_offset_mm) * tz + float(self.normal_offset_mm) * nz

        dy_mm = target_align_y - source_y
        dz_mm = target_align_z - source_z

        translated = self.source_component.translated(dy_mm, dz_mm)
        trace = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "source_component_id": self.source_component.element_id,
            "source_line_name": self.source_line_name,
            "target_component_id": self.target_component_id,
            "target_line_name": self.target_line_name,
            "alignment_mode": self.alignment_mode,
            "normal_offset_mm": float(self.normal_offset_mm),
            "tangential_offset_mm": float(self.tangential_offset_mm),
            "translation_dy_mm": dy_mm,
            "translation_dz_mm": dz_mm,
            "reverse_source_direction": self.reverse_source_direction,
            "create_connection": self.create_connection,
            "connection_note": "Geometric alignment only; no connection/composite action is implied.",
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
