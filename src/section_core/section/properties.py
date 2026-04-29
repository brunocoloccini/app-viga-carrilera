"""Section property models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GrossElasticProperties:
    area_mm2: float
    centroid_y_mm: float
    centroid_z_mm: float
    Iyy_mm4: float
    Izz_mm4: float
    Iyz_mm4: float
    y_min_mm: float
    y_max_mm: float
    z_min_mm: float
    z_max_mm: float
    S_y_top_mm3: float
    S_y_bottom_mm3: float
    S_z_left_mm3: float
    S_z_right_mm3: float
    overlap_check_status: str = "not_implemented"
    trace: list[dict[str, float | str]] = field(default_factory=list)
