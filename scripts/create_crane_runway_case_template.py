from __future__ import annotations

import argparse

from section_core.crane_runway import (
    CaseTemplateError,
    CaseTemplateNotFoundError,
    list_crane_runway_case_template_ids,
    write_crane_runway_case_template,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create crane runway JSON case files from built-in templates.")
    parser.add_argument("--list", action="store_true", help="List available template IDs.")
    parser.add_argument("--template", help="Template ID to render.")
    parser.add_argument("--output", help="Output JSON file path.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list:
        for tid in list_crane_runway_case_template_ids():
            print(tid)
        return 0

    if not args.template or not args.output:
        parser.error("--template and --output are required unless --list is used.")

    try:
        out = write_crane_runway_case_template(args.template, args.output, overwrite=args.overwrite)
    except CaseTemplateNotFoundError as exc:
        print(str(exc))
        return 1
    except CaseTemplateError as exc:
        print(str(exc))
        return 1

    print(f"WROTE: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
