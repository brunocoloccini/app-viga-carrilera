"""Update crane runway golden regression outputs for the demo case.

WARNING:
Golden outputs are regression baselines and should only be updated after
intentional calculation/reporting changes are reviewed.
"""

from __future__ import annotations

import json
from pathlib import Path

from section_core.crane_runway import CraneRunwayDemandSummaryHtmlFormatter, run_crane_runway_case_json


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = REPO_ROOT / "examples" / "crane_runway_case_demo.json"
GOLDEN_SUMMARY_PATH = REPO_ROOT / "examples" / "golden" / "crane_runway_case_demo_golden_summary.json"
GOLDEN_REPORT_PATH = REPO_ROOT / "examples" / "golden" / "crane_runway_case_demo_golden_report.md"
GOLDEN_HTML_PATH = REPO_ROOT / "examples" / "golden" / "crane_runway_case_demo_golden_report.html"


def _build_golden_summary(summary_dict: dict) -> dict:
    out = dict(summary_dict)
    out["schema_version"] = "1.0"
    out["source_case_path"] = "examples/crane_runway_case_demo.json"
    metadata = dict(out.get("metadata", {}))
    metadata["generated_by"] = "V1-038 golden regression baseline"
    metadata["notes"] = [
        "This is a regression baseline, not an independent engineering verification.",
        "Update only when intentional calculation changes are reviewed.",
    ]
    out["metadata"] = metadata
    return out


def main() -> None:
    result = run_crane_runway_case_json(CASE_PATH)
    golden_summary = _build_golden_summary(result.summary_dict)

    GOLDEN_SUMMARY_PATH.write_text(json.dumps(golden_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    GOLDEN_REPORT_PATH.write_text(result.markdown_report, encoding="utf-8")

    html_report = CraneRunwayDemandSummaryHtmlFormatter().format_html(result.workflow_result.summary)
    GOLDEN_HTML_PATH.write_text(html_report + "\n", encoding="utf-8")

    print(f"Updated: {GOLDEN_SUMMARY_PATH.relative_to(REPO_ROOT)}")
    print(f"Updated: {GOLDEN_REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"Updated: {GOLDEN_HTML_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
