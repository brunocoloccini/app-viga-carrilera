from __future__ import annotations

import json
import math
from pathlib import Path

from section_core.crane_runway import run_crane_runway_case_json


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = REPO_ROOT / "examples" / "crane_runway_case_demo.json"
GOLDEN_SUMMARY_PATH = REPO_ROOT / "examples" / "golden" / "crane_runway_case_demo_golden_summary.json"
GOLDEN_REPORT_PATH = REPO_ROOT / "examples" / "golden" / "crane_runway_case_demo_golden_report.md"


NUMERIC_KEYS = (
    "span_internal_mm",
    "max_vertical_moment_Nmm",
    "max_vertical_shear_abs_N",
    "max_vertical_deflection_mm",
    "max_lateral_moment_Nmm",
    "max_biaxial_stress_MPa",
    "max_torsional_input_Nmm",
)


def _normalized_markdown(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip() + "\n"


def test_golden_files_exist():
    assert GOLDEN_SUMMARY_PATH.exists(), f"Missing golden summary JSON: {GOLDEN_SUMMARY_PATH}"
    assert GOLDEN_REPORT_PATH.exists(), f"Missing golden report markdown: {GOLDEN_REPORT_PATH}"


def test_demo_case_summary_matches_golden_regression():
    actual = run_crane_runway_case_json(CASE_PATH).summary_dict
    golden = json.loads(GOLDEN_SUMMARY_PATH.read_text(encoding="utf-8"))

    for key in NUMERIC_KEYS:
        assert key in actual, f"Missing numeric key in actual summary: {key}"
        assert key in golden, f"Missing numeric key in golden summary: {key}"
        assert math.isclose(actual[key], golden[key], rel_tol=1e-6, abs_tol=1e-6), (
            f"Regression mismatch for {key}: actual={actual[key]!r}, expected={golden[key]!r}"
        )

    for key in ("serviceability_passed", "stress_criteria_passed", "overall_passed"):
        assert actual.get(key) == golden.get(key), (
            f"Regression mismatch for {key}: actual={actual.get(key)!r}, expected={golden.get(key)!r}"
        )

    for key in ("summary_id", "section_id", "load_model_id"):
        assert actual.get(key) == golden.get(key), (
            f"Regression mismatch for {key}: actual={actual.get(key)!r}, expected={golden.get(key)!r}"
        )

    assert actual.get("warnings") == golden.get("warnings"), (
        f"Regression mismatch for warnings: actual={actual.get('warnings')!r}, expected={golden.get('warnings')!r}"
    )


def test_demo_case_markdown_report_matches_golden_regression():
    actual_report = run_crane_runway_case_json(CASE_PATH).markdown_report
    golden_report = GOLDEN_REPORT_PATH.read_text(encoding="utf-8")
    assert _normalized_markdown(actual_report) == _normalized_markdown(golden_report)


def test_golden_summary_has_required_metadata():
    golden = json.loads(GOLDEN_SUMMARY_PATH.read_text(encoding="utf-8"))
    assert golden.get("schema_version") == "1.0"
    assert golden.get("source_case_path") == "examples/crane_runway_case_demo.json"
    metadata = golden.get("metadata", {})
    assert metadata.get("generated_by") == "V1-038 golden regression baseline"
