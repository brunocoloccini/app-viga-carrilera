from __future__ import annotations

import argparse
import importlib
import os
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("PYTHONPATH", "")
    src = str(SRC_PATH)
    env["PYTHONPATH"] = src if not current else f"{src}{os.pathsep}{current}"
    return env


def _public_api_import_check() -> tuple[bool, list[str]]:
    try:
        import section_core

        getattr(section_core, "__all__", [])
        from section_core import (  # noqa: F401
            CraneRailRecord,
            CraneRailRegistry,
            CraneRunwayApiService,
            HtmlReportingError,
            InvalidHtmlReportSummaryError,
            SteelMaterial,
            UserFacingValidationMessage,
            UserFacingValidationReport,
        )
        return True, []
    except Exception as exc:  # pragma: no cover
        return False, [f"IMPORT_ERROR {exc}"]


def audit_all_bindings() -> list[str]:
    import section_core

    missing: list[str] = []
    for module_info in pkgutil.walk_packages(section_core.__path__, section_core.__name__ + "."):
        module = importlib.import_module(module_info.name)
        exported = getattr(module, "__all__", None)
        if exported is None:
            continue
        for name in exported:
            if not hasattr(module, name):
                missing.append(f"MISSING_EXPORT {module_info.name}.{name}")
    return sorted(missing)


def _all_binding_check() -> tuple[bool, list[str]]:
    missing = audit_all_bindings()
    return len(missing) == 0, missing


def _run_command(args: Sequence[str], env: dict[str, str]) -> tuple[bool, list[str]]:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return True, []
    details: list[str] = [f"COMMAND_FAILED {' '.join(args)}"]
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if stdout:
        details.append(stdout)
    if stderr:
        details.append(stderr)
    return False, details


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run beta repository health checks.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip full `pytest -q` run.")
    parser.add_argument("--quiet", action="store_true", help="Only print final result and failure details.")
    args = parser.parse_args(argv)

    env = _build_env()

    checks: list[tuple[str, Callable[[], tuple[bool, list[str]]], bool]] = [
        ("Public API import check", _public_api_import_check, True),
        ("__all__ binding audit", _all_binding_check, True),
        (
            "pytest -q",
            lambda: _run_command([sys.executable, "-m", "pytest", "-q"], env),
            not args.skip_pytest,
        ),
        (
            "CLI smoke checks",
            lambda: _run_cli_smoke_checks(env),
            True,
        ),
        (
            "docs smoke tests",
            lambda: _run_command([sys.executable, "-m", "pytest", "-q", "tests/test_beta_docs_smoke.py"], env),
            True,
        ),
        (
            "public API export tests",
            lambda: _run_command([sys.executable, "-m", "pytest", "-q", "tests/test_public_api_exports.py"], env),
            True,
        ),
    ]

    all_pass = True
    failure_details: list[str] = []
    if not args.quiet:
        print("BETA HEALTH CHECK\n")

    total = len(checks)
    for idx, (name, runner, enabled) in enumerate(checks, start=1):
        if not enabled:
            if not args.quiet:
                print(f"[{idx}/{total}] {name} ... SKIP")
            continue
        passed, details = runner()
        status = "PASS" if passed else "FAIL"
        if not args.quiet:
            print(f"[{idx}/{total}] {name} ... {status}")
        if not passed:
            all_pass = False
            failure_details.extend(details)

    for line in failure_details:
        print(line)

    print(f"\nRESULT: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


def _run_cli_smoke_checks(env: dict[str, str]) -> tuple[bool, list[str]]:
    commands = [
        [sys.executable, "scripts/validate_crane_runway_case.py", "examples/crane_runway_case_demo.json"],
        [
            sys.executable,
            "scripts/run_crane_runway_case.py",
            "examples/crane_runway_case_demo.json",
            "--summary-json",
        ],
        [sys.executable, "scripts/run_crane_runway_case_matrix.py"],
    ]
    all_details: list[str] = []
    for cmd in commands:
        passed, details = _run_command(cmd, env)
        if not passed:
            all_details.extend(details)
    return len(all_details) == 0, all_details


if __name__ == "__main__":
    raise SystemExit(main())
