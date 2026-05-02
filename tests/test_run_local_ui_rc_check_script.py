from __future__ import annotations

import importlib.util
from pathlib import Path

from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi

SCRIPT = Path("scripts/run_local_ui_rc_check.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("run_local_ui_rc_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_help_mentions_options(capsys) -> None:
    module = _load_module()
    try:
        module.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    for token in ["--host", "--port", "--timeout", "--project-name", "--template", "--keep-server", "--skip-archive", "--verbose"]:
        assert token in out


def test_invalid_arg_exits_2() -> None:
    module = _load_module()
    try:
        module.main(["--nope"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit for invalid arg")


def test_extract_inline_script_from_rendered_html() -> None:
    module = _load_module()
    html = CraneRunwayLocalWebUi().render_index_html()
    script = module.extract_inline_script(html)
    assert "function loadTemplate" in script


def test_node_check_script_graceful() -> None:
    module = _load_module()
    ok, detail = module.node_check_script("function a(){ return 1; }")
    assert ok in {True, False}
    if ok:
        assert isinstance(detail, str)


def test_wait_for_server_unused_port_fails_cleanly() -> None:
    module = _load_module()
    assert module.wait_for_server("http://127.0.0.1:9/api/health", timeout=0.2) is False


def test_zip_entry_safety_helper() -> None:
    module = _load_module()
    assert module.is_safe_zip_entry("input_case.json") is True
    assert module.is_safe_zip_entry("/tmp/evil") is False
    assert module.is_safe_zip_entry("../evil.txt") is False
