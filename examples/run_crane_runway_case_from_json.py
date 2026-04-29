from pathlib import Path

from section_core.crane_runway import run_crane_runway_case_json

case_path = Path(__file__).resolve().parent / "crane_runway_case_demo.json"
result = run_crane_runway_case_json(case_path)
print(result.text_report)
print("\n" + "-" * 80 + "\n")
print(result.markdown_report)
