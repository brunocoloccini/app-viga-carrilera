from __future__ import annotations

import pytest

from section_core.crane_runway import (
    CaseTemplateNotFoundError,
    CraneRunwayCaseTemplate,
    CraneRunwayCaseTemplateRegistry,
    DuplicateCaseTemplateError,
    InvalidCaseTemplateError,
    build_default_crane_runway_case_template_registry,
    get_crane_runway_case_template,
    list_crane_runway_case_template_ids,
)
from section_core.crane_runway.case_io import run_crane_runway_case_dict
from section_core.crane_runway.case_schema import assert_valid_crane_runway_case_dict


def test_template_requires_schema_version_1_0() -> None:
    with pytest.raises(InvalidCaseTemplateError):
        CraneRunwayCaseTemplate(template_id="x", description="y", case_data={"schema_version": "0.9"})


def test_registry_add_and_duplicate_and_missing() -> None:
    reg = CraneRunwayCaseTemplateRegistry()
    t = CraneRunwayCaseTemplate(template_id="a", description="d", case_data={"schema_version": "1.0", "case_id": "a"})
    reg.add_template(t)
    assert reg.has_template("a")
    assert reg.list_template_ids() == ["a"]
    assert reg.get_template("a") == t
    with pytest.raises(DuplicateCaseTemplateError):
        reg.add_template(t)
    with pytest.raises(CaseTemplateNotFoundError):
        reg.get_template("missing")


def test_builtin_template_ids_and_generated_cases_validate_and_run() -> None:
    ids = list_crane_runway_case_template_ids()
    assert ids == ["ipn-no-rail-eccentricity", "ipn-with-cover", "ipn-without-cover"]

    registry = build_default_crane_runway_case_template_registry()
    for template_id in ids:
        case_dict = registry.get_template(template_id).generate_case_dict()
        assert case_dict["schema_version"] == "1.0"
        assert_valid_crane_runway_case_dict(case_dict, strict=True)
        result = run_crane_runway_case_dict(case_dict)
        assert result.case_id
        assert "max_vertical_moment_Nmm" in result.summary_dict


def test_get_template_by_id() -> None:
    template = get_crane_runway_case_template("ipn-with-cover")
    assert template.template_id == "ipn-with-cover"
    assert template.case_data["section"]["cover_plate"]["enabled"] is True
