from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi


def test_local_ui_beta_smoke_contains_expected_workflow_sections() -> None:
    html = CraneRunwayLocalWebUi().render_index_html()
    tokens = [
        # Core
        "Crane Runway Local UI",
        "App Viga Carrilera",
        "Crane Runway Local UI",
        "Internal Beta",
        "Results require engineering review",
        "No official CIRSOC/CISC/AISC compliance checks are performed",
        "engineering review",
        # Main workflow
        "Go to Results",
        "Load Demo",
        "Advanced",
        "Support",
        "Export",
        "Calculate",
        "Results",
        "Calculate",
        "Review",
        "Loads",
        "Setup",
        "Project",
        "Home",
        "Load Template",
        "Form-First Workflow",
        "Apply All Forms To JSON",
        "Validate & Run",
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
        "/assets/local_ui.css",
        "/assets/local_ui.js",
    ]
    for token in tokens:
        assert token in html


def test_local_ui_frontend_contract_smoke_tokens() -> None:
    html=CraneRunwayLocalWebUi().render_index_html();
    for t in ["Frontend Self-Test","/assets/frontend_contract.json","Run Frontend Self-Test","LOCAL_UI_BETA_VERSION","initializeLocalUi"]: assert t in html
