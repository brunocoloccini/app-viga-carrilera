from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from section_core.crane_runway import CaseTemplateError, CaseTemplateNotFoundError, write_crane_runway_case_template


PROJECT_NAME_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def _validate_project_name(name: str) -> str | None:
    if not name:
        return "Project name cannot be empty."
    if ".." in name:
        return "Project name cannot contain '..'."
    if "/" in name or "\\" in name:
        return "Project name cannot contain path separators."
    if " " in name:
        return "Project name cannot contain spaces."
    if any(char not in PROJECT_NAME_ALLOWED for char in name):
        return "Project name may only include letters, numbers, dash, and underscore."
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a ready-to-open local UI demo project.")
    parser.add_argument("--project-name", default="demo_local_ui_beta", help="Project name (letters, numbers, dash, underscore).")
    parser.add_argument("--template", default="ipn-with-cover", help="Built-in template ID.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing generated files in an existing project.")
    parser.add_argument("--run", action="store_true", help="Run the generated case and write package outputs.")
    parser.add_argument("--projects-root", default="projects", help="Projects workspace root path.")
    parser.add_argument("--quiet", action="store_true", help="Print only essential output.")
    return parser


def _project_readme(project_name: str, template_id: str) -> str:
    rel = f"projects/{project_name}"
    return f"""# Local UI Demo Project: {project_name}

Template: `{template_id}`

> ⚠️ This is a demo project for onboarding and UI evaluation only.

## Start the Local UI

`PYTHONPATH=src python scripts/launch_crane_runway_ui.py`

## Run directly from CLI

`PYTHONPATH=src python scripts/run_crane_runway_case.py {rel}/input_case.json --package-output {rel}/outputs --overwrite-package`

## Expected UI workflow

1. Open **Project Workspace**.
2. Refresh project list.
3. Open project: `{project_name}`.
4. Validate.
5. Run project.
6. Inspect HTML report.

## Limitations

- Sample data must be independently verified.
- Generic checks only.
- No official CIRSOC/CISC/AISC checks.
- No fatigue/torsion/warping/LTB checks.
- Engineering review required.
"""


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    err = _validate_project_name(args.project_name)
    if err:
        print(err)
        return 1

    project_dir = Path(args.projects_root) / args.project_name
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
        readme_path.write_text(_project_readme(args.project_name, args.template), encoding="utf-8")
    except (CaseTemplateNotFoundError, CaseTemplateError) as exc:
        print(str(exc))
        return 1

    if args.run:
        cmd = [
            sys.executable,
            "scripts/run_crane_runway_case.py",
            str(case_path),
            "--package-output",
            str(outputs_dir),
            "--overwrite-package",
            "--output",
            str(outputs_dir / "report.html"),
            "--html",
        ]
        env = dict(**__import__("os").environ)
        env["PYTHONPATH"] = "src"
        completed = subprocess.run(cmd, capture_output=args.quiet, text=True, env=env)
        if completed.returncode != 0:
            if completed.stdout:
                print(completed.stdout.rstrip())
            if completed.stderr:
                print(completed.stderr.rstrip())
            return 1

    if not args.quiet:
        print("LOCAL UI DEMO PROJECT\n")
        print(f"Project: {args.project_name}")
        print(f"Template: {args.template}")
        print(f"Created: {project_dir}")
        print(f"Input case: {case_path}")
        print(f"Outputs: {outputs_dir}\n")
        print("NEXT STEPS:")
        print("1. Start the UI:")
        print("   PYTHONPATH=src python scripts/launch_crane_runway_ui.py")
        print("2. Open Project Workspace.")
        print(f"3. Open project: {args.project_name}.")
        print("4. Validate and Run.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
