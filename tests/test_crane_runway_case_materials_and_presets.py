from __future__ import annotations

from pathlib import Path

import pytest

from section_core.crane_runway import (
    InvalidCraneRunwayCaseError,
    build_workflow_input_from_case_dict,
    load_crane_runway_case_json,
    run_crane_runway_case_json,
    validate_crane_runway_case_dict,
)


def _base_case() -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / "cases" / "crane_runway_case_with_cover_and_eccentricity.json"
    return load_crane_runway_case_json(path)


def _with_material_and_presets() -> dict:
    case = _base_case()
    case["material"] = {
        "material_id": "F24",
        "Fy": {"value": 235, "unit": "MPa"},
        "Fu": {"value": 370, "unit": "MPa"},
        "E": {"value": 200000, "unit": "MPa"},
        "source": "sample_data",
        "metadata": {"requires_independent_verification_before_design_use": True},
    }
    case["criteria_presets"] = {"deflection": ["deflection_L_over_600"], "stress": ["stress_0_66Fy"]}
    return case


def test_material_block_validation_cases():
    case = _with_material_and_presets()
    assert validate_crane_runway_case_dict(case, strict=True).valid

    bad = _with_material_and_presets()
    bad["material"].pop("Fy")
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _with_material_and_presets()
    bad["material"]["Fy"] = {"value": 235}
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _with_material_and_presets()
    bad["material"]["metadata"] = []
    assert not validate_crane_runway_case_dict(bad, strict=True).valid


def test_workflow_material_parsing_and_E_precedence():
    case = _with_material_and_presets()
    wi = build_workflow_input_from_case_dict(case)
    assert wi.metadata["material"]["Fy_internal_MPa"] == pytest.approx(235.0)

    case_no_analysis_e = _with_material_and_presets()
    case_no_analysis_e["analysis"].pop("E")
    wi_no_analysis_e = build_workflow_input_from_case_dict(case_no_analysis_e)
    assert wi_no_analysis_e.E_internal_MPa == pytest.approx(200000.0)

    case_with_both = _with_material_and_presets()
    case_with_both["analysis"]["E"] = {"value": 190000, "unit": "MPa"}
    wi_both = build_workflow_input_from_case_dict(case_with_both)
    assert wi_both.E_internal_MPa == pytest.approx(190000.0)


def test_criteria_preset_schema_shapes_and_rejections():
    case = _with_material_and_presets()
    case["criteria_presets"] = {"deflection": ["deflection_L_over_600", {"preset_id": "deflection_L_over_750", "limit_id": "x"}]}
    assert validate_crane_runway_case_dict(case, strict=True).valid

    case = _with_material_and_presets()
    case["criteria_presets"] = {"stress": ["stress_0_66Fy", {"preset_id": "stress_0_90Fy", "Fy": {"value": 250, "unit": "MPa"}}]}
    assert validate_crane_runway_case_dict(case, strict=True).valid

    bad = _with_material_and_presets()
    bad["criteria_presets"]["deflection"] = [123]
    assert not validate_crane_runway_case_dict(bad, strict=True).valid

    bad = _with_material_and_presets()
    bad["criteria_presets"]["stress"] = [{"preset_id": "stress_0_90Fy", "Fy": {"value": 250}}]
    assert not validate_crane_runway_case_dict(bad, strict=True).valid


def test_case_io_preset_conversion_and_errors():
    case = _with_material_and_presets()
    wi = build_workflow_input_from_case_dict(case)
    assert any(l.limit_id == "deflection_L_over_600" for l in wi.serviceability_limits)
    assert any(l.limit_id == "stress_0_66Fy" for l in wi.stress_limits)

    case = _with_material_and_presets()
    case["criteria_presets"]["stress"] = [{"preset_id": "stress_0_66Fy", "Fy": {"value": 300, "unit": "MPa"}}]
    wi = build_workflow_input_from_case_dict(case)
    stress = next(l for l in wi.stress_limits if l.limit_id == "stress_0_66Fy")
    assert stress.Fy_internal_MPa == pytest.approx(300.0)

    case = _base_case()
    case["criteria_presets"] = {"stress": ["stress_0_66Fy"]}
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(case)

    case = _with_material_and_presets()
    case["criteria_presets"]["deflection"] = ["missing_deflection"]
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(case)

    case = _with_material_and_presets()
    case["criteria_presets"]["stress"] = ["missing_stress"]
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(case)

    case = _with_material_and_presets()
    case["serviceability_limits"] = [{"limit_id": "explicit", "type": "span_over", "divisor": 500}]
    wi = build_workflow_input_from_case_dict(case)
    assert any(l.limit_id == "explicit" for l in wi.serviceability_limits)
    assert any(l.limit_id == "deflection_L_over_600" for l in wi.serviceability_limits)


def test_example_case_with_material_and_presets_executes():
    path = Path(__file__).resolve().parents[1] / "examples" / "cases" / "crane_runway_case_with_material_and_presets.json"
    case = load_crane_runway_case_json(path)
    assert validate_crane_runway_case_dict(case, strict=True).valid
    result = run_crane_runway_case_json(path)
    assert "serviceability_passed" in result.summary_dict
    assert "stress_criteria_passed" in result.summary_dict
