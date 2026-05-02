from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi


def test_local_ui_beta_smoke_contains_expected_workflow_sections() -> None:
    html = CraneRunwayLocalWebUi().render_index_html()
    tokens = [
        # Core
        "Crane Runway Local UI",
        "Local beta tool",
        "engineering review",
        # Main workflow
        "Load Template",
        "Import JSON File",
        "Common Inputs",
        "Apply Form To JSON",
        "Visual Preview",
        "Validate",
        "Validation",
        "Run",
        "Result Cards",
        "Result Interpretation",
        "HTML Report",
        "Package Export",
        "Local UI RC Status",
        "Keyboard Shortcuts",
        "Known limitations",
        "Documentation Portal",
        "Guided Demo",
        "Welcome to the Local UI Beta",
        "Scenario Comparison",
        # Persistence / export
        "Autosave",
        "Clear Saved Session",
        "Download JSON Case",
        "Download Summary JSON",
        "Download HTML Report",
        "Download All Package Files",
        # Warnings / limitations
        "no official CIRSOC/CISC/AISC checks",
        "no fatigue",
        "no torsional/warping stress",
        "no LTB",
        # API references
        "/api/health",
        "/api/templates",
        "/api/validate",
        "/api/run",
    ]
    for token in tokens:
        assert token in html
