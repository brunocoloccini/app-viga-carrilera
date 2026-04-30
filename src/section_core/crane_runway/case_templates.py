"""Built-in JSON case templates for crane runway workflows (V1-056)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .case_io import dump_crane_runway_case_json, run_crane_runway_case_dict
from .case_schema import CASE_SCHEMA_VERSION, assert_valid_crane_runway_case_dict


class CaseTemplateError(ValueError):
    """Base error for crane runway case template handling."""


class InvalidCaseTemplateError(CaseTemplateError):
    """Raised when a case template definition is invalid."""


class DuplicateCaseTemplateError(CaseTemplateError):
    """Raised when template registration duplicates an existing template_id."""


class CaseTemplateNotFoundError(CaseTemplateError):
    """Raised when requesting an unknown template_id."""


@dataclass(frozen=True)
class CraneRunwayCaseTemplate:
    template_id: str
    description: str
    case_data: dict[str, Any]
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.template_id, str) or not self.template_id.strip():
            raise InvalidCaseTemplateError("template_id is required.")
        if not isinstance(self.description, str) or not self.description.strip():
            raise InvalidCaseTemplateError("description is required.")
        if not isinstance(self.case_data, dict):
            raise InvalidCaseTemplateError("case_data must be an object.")
        if self.case_data.get("schema_version") != CASE_SCHEMA_VERSION:
            raise InvalidCaseTemplateError(
                f"template '{self.template_id}' must include schema_version '{CASE_SCHEMA_VERSION}'."
            )

    def generate_case_dict(self, *, case_id: str | None = None) -> dict[str, Any]:
        payload = json.loads(json.dumps(self.case_data))
        payload["schema_version"] = CASE_SCHEMA_VERSION
        payload["case_id"] = case_id or payload.get("case_id") or self.template_id
        return payload


@dataclass
class CraneRunwayCaseTemplateRegistry:
    templates: dict[str, CraneRunwayCaseTemplate] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None

    def add_template(self, template: CraneRunwayCaseTemplate) -> None:
        if template.template_id in self.templates:
            raise DuplicateCaseTemplateError(f"Duplicate case template_id: {template.template_id}")
        self.templates[template.template_id] = template

    def get_template(self, template_id: str) -> CraneRunwayCaseTemplate:
        if template_id not in self.templates:
            raise CaseTemplateNotFoundError(f"Case template not found: {template_id}")
        return self.templates[template_id]

    def list_template_ids(self) -> list[str]:
        return sorted(self.templates)

    def has_template(self, template_id: str) -> bool:
        return template_id in self.templates



def _base_template_case() -> dict[str, Any]:
    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "case_id": "template_case",
        "description": "Template crane runway case.",
        "shape_library_path": "data/shape_libraries/cirsoc_sample_shapes.json",
        "base_shape_id": "CIRSOC_IPN_200",
        "section": {
            "section_id": "ipn_200_with_cover_plate",
            "base_component_id": "ipn_200",
            "base_center_y": {"value": 0, "unit": "mm"},
            "base_center_z": {"value": 100, "unit": "mm"},
            "cover_plate": {
                "enabled": True,
                "element_id": "cover_plate",
                "width": {"value": 140, "unit": "mm"},
                "thickness": {"value": 10, "unit": "mm"},
                "weld_size": {"value": 6, "unit": "mm"},
                "weld_type": "fillet",
            },
        },
        "span": {"value": 6, "unit": "m"},
        "analysis": {
            "movement_step": {"value": 250, "unit": "mm"},
            "station_step": {"value": 500, "unit": "mm"},
            "E": {"value": 200000, "unit": "MPa"},
        },
        "crane": {
            "crane_id": "demo_crane",
            "name": "Demo crane",
            "vertical_impact_factor": 0.25,
            "lateral_force_factor": 0.1,
            "longitudinal_force_factor": 0.0,
            "wheels": [
                {"wheel_id": "W1", "position_x": {"value": 0, "unit": "mm"}, "vertical_force": {"value": 80, "unit": "kN"}},
                {"wheel_id": "W2", "position_x": {"value": 2, "unit": "m"}, "vertical_force": {"value": 80, "unit": "kN"}},
            ],
        },
        "serviceability_limits": [{"limit_id": "L_over_600", "type": "span_over", "divisor": 600}],
        "stress_limits": [
            {"limit_id": "0.66Fy", "type": "fraction_of_Fy", "Fy": {"value": 250, "unit": "MPa"}, "factor": 0.66}
        ],
        "rail_eccentricity": {
            "enabled": True,
            "model_id": "rail_eccentricity",
            "vertical_eccentricity_y": {"value": 25, "unit": "mm"},
            "lateral_load_height_z": {"value": 100, "unit": "mm"},
            "include_vertical": True,
            "include_lateral": True,
        },
        "warnings": [
            "CIRSOC sample profile data is manually curated and must be independently verified before production use.",
            "No CIRSOC design-code checks are performed.",
        ],
        "metadata": {"is_demo": True},
    }


def build_default_crane_runway_case_template_registry() -> CraneRunwayCaseTemplateRegistry:
    registry = CraneRunwayCaseTemplateRegistry(metadata={"template_scope": "crane_runway_beta"})

    with_cover = _base_template_case()
    with_cover["case_id"] = "with_cover_and_eccentricity"
    with_cover["description"] = "Baseline demo case with cover plate and rail eccentricity enabled."
    registry.add_template(CraneRunwayCaseTemplate("ipn-with-cover", with_cover["description"], with_cover))

    without_cover = _base_template_case()
    without_cover["case_id"] = "without_cover_plate"
    without_cover["description"] = "Variant with cover plate disabled and rail eccentricity enabled."
    without_cover["section"]["cover_plate"]["enabled"] = False
    registry.add_template(CraneRunwayCaseTemplate("ipn-without-cover", without_cover["description"], without_cover))

    no_ecc = _base_template_case()
    no_ecc["case_id"] = "without_rail_eccentricity"
    no_ecc["description"] = "Variant with rail eccentricity disabled."
    no_ecc["rail_eccentricity"]["enabled"] = False
    registry.add_template(CraneRunwayCaseTemplate("ipn-no-rail-eccentricity", no_ecc["description"], no_ecc))

    for template_id in registry.list_template_ids():
        template_data = registry.get_template(template_id).generate_case_dict()
        assert_valid_crane_runway_case_dict(template_data, strict=True)
        run_crane_runway_case_dict(template_data)

    return registry


def get_crane_runway_case_template(template_id: str) -> CraneRunwayCaseTemplate:
    return build_default_crane_runway_case_template_registry().get_template(template_id)


def list_crane_runway_case_template_ids() -> list[str]:
    return build_default_crane_runway_case_template_registry().list_template_ids()


def write_crane_runway_case_template(
    template_id: str,
    output_path: str | Path,
    *,
    overwrite: bool = False,
    case_id: str | None = None,
) -> Path:
    template = get_crane_runway_case_template(template_id)
    out = Path(output_path)
    if out.exists() and not overwrite:
        raise CaseTemplateError(f"Output file already exists: {out}")
    dump_crane_runway_case_json(template.generate_case_dict(case_id=case_id), out)
    return out
