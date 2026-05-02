from __future__ import annotations

import argparse
import json
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print concise local UI beta status and onboarding commands.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON payload.")
    parser.add_argument("--check-files", action="store_true", help="Check required docs/scripts exist.")
    parser.add_argument("--quiet", action="store_true", help="Print only essential commands.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    payload = {
        "app": "App Viga Carrilera",
        "module": "Crane Runway Local UI",
        "beta_status": "Internal beta",
        "schema_version": "1.0",
        "commands": {
            "launch_ui": "PYTHONPATH=src python scripts/launch_crane_runway_ui.py",
            "health_check": "PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest",
            "rc_check": "PYTHONPATH=src python scripts/run_local_ui_rc_check.py --skip-archive",
            "create_demo_project": "PYTHONPATH=src python scripts/create_local_ui_demo_project.py --overwrite --run",
        },
        "docs": [
            "docs/getting_started_crane_runway.md",
            "docs/crane_runway_local_web_ui.md",
            "docs/local_ui_beta_onboarding.md",
            "docs/local_ui_beta_manual_qa_checklist.md",
            "docs/local_ui_beta_known_issues.md",
            "docs/local_ui_beta_rc_release_notes.md",
        ],
        "limitations": [
            "no official CIRSOC/CISC/AISC checks",
            "no fatigue checks",
            "no torsional/warping stress checks",
            "no LTB checks",
            "sample data requires independent verification",
            "engineering review required",
        ],
    }

    required_paths = [
        "scripts/launch_crane_runway_ui.py",
        "scripts/run_beta_health_check.py",
        "scripts/run_local_ui_rc_check.py",
        "scripts/create_local_ui_demo_project.py",
        *payload["docs"],
    ]

    if args.check_files:
        missing = [p for p in required_paths if not Path(p).exists()]
        if missing:
            print("Missing required files:")
            for item in missing:
                print(f"- {item}")
            return 1

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    if args.quiet:
        print(payload["commands"]["launch_ui"])
        print(payload["commands"]["health_check"])
        print(payload["commands"]["create_demo_project"])
        return 0

    print("LOCAL UI BETA INFO\n")
    print(f"App: {payload['app']}")
    print(f"Module: {payload['module']}")
    print(f"Beta status: {payload['beta_status']}")
    print(f"Schema version: {payload['schema_version']}\n")
    print("Important commands:")
    print(f"- Launch UI:\n  {payload['commands']['launch_ui']}")
    print(f"- Health check:\n  {payload['commands']['health_check']}")
    print(f"- RC check:\n  {payload['commands']['rc_check']}")
    print(f"- Create demo project:\n  {payload['commands']['create_demo_project']}\n")
    print("Important docs:")
    for item in payload["docs"]:
        print(f"- {item}")
    print("\nLimitations:")
    for item in payload["limitations"]:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
