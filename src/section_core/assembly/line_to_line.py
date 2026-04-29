"""Line-to-line geometric assembly operation."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees
from typing import Any

from section_core.geometry import Transform2D

from section_core.components import SectionElement
from section_core.geometry import GeometryTolerance, SectionLine
from section_core.interfaces import ComponentInterface, WeldInterface
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
    allow_rotation: bool = False
    rotation_mode: str = "align_direction"
    alignment_mode: str = "midpoint_to_midpoint"
    overlap_mode: str = "none"
    normal_offset_mm: float = 0.0
    tangential_offset_mm: float = 0.0
    reverse_source_direction: bool = False
    create_connection: bool = False
    metadata: dict[str, Any] | None = None
    interface_type: str = "shared_boundary"
    weld_size_mm: float | None = None
    weld_type: str = "fillet"

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

    def _line_point(self, line: SectionLine, mode: str, *, is_source: bool) -> tuple[float, float]:
        if mode == "midpoint":
            p = line.midpoint
        elif mode == "start":
            p = line.start
        elif mode == "end":
            p = line.end
        else:
            role = "source" if is_source else "target"
            raise AssemblyGeometryError(f"Unsupported {role} alignment selector '{mode}'.")
        return p.y_internal_mm, p.z_internal_mm

    def _resolve_alignment_mode(self) -> tuple[str, str]:
        mode = self.alignment_mode
        mapping = {
            "midpoint_to_midpoint": ("midpoint", "midpoint"),
            "start_to_start": ("start", "start"),
            "end_to_end": ("end", "end"),
            "start_to_end": ("start", "end"),
            "end_to_start": ("end", "start"),
        }
        if mode not in mapping:
            raise AssemblyGeometryError(f"Unsupported alignment mode '{mode}'.")
        return mapping[mode]

    def _resolve_overlap_mode(self) -> tuple[str, str]:
        mapping = {
            "none": self._resolve_alignment_mode(),
            "centered": ("midpoint", "midpoint"),
            "from_target_start": ("start", "start"),
            "from_target_end": ("end", "end"),
        }
        if self.overlap_mode not in mapping:
            raise AssemblyGeometryError(f"Unsupported overlap mode '{self.overlap_mode}'.")
        return mapping[self.overlap_mode]

    def apply(self, section: Section) -> Section:
        if not isinstance(self.source_component, SectionElement):
            raise AssemblyGeometryError("Invalid source component type; expected SectionElement.")
        if self.rotation_mode != "align_direction":
            raise AssemblyGeometryError(f"Unsupported rotation mode '{self.rotation_mode}'.")

        source_line = self._resolve_source_line()
        target_line = self._resolve_target_line(section)
        tolerance = GeometryTolerance.default()

        rotation_angle_deg = 0.0
        rotation_center = source_line.midpoint
        if not source_line.is_parallel_to(target_line, tolerance):
            if not self.allow_rotation:
                raise AssemblyGeometryError("Source and target lines are not parallel/anti-parallel and allow_rotation is False.")
            sy, sz = source_line.direction
            ty, tz = target_line.direction
            source_angle = degrees(atan2(sz, sy))
            target_angle = degrees(atan2(tz, ty))
            if self.reverse_source_direction:
                target_angle += 180.0
            rotation_angle_deg = target_angle - source_angle

        rotated = self.source_component.transformed(
            Transform2D.rotation(rotation_angle_deg, rotation_center.y_internal_mm, rotation_center.z_internal_mm)
        )
        rotated_source_line = rotated.get_reference_line(self.source_line_name)

        source_selector, target_selector = self._resolve_overlap_mode()
        source_y, source_z = self._line_point(rotated_source_line, source_selector, is_source=True)
        target_y, target_z = self._line_point(target_line, target_selector, is_source=False)

        ty, tz = target_line.direction
        ny, nz = -tz, ty
        target_align_y = target_y + float(self.tangential_offset_mm) * ty + float(self.normal_offset_mm) * ny
        target_align_z = target_z + float(self.tangential_offset_mm) * tz + float(self.normal_offset_mm) * nz

        dy_mm = target_align_y - source_y
        dz_mm = target_align_z - source_z
        transformed = rotated.transformed(Transform2D.translation(dy_mm, dz_mm))

        source_len = rotated_source_line.length_mm
        target_len = target_line.length_mm
        overlap_len = min(source_len, target_len) if self.overlap_mode != "none" else None
        trace = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "source_component_id": self.source_component.element_id,
            "source_line_name": self.source_line_name,
            "target_component_id": self.target_component_id,
            "target_line_name": self.target_line_name,
            "allow_rotation": self.allow_rotation,
            "rotation_angle_deg": rotation_angle_deg,
            "rotation_center_y_mm": rotation_center.y_internal_mm,
            "rotation_center_z_mm": rotation_center.z_internal_mm,
            "alignment_mode": self.alignment_mode,
            "overlap_mode": self.overlap_mode,
            "normal_offset_mm": float(self.normal_offset_mm),
            "tangential_offset_mm": float(self.tangential_offset_mm),
            "translation_dy_mm": dy_mm,
            "translation_dz_mm": dz_mm,
            "source_line_length_mm": source_len,
            "target_line_length_mm": target_len,
            "overlap_length_mm": overlap_len,
            "reverse_source_direction": self.reverse_source_direction,
            "create_connection": self.create_connection,
            "note": "No boolean merge or structural connection implied.",
        }
        merged_metadata = dict(transformed.metadata) if transformed.metadata is not None else {}
        merged_metadata["assembly"] = trace
        transformed = transformed.__class__(**{**transformed.__dict__, "metadata": merged_metadata})

        new_section = Section(section_id=section.section_id, name=section.name, components=list(section.components), interfaces=list(section.interfaces), metadata=dict(section.metadata) if section.metadata is not None else None)
        try:
            new_section.add_component(transformed)
        except DuplicateComponentError as exc:
            raise AssemblyReferenceError(f"Duplicate component id '{transformed.element_id}' when adding transformed component.") from exc
        except UnsupportedComponentTypeError as exc:
            raise AssemblyGeometryError(str(exc)) from exc

        if self.create_connection:
            iface_metadata = {
                "created_by_operation_id": self.operation_id,
                "source_line_name": self.source_line_name,
                "target_line_name": self.target_line_name,
                "note": "Interface is recorded but not structurally verified.",
            }
            interface_id = f"IF_{self.operation_id}_{self.target_component_id}_{transformed.element_id}"
            if self.interface_type == "weld":
                interface = WeldInterface(
                    interface_id=interface_id,
                    component_a_id=self.target_component_id,
                    component_b_id=transformed.element_id,
                    line_a_name=self.target_line_name,
                    line_b_name=self.source_line_name,
                    length_mm=overlap_len,
                    metadata=iface_metadata,
                    weld_size_mm=self.weld_size_mm,
                    weld_type=self.weld_type,
                )
            else:
                interface = ComponentInterface(
                    interface_id=interface_id,
                    interface_type=self.interface_type,
                    component_a_id=self.target_component_id,
                    component_b_id=transformed.element_id,
                    line_a_name=self.target_line_name,
                    line_b_name=self.source_line_name,
                    length_mm=overlap_len,
                    metadata=iface_metadata,
                )
            new_section.add_interface(interface)
        return new_section
