"""Coordinate system manager for section coordinates."""

from __future__ import annotations

from dataclasses import dataclass

from section_core.units import Dimension, UnitRegistry

from .errors import UnsupportedCoordinateFrameError
from .node import Node


@dataclass
class CoordinateFrame:
    origin_mode: str = "fixed"
    origin_y_internal_mm: float = 0.0
    origin_z_internal_mm: float = 0.0
    rotation_deg: float = 0.0
    origin_node: Node | None = None
    centroid_internal_fn: callable | None = None
    frozen_origin_internal: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if abs(self.rotation_deg) > 0.0:
            raise UnsupportedCoordinateFrameError(
                "Rotation is not supported yet. Only translation-only frames are supported."
            )
        valid_modes = {"fixed", "node_linked", "node_frozen", "centroid_dynamic", "centroid_frozen"}
        if self.origin_mode not in valid_modes:
            raise ValueError(f"Unknown origin mode: {self.origin_mode}")

    @classmethod
    def fixed(cls, y_internal_mm: float = 0.0, z_internal_mm: float = 0.0) -> "CoordinateFrame":
        return cls(origin_mode="fixed", origin_y_internal_mm=y_internal_mm, origin_z_internal_mm=z_internal_mm)

    @classmethod
    def from_node(cls, node: Node, frozen: bool = False) -> "CoordinateFrame":
        mode = "node_frozen" if frozen else "node_linked"
        frozen_origin = (node.y_internal_mm, node.z_internal_mm) if frozen else None
        return cls(origin_mode=mode, origin_node=node, frozen_origin_internal=frozen_origin)

    @classmethod
    def from_centroid(cls, centroid_internal_fn: callable, frozen: bool = False) -> "CoordinateFrame":
        mode = "centroid_frozen" if frozen else "centroid_dynamic"
        frozen_origin = centroid_internal_fn() if frozen else None
        return cls(origin_mode=mode, centroid_internal_fn=centroid_internal_fn, frozen_origin_internal=frozen_origin)

    def origin_internal(self) -> tuple[float, float]:
        if self.origin_mode == "fixed":
            return (self.origin_y_internal_mm, self.origin_z_internal_mm)
        if self.origin_mode == "node_linked":
            assert self.origin_node is not None
            return (self.origin_node.y_internal_mm, self.origin_node.z_internal_mm)
        if self.origin_mode == "node_frozen":
            assert self.frozen_origin_internal is not None
            return self.frozen_origin_internal
        if self.origin_mode == "centroid_dynamic":
            assert self.centroid_internal_fn is not None
            return self.centroid_internal_fn()
        assert self.frozen_origin_internal is not None
        return self.frozen_origin_internal

    def internal_to_local(self, y_internal_mm: float, z_internal_mm: float) -> tuple[float, float]:
        oy, oz = self.origin_internal()
        return (float(y_internal_mm) - oy, float(z_internal_mm) - oz)

    def local_to_internal(self, y_local: float, z_local: float, units: str = "mm") -> tuple[float, float]:
        registry = UnitRegistry()
        y_local_mm = registry.to_internal(float(y_local), units, Dimension.LENGTH)
        z_local_mm = registry.to_internal(float(z_local), units, Dimension.LENGTH)
        oy, oz = self.origin_internal()
        return (oy + y_local_mm, oz + z_local_mm)
