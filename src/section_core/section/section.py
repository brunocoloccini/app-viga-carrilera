"""Section container and gross elastic property calculations."""

from __future__ import annotations

from dataclasses import dataclass, field

from section_core.components import PlateElement, RectangularElement, SectionElement
from section_core.geometry import Node, SectionLine, SectionPoint

from .errors import (
    DuplicateComponentError,
    EmptySectionError,
    InvalidSectionPropertiesError,
    UnsupportedComponentTypeError,
)
from .properties import GrossElasticProperties


@dataclass
class Section:
    section_id: str
    name: str | None = None
    components: list[SectionElement] = field(default_factory=list)
    metadata: dict[str, object] | None = None

    def _validate_supported(self, component: SectionElement) -> None:
        if not isinstance(component, (RectangularElement, PlateElement)):
            raise UnsupportedComponentTypeError(
                f"Unsupported component type for V1-005: {type(component).__name__}. "
                "Only RectangularElement and PlateElement are supported."
            )

    def add_component(self, component: SectionElement) -> None:
        self._validate_supported(component)
        if component.element_id in self.component_ids():
            raise DuplicateComponentError(f"Duplicate component_id '{component.element_id}' in section '{self.section_id}'.")
        self.components.append(component)

    def component_ids(self) -> list[str]:
        return [component.element_id for component in self.components]

    def has_component(self, component_id: str) -> bool:
        return component_id in self.component_ids()

    def get_component(self, component_id: str) -> SectionElement:
        for component in self.components:
            if component.element_id == component_id:
                return component
        raise EmptySectionError(f"Component '{component_id}' not found in section '{self.section_id}'.")

    def nodes(self) -> list[Node]:
        return [node for component in self.components for node in component.nodes()]

    def lines(self) -> list[SectionLine]:
        return [line for component in self.components for line in component.lines()]

    def reference_points(self) -> list[SectionPoint]:
        return [point for component in self.components for point in component.reference_points().values()]

    def bounding_box(self) -> tuple[float, float, float, float]:
        if not self.components:
            raise EmptySectionError("Section is empty; cannot compute bounding box.")
        bboxes = [component.bounding_box() for component in self.components]
        return (
            min(box[0] for box in bboxes),
            min(box[1] for box in bboxes),
            max(box[2] for box in bboxes),
            max(box[3] for box in bboxes),
        )

    def gross_area_mm2(self) -> float:
        if not self.components:
            raise EmptySectionError("Section is empty; cannot compute gross area.")
        return sum(component.area_mm2() for component in self.components)

    def gross_centroid(self) -> tuple[float, float]:
        area = self.gross_area_mm2()
        if area <= 0.0:
            raise InvalidSectionPropertiesError("Invalid zero total area; cannot compute section centroid.")
        sum_ay = 0.0
        sum_az = 0.0
        for component in self.components:
            center = component.centroid_point()
            comp_area = component.area_mm2()
            sum_ay += comp_area * center.y_internal_mm
            sum_az += comp_area * center.z_internal_mm
        return (sum_ay / area, sum_az / area)

    def gross_elastic_properties(self) -> GrossElasticProperties:
        if not self.components:
            raise EmptySectionError("Section is empty; cannot compute gross elastic properties.")

        area = self.gross_area_mm2()
        if area <= 0.0:
            raise InvalidSectionPropertiesError("Invalid zero total area; cannot compute elastic properties.")

        yc, zc = self.gross_centroid()
        y_min, z_min, y_max, z_max = self.bounding_box()

        Iyy = 0.0
        Izz = 0.0
        Iyz = 0.0
        trace: list[dict[str, float | str]] = []

        for component in self.components:
            self._validate_supported(component)
            if component.rotation_deg != 0.0:
                raise InvalidSectionPropertiesError(
                    f"Gross elastic properties for rotated components are not implemented yet (component_id={component.element_id}, rotation_deg={component.rotation_deg})."
                )
            comp_area = component.area_mm2()
            comp_center = component.centroid_point()
            dy = comp_center.y_internal_mm - yc
            dz = comp_center.z_internal_mm - zc
            iyy_local = component.width_internal_mm * (component.height_internal_mm ** 3) / 12.0
            izz_local = component.height_internal_mm * (component.width_internal_mm ** 3) / 12.0
            iyz_local = 0.0
            iyy_contrib = iyy_local + comp_area * (dz ** 2)
            izz_contrib = izz_local + comp_area * (dy ** 2)
            iyz_contrib = iyz_local + comp_area * dy * dz
            Iyy += iyy_contrib
            Izz += izz_contrib
            Iyz += iyz_contrib
            trace.append(
                {
                    "component_id": component.element_id,
                    "area_mm2": comp_area,
                    "centroid_y_mm": comp_center.y_internal_mm,
                    "centroid_z_mm": comp_center.z_internal_mm,
                    "Iyy_local_mm4": iyy_local,
                    "Izz_local_mm4": izz_local,
                    "Iyz_local_mm4": iyz_local,
                    "dy_mm": dy,
                    "dz_mm": dz,
                    "Iyy_contribution_mm4": iyy_contrib,
                    "Izz_contribution_mm4": izz_contrib,
                    "Iyz_contribution_mm4": iyz_contrib,
                }
            )

        den_top = z_max - zc
        den_bottom = zc - z_min
        den_left = yc - y_min
        den_right = y_max - yc

        if den_top <= 0 or den_bottom <= 0 or den_left <= 0 or den_right <= 0:
            raise InvalidSectionPropertiesError("Invalid section modulus denominator; check centroid and bounding box extents.")

        return GrossElasticProperties(
            area_mm2=area,
            centroid_y_mm=yc,
            centroid_z_mm=zc,
            Iyy_mm4=Iyy,
            Izz_mm4=Izz,
            Iyz_mm4=Iyz,
            y_min_mm=y_min,
            y_max_mm=y_max,
            z_min_mm=z_min,
            z_max_mm=z_max,
            S_y_top_mm3=Iyy / den_top,
            S_y_bottom_mm3=Iyy / den_bottom,
            S_z_left_mm3=Izz / den_left,
            S_z_right_mm3=Izz / den_right,
            overlap_check_status="not_implemented",
            trace=trace,
        )
