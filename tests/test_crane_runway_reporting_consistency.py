from pathlib import Path

from section_core import (
    CraneRunwayDemandSummary,
    CraneRunwayDemandSummaryFormatter,
    CraneRunwayDemandSummaryHtmlFormatter,
    run_crane_runway_case_json,
)

CASE_PATH = Path(__file__).resolve().parents[1] / "examples" / "cases" / "crane_runway_case_with_material_and_presets.json"


def test_text_markdown_html_include_core_contract_content():
    result = run_crane_runway_case_json(CASE_PATH)
    summary = result.workflow_result.summary
    html = CraneRunwayDemandSummaryHtmlFormatter().format_html(summary)

    for content in [
        "Crane Runway Demand Summary",
        "serviceability",
        "stress",
        "overall",
    ]:
        assert content.lower() in result.text_report.lower()
        assert content.lower() in result.markdown_report.lower()
        assert content.lower() in html.lower()

    assert (summary.load_model_id and summary.load_model_id in result.text_report) or (
        summary.summary_id in result.text_report
    )


def test_missing_values_render_na_in_all_formats():
    summary = CraneRunwayDemandSummary(summary_id="MIN", span_internal_mm=1000)
    text = CraneRunwayDemandSummaryFormatter().format_text(summary)
    md = CraneRunwayDemandSummaryFormatter().format_markdown(summary)
    html = CraneRunwayDemandSummaryHtmlFormatter().format_html(summary)

    assert "N/A" in text
    assert "N/A" in md
    assert "N/A" in html


def test_warnings_and_escape_consistency():
    warning = 'warn <unsafe> & "quoted"'
    summary = CraneRunwayDemandSummary(summary_id="WARN", span_internal_mm=1000, warnings=[warning])
    text = CraneRunwayDemandSummaryFormatter().format_text(summary)
    md = CraneRunwayDemandSummaryFormatter().format_markdown(summary)
    html = CraneRunwayDemandSummaryHtmlFormatter().format_html(summary)

    assert warning in text
    assert warning in md
    assert "&lt;unsafe&gt;" in html and "&amp;" in html


def test_status_mapping_pass_fail_na_in_all_formats():
    fmt = CraneRunwayDemandSummaryFormatter()
    hfmt = CraneRunwayDemandSummaryHtmlFormatter()

    pass_summary = CraneRunwayDemandSummary(
        summary_id="PASS", span_internal_mm=1000, serviceability_results=[type("X", (), {"passed": True})()], stress_utilization_results=[type("X", (), {"passed": True})()]
    )
    fail_summary = CraneRunwayDemandSummary(summary_id="FAIL", span_internal_mm=1000, serviceability_results=[type("X", (), {"passed": False})()])
    na_summary = CraneRunwayDemandSummary(summary_id="NA", span_internal_mm=1000)

    for expected, summary in [("PASS", pass_summary), ("FAIL", fail_summary), ("N/A", na_summary)]:
        assert f"overall status: {expected}" in fmt.format_text(summary)
        assert f"| Overall | {expected} |" in fmt.format_markdown(summary)
        assert expected in hfmt.format_html(summary)
