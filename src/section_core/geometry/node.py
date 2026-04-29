"""Section node model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    node_id: str
    name: str
    y_internal_mm: float
    z_internal_mm: float
    element_id: str | None = None
    node_type: str = "vertex"
