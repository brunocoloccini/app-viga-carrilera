from __future__ import annotations

import argparse
import sys
from pathlib import Path

from section_core.crane_runway import (
    CraneRunwayMatrixHtmlFormatter,
    assert_valid_crane_runway_case_dict,
    load_crane_runway_case_json,
    run_crane_runway_case_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run crane runway scenario matrix cases.")
    parser.add_argument("--html", action="store_true", help="Print HTML matrix report.")
    parser.add_argument("--output", type=Path, help="Output file path for HTML report (requires --html).")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cases_dir = repo_root / "examples" / "cases"
    case_paths = sorted(cases_dir.glob("*.json"))
    if not case_paths:
        print(f"No case files found under {cases_dir}", file=sys.stderr)
        return 1

    results = []
    for path in case_paths:
        try:
            data = load_crane_runway_case_json(path)
            assert_valid_crane_runway_case_dict(data, strict=True)
            results.append(run_crane_runway_case_json(path))
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {path.name}: {exc}", file=sys.stderr)
            return 2

    if args.html:
        formatter = CraneRunwayMatrixHtmlFormatter()
        rows = [formatter.row_from_case_result(result, case_path=str(path)) for result, path in zip(results, case_paths)]
        html = formatter.format_html(rows)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(html, encoding="utf-8")
            print(f"WROTE: {args.output}")
        else:
            print(html)
        return 0

    for result in results:
        s = result.workflow_result.summary
        print(
            f"{result.case_id}: "
            f"Mmax={s.max_vertical_moment_Nmm():.3f} N·mm, "
            f"dmax={s.max_vertical_deflection_mm():.3f} mm, "
            f"sigma_bi,max={s.max_biaxial_stress_MPa():.3f} MPa, "
            f"serviceability={s.serviceability_passed()}, "
            f"stress={s.stress_criteria_passed()}, "
            f"overall={s.overall_passed()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
