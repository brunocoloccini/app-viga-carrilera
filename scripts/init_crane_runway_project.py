from __future__ import annotations

import argparse
import re
from pathlib import Path

from section_core.crane_runway import (
    CaseTemplateError,
    CaseTemplateNotFoundError,
    CraneRunwayCaseErrorFormatter,
    CraneRunwayDemandSummaryHtmlFormatter,
    CraneRunwayReportPackageWriter,
    run_crane_runway_case_json,
    write_crane_runway_case_template,
)

_PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a crane runway project workspace from a built-in template.")
    parser.add_argument("--name", required=True, help="Project name (letters, numbers, dash, underscore).")
    parser.add_argument("--template", required=True, help="Built-in template ID.")
    parser.add_argument("--root", default="projects", help="Root directory for project workspaces.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting known generated files in existing projects.")
    parser.add_argument("--validate", action="store_true", help="Validate generated input_case.json after initialization.")
    parser.add_argument("--run", action="store_true", help="Run generated case and write package to outputs/ (implies --validate).")
    return parser


def _validate_project_name(name: str) -> str | None:
    if not name:
        return "Project name cannot be empty."
    if ".." in name:
        return "Project name cannot contain '..'."
    if "/" in name or "\\" in name:
        return "Project name cannot contain path separators."
    if " " in name:
        return "Project name cannot contain spaces."
    if not _PROJECT_NAME_RE.fullmatch(name):
        return "Project name may only include letters, numbers, dash, and underscore."
    return None


def _project_readme(project_name: str, template_id: str, project_path: Path) -> str:
    rel = project_path.as_posix()
    return (
        f"# Crane Runway Project: {project_name}\n\n"
        f"Template: `{template_id}`\n\n"
        "## Commands\n\n"
        "Validate case:\n\n"
        f"`PYTHONPATH=src python scripts/validate_crane_runway_case.py {rel}/input_case.json`\n\n"
        "Run HTML report:\n\n"
        f"`PYTHONPATH=src python scripts/run_crane_runway_case.py {rel}/input_case.json --html --output {rel}/outputs/report.html`\n\n"
        "Generate report package:\n\n"
        f"`PYTHONPATH=src python scripts/run_crane_runway_case.py {rel}/input_case.json --package-output {rel}/outputs --overwrite-package`\n\n"
        "## Warnings\n\n"
        "- Sample data requires independent verification before design use.\n"
        "- Current checks are generic and are not official CIRSOC/CISC/AISC compliance checks.\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    name_error = _validate_project_name(args.name)
    if name_error:
        print(name_error)
        return 1

    root = Path(args.root)
    project_dir = root / args.name
    case_path = project_dir / "input_case.json"
    readme_path = project_dir / "README.md"
    outputs_dir = project_dir / "outputs"

    if project_dir.exists() and any(project_dir.iterdir()) and not args.overwrite:
        print(f"Project directory already exists and is non-empty: {project_dir}")
        return 1

    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        write_crane_runway_case_template(args.template, case_path, overwrite=args.overwrite)
        readme_path.write_text(_project_readme(args.name, args.template, project_dir), encoding="utf-8")
    except (CaseTemplateNotFoundError, CaseTemplateError) as exc:
        print(str(exc))
        return 1

    print(f"CREATED: {project_dir}")

    should_validate = args.validate or args.run
    if should_validate:
        report = CraneRunwayCaseErrorFormatter.validate_case_json_for_user(str(case_path))
        if not report.valid:
            print(report.to_text())
            return 1
        print(f"VALID: {case_path}")

    if args.run:
        try:
            result = run_crane_runway_case_json(str(case_path))
            writer = CraneRunwayReportPackageWriter()
            writer.write_case_result_package(
                str(case_path),
                result,
                CraneRunwayCaseErrorFormatter.validate_case_json_for_user(str(case_path)),
                str(outputs_dir),
                overwrite=True,
            )
            html = CraneRunwayDemandSummaryHtmlFormatter().format_html(result.workflow_result.summary)
            (outputs_dir / "report.html").write_text(html + "\n", encoding="utf-8")
        except Exception as exc:
            print(CraneRunwayCaseErrorFormatter.from_exception(exc).to_text())
            return 1
        print(f"PACKAGE WROTE: {outputs_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
