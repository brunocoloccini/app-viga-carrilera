from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from section_core.crane_runway import (
    CraneRunwayCaseResult,
    CraneRunwayWorkflowInput,
    InvalidCraneRunwayCaseError,
    build_workflow_input_from_case_dict,
    crane_runway_case_from_json_dict,
    crane_runway_case_to_json_dict,
    dump_crane_runway_case_json,
    load_crane_runway_case_json,
    run_crane_runway_case_dict,
    run_crane_runway_case_json,
)


def _example_case_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "crane_runway_case_demo.json"


def _example_case_dict() -> dict:
    return load_crane_runway_case_json(_example_case_path())


def test_case_json_loading():
    data = _example_case_dict()
    assert data["case_id"] == "demo_case"


def test_build_workflow_input_from_case_dict():
    wi = build_workflow_input_from_case_dict(_example_case_dict())
    assert isinstance(wi, CraneRunwayWorkflowInput)
    assert wi.span_internal_mm == pytest.approx(6000)
    assert wi.movement_step_internal_mm == pytest.approx(250)
    assert wi.station_step_internal_mm == pytest.approx(500)
    assert len(wi.crane_load_model.wheel_group.wheels) == 2


def test_run_case_dict():
    result = run_crane_runway_case_dict(_example_case_dict())
    assert isinstance(result, CraneRunwayCaseResult)
    assert result.workflow_result.summary.max_vertical_moment_Nmm() > 0
    assert result.workflow_result.summary.max_vertical_deflection_mm() > 0
    assert result.workflow_result.summary.max_biaxial_stress_MPa() > 0
    assert "overall_passed" in result.summary_dict
    assert "Crane Runway Demand Summary" in result.text_report
    assert "# Crane Runway Demand Summary" in result.markdown_report


def test_run_case_json_file():
    result = run_crane_runway_case_json(_example_case_path())
    assert result.case_id == "demo_case"


def test_demo_script_runs():
    script = Path(__file__).resolve().parents[1] / "examples" / "run_crane_runway_case_from_json.py"
    out = subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert "Crane Runway Demand Summary" in out.stdout
    assert "# Crane Runway Demand Summary" in out.stdout


def test_validation_errors():
    base = _example_case_dict()
    for k in ["case_id", "shape_library_path"]:
        bad = dict(base)
        bad.pop(k)
        with pytest.raises(InvalidCraneRunwayCaseError):
            build_workflow_input_from_case_dict(bad)

    bad = dict(base)
    bad["crane"] = {"wheels": []}
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(bad)

    bad = _example_case_dict()
    bad["span"] = {"value": 6}
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(bad)

    bad = _example_case_dict()
    bad["serviceability_limits"] = [{"limit_id": "x", "type": "unknown"}]
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(bad)

    bad = _example_case_dict()
    bad["stress_limits"] = [{"limit_id": "x", "type": "unknown"}]
    with pytest.raises(InvalidCraneRunwayCaseError):
        build_workflow_input_from_case_dict(bad)


def test_disabled_cover_plate_and_rail_eccentricity():
    data = _example_case_dict()
    data["section"]["cover_plate"]["enabled"] = False
    data["rail_eccentricity"]["enabled"] = False
    result = run_crane_runway_case_dict(data)
    assert result.workflow_result.summary.max_torsional_input_Nmm() is None


def test_roundtrip_dump_load_and_run(tmp_path: Path):
    data = _example_case_dict()
    serialized = crane_runway_case_to_json_dict(crane_runway_case_from_json_dict(data))
    out = tmp_path / "roundtrip.json"
    dump_crane_runway_case_json(serialized, out)
    loaded = load_crane_runway_case_json(out)
    rerun = run_crane_runway_case_dict(loaded)
    assert rerun.case_id == "demo_case"
