from __future__ import annotations

from pathlib import Path
import importlib.util
import subprocess
import sys

from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi


def _load_smoke_module():
    path = Path("scripts/check_local_ui_smoke.py")
    spec = importlib.util.spec_from_file_location("check_local_ui_smoke", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_smoke_script_exists() -> None:
    assert Path("scripts/check_local_ui_smoke.py").exists()


def test_smoke_script_help_mentions_options() -> None:
    result = subprocess.run([sys.executable, "scripts/check_local_ui_smoke.py", "--help"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "--url" in result.stdout
    assert "--timeout" in result.stdout


def test_smoke_script_invalid_arg_exits_2() -> None:
    result = subprocess.run([sys.executable, "scripts/check_local_ui_smoke.py", "--invalid"], capture_output=True, text=True, check=False)
    assert result.returncode == 2


def test_extract_inline_script_from_ui_html_contains_diagnostics_function() -> None:
    html = CraneRunwayLocalWebUi().render_index_html()
    smoke_module = _load_smoke_module()
    script = smoke_module.extract_inline_script(html)
    assert "runUiDiagnostics" in script
