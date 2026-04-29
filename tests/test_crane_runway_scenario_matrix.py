from __future__ import annotations

from pathlib import Path

from section_core.crane_runway import (
    assert_valid_crane_runway_case_dict,
    load_crane_runway_case_json,
    run_crane_runway_case_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = REPO_ROOT / "examples" / "cases"

EXPECTED_STATUS = {
    "crane_runway_case_with_cover_and_eccentricity": {
        "serviceability_passed": False,
        "stress_criteria_passed": False,
        "overall_passed": False,
        "has_torsional_input": True,
    },
    "crane_runway_case_without_cover_plate": {
        "serviceability_passed": False,
        "stress_criteria_passed": False,
        "overall_passed": False,
        "has_torsional_input": True,
    },
    "crane_runway_case_without_rail_eccentricity": {
        "serviceability_passed": False,
        "stress_criteria_passed": False,
        "overall_passed": False,
        "has_torsional_input": False,
    },
    "crane_runway_case_deflection_fail": {
        "serviceability_passed": False,
        "stress_criteria_passed": False,
        "overall_passed": False,
        "has_torsional_input": True,
    },
    "crane_runway_case_stress_fail": {
        "serviceability_passed": False,
        "stress_criteria_passed": False,
        "overall_passed": False,
        "has_torsional_input": True,
    },
}


def _case_paths() -> list[Path]:
    return sorted(CASES_DIR.glob("*.json"))


def test_scenario_matrix_cases_validate_and_run():
    paths = _case_paths()
    assert len(paths) >= 5

    for path in paths:
        data = load_crane_runway_case_json(path)
        assert data.get("schema_version") == "1.0"
        assert_valid_crane_runway_case_dict(data, strict=True)

        result = run_crane_runway_case_json(path)
        summary = result.workflow_result.summary

        assert result.case_id
        assert summary is not None
        assert summary.max_vertical_moment_Nmm() > 0
        assert summary.max_vertical_shear_abs_N() > 0
        assert summary.max_vertical_deflection_mm() > 0
        assert summary.max_biaxial_stress_MPa() > 0
        assert "Crane Runway Demand Summary" in result.text_report
        assert "# Crane Runway Demand Summary" in result.markdown_report
        assert "overall_passed" in summary.to_dict()


def test_scenario_matrix_specific_expectations():
    for case_stem, expected in EXPECTED_STATUS.items():
        result = run_crane_runway_case_json(CASES_DIR / f"{case_stem}.json")
        summary = result.workflow_result.summary

        assert summary.serviceability_passed() is expected["serviceability_passed"]
        assert summary.stress_criteria_passed() is expected["stress_criteria_passed"]
        assert summary.overall_passed() is expected["overall_passed"]

        has_torsion = summary.max_torsional_input_Nmm() is not None
        assert has_torsion is expected["has_torsional_input"]

        summary_dict = summary.to_dict()
        if expected["has_torsional_input"]:
            assert summary.max_torsional_input_Nmm() > 0
        else:
            assert summary.max_torsional_input_Nmm() is None
            assert summary_dict["max_torsional_input_Nmm"] is None
            assert "N/A" in result.text_report
            assert "N/A" in result.markdown_report

        if "deflection_fail" in case_stem or "stress_fail" in case_stem:
            assert "FAIL" in result.text_report
            assert "FAIL" in result.markdown_report


def test_without_cover_plate_variant_runs_with_expected_demands():
    result = run_crane_runway_case_json(CASES_DIR / "crane_runway_case_without_cover_plate.json")
    summary = result.workflow_result.summary
    assert summary.section_id
    assert summary.max_vertical_moment_Nmm() > 0
    assert summary.max_biaxial_stress_MPa() > 0
