from pathlib import Path

from section_core import CraneRunwayDemandSummaryHtmlFormatter, run_crane_runway_case_json


CASE_PATH = Path(__file__).resolve().parents[1] / "examples" / "cases" / "crane_runway_case_with_material_and_presets.json"


def test_workflow_case_contract_and_summary_metrics():
    result = run_crane_runway_case_json(CASE_PATH)
    assert result.workflow_result is not None
    assert result.workflow_result.summary is not None

    summary = result.workflow_result.summary
    as_dict = summary.to_dict()

    assert isinstance(as_dict, dict)
    assert result.text_report.strip()
    assert result.markdown_report.strip()

    assert summary.max_vertical_moment_Nmm() > 0
    assert summary.max_vertical_shear_abs_N() > 0
    assert summary.max_vertical_deflection_mm() > 0
    assert summary.max_biaxial_stress_MPa() > 0


def test_summary_getters_match_to_dict_and_status_flags():
    summary = run_crane_runway_case_json(CASE_PATH).workflow_result.summary
    as_dict = summary.to_dict()

    for key in [
        "max_vertical_moment_Nmm",
        "max_vertical_shear_abs_N",
        "max_vertical_deflection_mm",
        "max_lateral_moment_Nmm",
        "max_biaxial_stress_MPa",
        "max_torsional_input_Nmm",
    ]:
        assert as_dict[key] == getattr(summary, key)()

    assert as_dict["serviceability_passed"] == summary.serviceability_passed()
    assert as_dict["stress_criteria_passed"] == summary.stress_criteria_passed()
    assert as_dict["overall_passed"] == summary.overall_passed()


def test_metadata_warning_and_determinism_contract():
    result_1 = run_crane_runway_case_json(CASE_PATH)
    result_2 = run_crane_runway_case_json(CASE_PATH)

    summary_1 = result_1.workflow_result.summary
    summary_2 = result_2.workflow_result.summary

    as_dict_1 = summary_1.to_dict()
    assert isinstance(summary_1.warnings, list)
    assert as_dict_1["warnings"] == summary_1.warnings

    material_meta = result_1.workflow_result.metadata.get("material")
    if material_meta is not None:
        assert "material_id" in material_meta
        assert "Fy_internal_MPa" in material_meta

    source_warnings = CASE_PATH.read_text(encoding="utf-8")
    if "no CIRSOC design-code checks are performed" in source_warnings:
        assert any("no CIRSOC design-code checks are performed" in warning for warning in summary_1.warnings)

    assert summary_1.to_dict() == summary_2.to_dict()
    assert result_1.markdown_report == result_2.markdown_report

    html_formatter = CraneRunwayDemandSummaryHtmlFormatter()
    assert html_formatter.format_html(summary_1) == html_formatter.format_html(summary_2)
