from __future__ import annotations

import argparse
import json
from pathlib import Path

from section_core.crane_runway import (
    CraneRunwayCaseErrorFormatter,
    CraneRunwayDemandSummaryHtmlFormatter,
    CraneRunwayReportPackageWriter,
    run_crane_runway_case_json,
)


_SEPARATOR = "\n\n---\n\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute a crane runway JSON case file and print text/markdown/HTML/JSON reports."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", action="store_true", help="Print text report (default).")
    group.add_argument("--markdown", action="store_true", help="Print markdown report.")
    group.add_argument("--both", action="store_true", help="Print text and markdown reports.")
    group.add_argument("--summary-json", action="store_true", help="Print summary.to_dict() as JSON.")
    group.add_argument("--html", action="store_true", help="Print HTML report.")
    parser.add_argument("--output", help="Write selected output to file instead of stdout.")
    parser.add_argument("--package-output", help="Write a deterministic report package folder to DIR.")
    parser.add_argument("--overwrite-package", action="store_true", help="Allow overwriting known package files in non-empty package directory.")
    parser.add_argument("path", help="Crane runway JSON case file path.")
    return parser


def _render_output(
    args: argparse.Namespace,
    result_text: str,
    result_markdown: str,
    result_html: str,
    summary_dict: dict[str, object],
) -> str:
    if args.markdown:
        return result_markdown
    if args.both:
        return f"{result_text}{_SEPARATOR}{result_markdown}"
    if args.summary_json:
        return json.dumps(summary_dict, indent=2)
    if args.html:
        return result_html
    return result_text


def _print_user_error(exc: Exception) -> None:
    report = CraneRunwayCaseErrorFormatter.from_exception(exc)
    print(report.to_text())


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_crane_runway_case_json(args.path)
        result_html = CraneRunwayDemandSummaryHtmlFormatter().format_html(result.workflow_result.summary)
        output = _render_output(args, result.text_report, result.markdown_report, result_html, result.summary_dict)
    except Exception as exc:
        _print_user_error(exc)
        return 1

    if args.package_output:
        try:
            writer = CraneRunwayReportPackageWriter()
            writer.write_case_result_package(
                args.path,
                result,
                CraneRunwayCaseErrorFormatter.validate_case_json_for_user(args.path),
                args.package_output,
                overwrite=args.overwrite_package,
            )
        except Exception as exc:
            _print_user_error(exc)
            return 1
        print(f"PACKAGE WROTE: {args.package_output}")

    if args.output:
        try:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output + "\n", encoding="utf-8")
        except Exception as exc:
            _print_user_error(exc)
            return 1
        print(f"WROTE: {output_path}")
        return 0

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
