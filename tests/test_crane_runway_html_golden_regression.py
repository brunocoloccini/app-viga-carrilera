from __future__ import annotations

import os
import subprocess
from pathlib import Path

from section_core.crane_runway import CraneRunwayDemandSummaryHtmlFormatter, run_crane_runway_case_json


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = REPO_ROOT / "examples" / "crane_runway_case_demo.json"
GOLDEN_HTML_PATH = REPO_ROOT / "examples" / "golden" / "crane_runway_case_demo_golden_report.html"


def _normalized_html(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip() + "\n"


def test_golden_html_file_exists():
    assert GOLDEN_HTML_PATH.exists(), f"Missing golden HTML report: {GOLDEN_HTML_PATH}"


def test_demo_case_html_matches_golden_regression():
    result = run_crane_runway_case_json(CASE_PATH)
    actual_html = CraneRunwayDemandSummaryHtmlFormatter().format_html(result.workflow_result.summary)
    golden_html = GOLDEN_HTML_PATH.read_text(encoding="utf-8")
    assert _normalized_html(actual_html) == _normalized_html(golden_html)


def test_golden_html_structure_sanity():
    golden_html = _normalized_html(GOLDEN_HTML_PATH.read_text(encoding="utf-8"))
    assert "<!doctype html>" in golden_html
    assert "<h1>Crane Runway Demand Summary</h1>" in golden_html
    assert "Identification" in golden_html
    assert ("Demand Summary" in golden_html) or ("Demands" in golden_html)
    assert ("Check Summary" in golden_html) or ("Checks" in golden_html)
    assert "Warnings" in golden_html


def test_cli_html_stdout_matches_golden_regression():
    completed = subprocess.run(
        [
            "python",
            "scripts/run_crane_runway_case.py",
            "examples/crane_runway_case_demo.json",
            "--html",
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )
    golden_html = GOLDEN_HTML_PATH.read_text(encoding="utf-8")
    assert _normalized_html(completed.stdout) == _normalized_html(golden_html)


def test_cli_html_output_file_matches_golden_regression(tmp_path: Path):
    output_path = tmp_path / "report.html"
    subprocess.run(
        [
            "python",
            "scripts/run_crane_runway_case.py",
            "examples/crane_runway_case_demo.json",
            "--html",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )
    golden_html = GOLDEN_HTML_PATH.read_text(encoding="utf-8")
    assert _normalized_html(output_path.read_text(encoding="utf-8")) == _normalized_html(golden_html)
