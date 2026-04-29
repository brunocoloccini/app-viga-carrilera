from __future__ import annotations

import sys
from pathlib import Path

from section_core.crane_runway import (
    assert_valid_crane_runway_case_dict,
    load_crane_runway_case_json,
    run_crane_runway_case_json,
)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cases_dir = repo_root / "examples" / "cases"
    case_paths = sorted(cases_dir.glob("*.json"))
    if not case_paths:
        print(f"No case files found under {cases_dir}", file=sys.stderr)
        return 1

    for path in case_paths:
        try:
            data = load_crane_runway_case_json(path)
            assert_valid_crane_runway_case_dict(data, strict=True)
            result = run_crane_runway_case_json(path)
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
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {path.name}: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
