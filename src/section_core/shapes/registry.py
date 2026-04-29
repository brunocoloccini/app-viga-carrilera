"""Registry for tabulated structural profile records."""

from __future__ import annotations

from section_core.components import LibraryShapeComponent

from .errors import DuplicateShapeError, InvalidShapeRecordError, ShapeNotFoundError
from .shape_record import ShapeRecord


class ShapeLibraryRegistry:
    def __init__(self, records: list[ShapeRecord] | None = None) -> None:
        self._records: dict[str, ShapeRecord] = {}
        if records:
            for record in records:
                self.add(record)

    def add(self, record: ShapeRecord) -> None:
        if not isinstance(record, ShapeRecord):
            raise InvalidShapeRecordError("record must be a ShapeRecord.")
        if record.shape_id in self._records:
            raise DuplicateShapeError(f"Shape '{record.shape_id}' already exists.")
        self._records[record.shape_id] = record

    def has(self, shape_id: str) -> bool:
        return shape_id in self._records

    def get(self, shape_id: str) -> ShapeRecord:
        if shape_id not in self._records:
            raise ShapeNotFoundError(f"Shape '{shape_id}' was not found.")
        return self._records[shape_id]

    def find_by_name(self, shape_family: str, shape_name: str) -> ShapeRecord:
        for record in self._records.values():
            if record.shape_family == shape_family and record.shape_name == shape_name:
                return record
        raise ShapeNotFoundError(f"Shape '{shape_family}/{shape_name}' was not found.")

    def list_families(self) -> list[str]:
        return sorted({record.shape_family for record in self._records.values()})

    def list_shapes(self, shape_family: str | None = None) -> list[ShapeRecord]:
        records = list(self._records.values())
        if shape_family is not None:
            records = [record for record in records if record.shape_family == shape_family]
        return sorted(records, key=lambda r: r.shape_id)

    def to_component(self, shape_id: str, element_id: str, center_y: float = 0, center_z: float = 0, center_unit: str = "mm", material_id: str | None = None, metadata: dict | None = None) -> LibraryShapeComponent:
        record = self.get(shape_id)
        return LibraryShapeComponent.from_tabulated(
            element_id=element_id,
            source="library",
            material_id=material_id,
            metadata=metadata,
            shape_family=record.shape_family,
            shape_name=record.shape_name,
            center_y=center_y,
            center_z=center_z,
            center_unit=center_unit,
            depth=record.depth_mm,
            depth_unit="mm",
            width=record.width_mm,
            width_unit="mm",
            area=record.area_mm2,
            area_unit="mm2",
            Iyy=record.Iyy_mm4,
            Iyy_unit="mm4",
            Izz=record.Izz_mm4,
            Izz_unit="mm4",
            Iyz=record.Iyz_mm4,
            Iyz_unit="mm4",
            weight_per_length=record.weight_per_length,
            J_mm4=record.J_mm4,
            Cw_mm6=record.Cw_mm6,
            S_y_top_mm3=record.S_y_top_mm3,
            S_y_bottom_mm3=record.S_y_bottom_mm3,
            S_z_left_mm3=record.S_z_left_mm3,
            S_z_right_mm3=record.S_z_right_mm3,
        )

    def to_records(self) -> list[dict]:
        return [record.to_dict() for record in self.list_shapes()]

    @classmethod
    def from_records(cls, records: list[dict]) -> "ShapeLibraryRegistry":
        registry = cls()
        for item in records:
            registry.add(ShapeRecord(**item))
        return registry


def build_sample_shape_library_registry() -> ShapeLibraryRegistry:
    """Build tiny fake sample data set for tests/examples only."""
    return ShapeLibraryRegistry(
        records=[
            ShapeRecord(
                shape_id="W_TEST_600",
                shape_family="W",
                shape_name="W_TEST_600",
                source="sample_fake_data",
                depth_mm=600.0,
                width_mm=250.0,
                area_mm2=22000.0,
                Iyy_mm4=1.30e9,
                Izz_mm4=1.10e8,
                metadata={"note": "FAKE SAMPLE DATA ONLY - not a real profile table entry."},
            ),
            ShapeRecord(
                shape_id="IPE_TEST_300",
                shape_family="IPE",
                shape_name="IPE_TEST_300",
                source="sample_fake_data",
                depth_mm=300.0,
                width_mm=150.0,
                area_mm2=5300.0,
                Iyy_mm4=8.4e7,
                Izz_mm4=6.3e6,
                metadata={"note": "FAKE SAMPLE DATA ONLY - not a real profile table entry."},
            ),
        ]
    )
