import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from section_core.crane_runway import CraneRunwayDemandSummary


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "examples" / "end_to_end_crane_runway_demo.py"


spec = importlib.util.spec_from_file_location("end_to_end_crane_runway_demo", SCRIPT_PATH)
end_to_end_crane_runway_demo = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(end_to_end_crane_runway_demo)


def test_build_demo_summary_and_reports():
    summary = end_to_end_crane_runway_demo.build_demo_summary()
    assert isinstance(summary, CraneRunwayDemandSummary)

    assert summary.max_vertical_moment_Nmm() > 0
    assert summary.max_vertical_shear_abs_N() > 0
    assert summary.max_vertical_deflection_mm() > 0
    assert summary.max_lateral_moment_Nmm() > 0
    assert summary.max_biaxial_stress_MPa() > 0
    assert summary.max_torsional_input_Nmm() > 0

    assert summary.serviceability_results
    assert summary.stress_utilization_results
    assert "overall_passed" in summary.to_dict()

    text, markdown = end_to_end_crane_runway_demo.build_demo_reports()
    assert "Crane Runway Demand Summary" in text
    assert "demo_crane" in text
    assert "No CIRSOC design-code checks are performed" in text

    assert "# Crane Runway Demand Summary" in markdown
    assert "## Demands" in markdown
    assert "## Checks" in markdown
    assert "## Warnings" in markdown


def test_demo_script_subprocess_runs():
    run = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert run.returncode == 0, run.stderr
    assert "Crane Runway Demand Summary" in run.stdout
    assert "# Crane Runway Demand Summary" in run.stdout
