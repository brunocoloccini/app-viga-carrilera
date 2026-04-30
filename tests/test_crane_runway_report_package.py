from __future__ import annotations

import json
from pathlib import Path

import pytest

from section_core.crane_runway import (
    CraneRunwayReportPackageManifest,
    CraneRunwayReportPackageWriter,
    InvalidReportPackageError,
    ReportPackageError,
)


def test_manifest_valid_defaults_and_to_dict(tmp_path: Path) -> None:
    manifest = CraneRunwayReportPackageManifest(
        package_id="pkg-1",
        case_id="case-1",
        output_dir=str(tmp_path),
    )
    assert manifest.files == {}
    assert manifest.metadata == {}
    payload = manifest.to_dict()
    assert payload["package_id"] == "pkg-1"
    assert payload["case_id"] == "case-1"


def test_writer_writes_expected_files(tmp_path: Path) -> None:
    out = tmp_path / "pkg"
    result = CraneRunwayReportPackageWriter().write_case_package("examples/crane_runway_case_demo.json", out)
    expected = {
        "input_case.json",
        "validation_report.json",
        "summary.json",
        "report.txt",
        "report.md",
        "report.html",
        "metadata.json",
        "manifest.json",
    }
    assert expected == {p.name for p in out.iterdir() if p.is_file()}
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    validation = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    html = (out / "report.html").read_text(encoding="utf-8")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads((out / "metadata.json").read_text(encoding="utf-8"))
    assert "max_vertical_moment_Nmm" in summary
    assert validation["valid"] is True
    assert "<!doctype html>" in html
    assert expected == set(Path(v).name for v in manifest["files"].values())
    assert metadata["generated_by"] == "CraneRunwayReportPackageWriter"
    assert metadata["source_case_path"].endswith("examples/crane_runway_case_demo.json")
    assert result.manifest.case_id


def test_writer_non_empty_overwrite_behavior(tmp_path: Path) -> None:
    out = tmp_path / "pkg"
    out.mkdir(parents=True)
    (out / "junk.txt").write_text("x", encoding="utf-8")
    writer = CraneRunwayReportPackageWriter()
    with pytest.raises(ReportPackageError):
        writer.write_case_package("examples/crane_runway_case_demo.json", out)
    writer.write_case_package("examples/crane_runway_case_demo.json", out, overwrite=True)
    assert (out / "summary.json").exists()


def test_invalid_case_raises_and_no_partial(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    payload = json.loads(Path("examples/crane_runway_case_demo.json").read_text(encoding="utf-8"))
    payload.pop("schema_version", None)
    bad.write_text(json.dumps(payload), encoding="utf-8")
    out = tmp_path / "pkg"
    with pytest.raises((ReportPackageError, InvalidReportPackageError)):
        CraneRunwayReportPackageWriter().write_case_package(bad, out)
    assert not out.exists() or not any(out.iterdir())


def test_package_determinism_key_files(tmp_path: Path) -> None:
    writer = CraneRunwayReportPackageWriter()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    writer.write_case_package("examples/crane_runway_case_demo.json", out_a)
    writer.write_case_package("examples/crane_runway_case_demo.json", out_b)
    for name in ["summary.json", "report.txt", "report.md", "report.html", "validation_report.json", "input_case.json"]:
        assert (out_a / name).read_text(encoding="utf-8") == (out_b / name).read_text(encoding="utf-8")
