from __future__ import annotations

from pathlib import Path

from section_core.crane_runway import (
    CraneRunwayMatrixCaseRow,
    CraneRunwayMatrixHtmlFormatter,
    run_crane_runway_case_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = REPO_ROOT / "examples" / "cases"


def test_matrix_formatter_basics_and_escaping():
    formatter = CraneRunwayMatrixHtmlFormatter()
    rows = [
        CraneRunwayMatrixCaseRow(
            case_id="ok_case",
            case_path="examples/cases/ok.json",
            max_vertical_moment_Nmm=2_000_000.0,
            max_vertical_shear_abs_N=2_500.0,
            max_vertical_deflection_mm=10.1234,
            max_biaxial_stress_MPa=123.4567,
            max_torsional_input_Nmm=3_000_000.0,
            serviceability_passed=True,
            stress_criteria_passed=False,
            overall_passed=None,
            warnings=["warn <script>alert(1)</script>"],
        ),
        CraneRunwayMatrixCaseRow(case_id="<script>case</script>"),
    ]

    html = formatter.format_html(rows, title="Crane Runway Scenario Matrix")
    assert "<!doctype html>" in html
    assert "<h1>Crane Runway Scenario Matrix</h1>" in html
    assert "ok_case" in html
    assert "2.000 kN·m" in html
    assert "2.500 kN" in html
    assert "10.123 mm" in html
    assert "123.457 MPa" in html
    assert "3.000 kN·m" in html
    assert "PASS" in html and "FAIL" in html and "N/A" in html
    assert "N/A" in html
    assert "warn" in html
    assert "<script>" not in html
    assert "&lt;script&gt;case&lt;/script&gt;" in html


def test_matrix_formatter_integration_with_case_matrix():
    formatter = CraneRunwayMatrixHtmlFormatter()
    paths = sorted(CASES_DIR.glob("*.json"))
    rows = []
    for path in paths:
        result = run_crane_runway_case_json(path)
        rows.append(formatter.row_from_case_result(result, case_path=str(path)))

    html = formatter.build_report(rows).html
    for path in paths:
        assert path.stem in html
    assert "PASS" in html or "FAIL" in html
    assert "<script>" not in html
