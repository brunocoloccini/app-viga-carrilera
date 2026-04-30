"""Registry for crane rail records."""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import DuplicateRailRecordError, InvalidRailRecordError, RailRecordNotFoundError
from .rail_record import CraneRailRecord


@dataclass
class CraneRailRegistry:
    records: dict[str, CraneRailRecord] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.records, dict):
            raise InvalidRailRecordError("records must be a dict[str, CraneRailRecord].")
        normalized: dict[str, CraneRailRecord] = {}
        for rail_id, record in self.records.items():
            if not isinstance(record, CraneRailRecord):
                raise InvalidRailRecordError("records must contain CraneRailRecord values.")
            if rail_id != record.rail_id:
                raise InvalidRailRecordError("record key must match record.rail_id.")
            normalized[rail_id] = record
        self.records = normalized
        if self.metadata is None:
            self.metadata = {}

    def add(self, record: CraneRailRecord) -> None:
        if not isinstance(record, CraneRailRecord):
            raise InvalidRailRecordError("record must be a CraneRailRecord.")
        if record.rail_id in self.records:
            raise DuplicateRailRecordError(f"Rail '{record.rail_id}' already exists.")
        self.records[record.rail_id] = record

    def get(self, rail_id: str) -> CraneRailRecord:
        if rail_id not in self.records:
            raise RailRecordNotFoundError(f"Rail '{rail_id}' was not found.")
        return self.records[rail_id]

    def has(self, rail_id: str) -> bool:
        return rail_id in self.records

    def list_rail_ids(self) -> list[str]:
        return sorted(self.records.keys())

    def list_families(self) -> list[str]:
        return sorted({record.rail_family for record in self.records.values()})

    def list_by_family(self, rail_family: str) -> list[CraneRailRecord]:
        return sorted(
            [record for record in self.records.values() if record.rail_family == rail_family],
            key=lambda record: record.rail_id,
        )

    def to_records(self) -> list[dict]:
        return [self.records[rail_id].to_dict() for rail_id in self.list_rail_ids()]

    @classmethod
    def from_records(cls, records: list[CraneRailRecord]) -> "CraneRailRegistry":
        registry = cls()
        for record in records:
            if not isinstance(record, CraneRailRecord):
                raise InvalidRailRecordError("from_records expects CraneRailRecord values.")
            registry.add(record)
        return registry

    def to_dict(self) -> dict:
        return {
            "records": self.to_records(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CraneRailRegistry":
        records = [CraneRailRecord(**item) for item in data.get("records", [])]
        return cls.from_records(records=records)


def build_sample_crane_rail_registry() -> CraneRailRegistry:
    metadata = {
        "sample_rail": True,
        "is_real_profile": False,
        "requires_independent_verification_before_design_use": True,
        "not_official_complete_rail_library": True,
    }
    return CraneRailRegistry.from_records(
        records=[
            CraneRailRecord.from_values(
                rail_id="RAIL_TEST_A",
                rail_name="RAIL TEST A",
                rail_family="TEST_RAIL",
                source="fake_test_data",
                height=100,
                height_unit="mm",
                head_width=50,
                head_width_unit="mm",
                base_width=100,
                base_width_unit="mm",
                area=5000,
                area_unit="mm2",
                weight_per_length=39.25,
                weight_per_length_unit="kg/m",
                Ixx=8_000_000,
                Iyy=1_000_000,
                Sxx_head=120_000,
                Sxx_base=100_000,
                Syy=40_000,
                centroid_from_base=45,
                metadata=metadata,
            ),
            CraneRailRecord.from_values(
                rail_id="RAIL_TEST_B",
                rail_name="RAIL TEST B",
                rail_family="TEST_RAIL",
                source="fake_test_data",
                height=120,
                height_unit="mm",
                head_width=60,
                head_width_unit="mm",
                base_width=120,
                base_width_unit="mm",
                area=7000,
                area_unit="mm2",
                weight_per_length=54.95,
                weight_per_length_unit="kg/m",
                Ixx=14_000_000,
                Iyy=1_800_000,
                Sxx_head=180_000,
                Sxx_base=150_000,
                Syy=60_000,
                centroid_from_base=55,
                metadata=metadata,
            ),
        ]
    )
