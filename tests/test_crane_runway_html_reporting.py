from __future__ import annotations

from section_core.crane_runway import (
    CraneRunwayDemandSummary,
    CraneRunwayDemandSummaryBuilder,
    CraneRunwayDemandSummaryHtmlFormatter,
    CraneRunwayHtmlReport,
    InvalidHtmlReportSummaryError,
    run_crane_runway_case_json,
)


def test_basic_html_formatter_output() -> None:
    summary = CraneRunwayDemandSummary(summary_id="R1", span_internal_mm=10_000)
    html = CraneRunwayDemandSummaryHtmlFormatter().format_html(summary)
    assert isinstance(html, str)
    assert "<!doctype html>" in html
    assert "<h1>Crane Runway Demand Summary</h1>" in html
    assert "R1" in html
    assert "<h2>Demands</h2>" in html
    assert "<h2>Checks</h2>" in html


def test_missing_values_render_na() -> None:
    summary = CraneRunwayDemandSummaryBuilder.build_basic_summary(summary_id="R2", span_internal_mm=10_000)
    html = CraneRunwayDemandSummaryHtmlFormatter().format_html(summary)
    assert "N/A" in html


def test_status_rendering_pass_fail_na() -> None:
    fmt = CraneRunwayDemandSummaryHtmlFormatter()
    pass_summary = CraneRunwayDemandSummary(
        summary_id="PASS",
        span_internal_mm=1000,
        serviceability_results=[type("R", (), {"passed": True})()],
        stress_utilization_results=[type("R", (), {"passed": True})()],
    )
    fail_summary = CraneRunwayDemandSummary(
        summary_id="FAIL", span_internal_mm=1000, serviceability_results=[type("R", (), {"passed": False})()]
    )
    na_summary = CraneRunwayDemandSummary(summary_id="NA", span_internal_mm=1000)

    assert "PASS" in fmt.format_html(pass_summary)
    assert "FAIL" in fmt.format_html(fail_summary)
    assert "N/A" in fmt.format_html(na_summary)


def test_warnings_and_escaping() -> None:
    fmt = CraneRunwayDemandSummaryHtmlFormatter()
    summary = CraneRunwayDemandSummary(summary_id="<script>x</script>", span_internal_mm=1000, warnings=["<script>w</script>"])
    html = fmt.format_html(summary)
    assert "&lt;script&gt;x&lt;/script&gt;" in html
    assert "&lt;script&gt;w&lt;/script&gt;" in html
    assert "<script>" not in html

    no_warning_html = fmt.format_html(CraneRunwayDemandSummary(summary_id="NW", span_internal_mm=1000))
    assert "<li>None</li>" in no_warning_html


def test_build_report() -> None:
    summary = CraneRunwayDemandSummary(summary_id="B1", span_internal_mm=1000)
    report = CraneRunwayDemandSummaryHtmlFormatter().build_report(summary)
    assert isinstance(report, CraneRunwayHtmlReport)
    assert "<!doctype html>" in report.html


def test_integration_from_demo_case() -> None:
    result = run_crane_runway_case_json("examples/crane_runway_case_demo.json")
    html = CraneRunwayDemandSummaryHtmlFormatter().format_html(result.workflow_result.summary)
    assert "Crane Runway Demand Summary" in html
    assert "demo_crane" in html
    assert "Demands" in html
    assert "Checks" in html
    assert "Warnings" in html


def test_validation_errors() -> None:
    fmt = CraneRunwayDemandSummaryHtmlFormatter()
    try:
        fmt.format_html(None)
        raise AssertionError("expected error")
    except InvalidHtmlReportSummaryError:
        pass
