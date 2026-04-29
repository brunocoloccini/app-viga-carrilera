from __future__ import annotations

import argparse
import json
from pathlib import Path

from section_core.crane_runway import CraneRunwayCaseErrorFormatter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate crane runway JSON case files and print user-facing validation results."
    )
    parser.add_argument("paths", nargs="+", help="One or more crane runway case JSON file paths.")
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Run schema validation in non-strict mode (allows known compatibility warnings).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output instead of text.",
    )
    return parser


def _report_for_path(path: str, strict: bool) -> dict[str, object]:
    report = CraneRunwayCaseErrorFormatter.validate_case_json_for_user(path, strict=strict)
    return {"path": path, "valid": report.valid, "messages": report.to_dict()["messages"]}


def _print_text_report(payload: dict[str, object]) -> None:
    path = str(payload["path"])
    valid = bool(payload["valid"])
    print(f"VALID: {path}" if valid else f"INVALID: {path}")
    for msg in payload["messages"]:
        severity = str(msg["severity"]).upper()
        print(f"{severity} {msg['path']}: {msg['message']}")
        if msg.get("hint"):
            print(f"Hint: {msg['hint']}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    strict = not args.non_strict
    reports = [_report_for_path(path, strict=strict) for path in args.paths]

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for idx, payload in enumerate(reports):
            if idx > 0:
                print()
            _print_text_report(payload)

    return 0 if all(bool(payload["valid"]) for payload in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
