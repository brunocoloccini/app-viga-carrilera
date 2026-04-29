"""Base assembly operation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from section_core.section import Section


@dataclass(frozen=True)
class AssemblyOperation:
    operation_id: str
    operation_type: str
    metadata: dict[str, Any] | None = None

    def apply(self, section: Section) -> Section:
        raise NotImplementedError
