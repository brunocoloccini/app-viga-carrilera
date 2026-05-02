from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/create_local_ui_demo_project.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, env={"PYTHONPATH": "src"}, capture_output=True, text=True)


def test_script_exists() -> None:
    assert SCRIPT.exists()


def test_help_mentions_options() -> None:
    r = _run("--help")
    assert r.returncode == 0
    for token in ["--project-name", "--template", "--overwrite", "--run", "--projects-root", "--quiet"]:
        assert token in r.stdout


def test_invalid_args_exit_2() -> None:
    r = _run("--bad-option")
    assert r.returncode == 2


def test_create_and_overwrite_and_invalid_names(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    r1 = _run("--projects-root", str(root), "--project-name", "demo_test", "--template", "ipn-with-cover")
    assert r1.returncode == 0
    case_path = root / "demo_test" / "input_case.json"
    assert case_path.exists()
    assert (root / "demo_test" / "README.md").exists()
    assert (root / "demo_test" / "outputs").is_dir()
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"

    r2 = _run("--projects-root", str(root), "--project-name", "demo_test")
    assert r2.returncode == 1

    r3 = _run("--projects-root", str(root), "--project-name", "demo_test", "--overwrite")
    assert r3.returncode == 0

    for bad in ["../bad", "bad/name", "bad name"]:
        rb = _run("--projects-root", str(root), "--project-name", bad)
        assert rb.returncode == 1


def test_run_writes_outputs(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    r = _run("--projects-root", str(root), "--project-name", "demo_run", "--run")
    assert r.returncode == 0
    out = root / "demo_run" / "outputs"
    assert (out / "manifest.json").exists() or (out / "report.html").exists()
