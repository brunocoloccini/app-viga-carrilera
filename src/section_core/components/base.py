"""Base contracts for section components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from section_core.geometry import Node, SectionLine, SectionPoint, Transform2D


@dataclass(frozen=True)
class SectionElement(ABC):
    element_id: str
    element_type: str = "generic"
    name: str | None = None
    source: str = "user_defined"
    material_id: str | None = None
    metadata: dict[str, object] | None = None

    @abstractmethod
    def nodes(self) -> list[Node]:
        raise NotImplementedError

    @abstractmethod
    def lines(self) -> list[SectionLine]:
        raise NotImplementedError

    @abstractmethod
    def reference_points(self) -> dict[str, SectionPoint]:
        raise NotImplementedError

    @abstractmethod
    def bounding_box(self) -> tuple[float, float, float, float]:
        """Return (min_y, min_z, max_y, max_z) in internal mm."""

    @abstractmethod
    def transformed(self, transform: Transform2D) -> "SectionElement":
        raise NotImplementedError

    @abstractmethod
    def translated(self, dy_mm: float, dz_mm: float) -> "SectionElement":
        raise NotImplementedError

    @abstractmethod
    def local_reference(self) -> SectionPoint:
        """Return the default local reference point for this element."""
