"""Local UI asset helpers for crane runway local web UI."""

from __future__ import annotations


def render_local_ui_version_info() -> str:
    return "Local UI beta version V1-086 · schema version 1.0"


def render_local_ui_css() -> str:
    return """:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e5e7eb;
  --color-text: #111827;
  --color-muted: #4b5563;
  --color-primary: #2563eb;
  --color-primary-strong: #1d4ed8;
  --color-danger: #b91c1c;
  --color-warning: #92400e;
  --color-success: #166534;
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 0.75rem;
  --space-lg: 1rem;
  --radius-sm: 6px;
  --radius-md: 10px;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.08);
}
.app-shell{} .app-header{} .app-sidebar{} .app-main{} .app-card{} .app-card-header{} .app-card-body{}
.tab-button{} .tab-button.active{}
.primary-action{} .secondary-action{} .danger-action{}
.status-pass{color:var(--color-success);} .status-fail{color:var(--color-danger);} .status-na{color:var(--color-muted);} 
.warning-box{} .info-box{} .form-grid{} .field-row{} .compact-summary{} .empty-state{}
"""


def render_local_ui_js() -> str:
    return """// Constants
const LOCAL_UI_BETA_VERSION = "V1-086";
const LOCAL_UI_SCHEMA_VERSION = "1.0";
const LOCAL_UI_STORAGE_PREFIX = "craneRunway";
// State
let __localUiInitialized = false;
// DOM helpers
function byId(id){ return document.getElementById(id); }
// Status helpers
function setAppShellStatus(message){ const el = byId('app_shell_status'); if (el) { el.textContent = message; }}
// Tab/navigation helpers
function setupActionHandlers(){ document.addEventListener('click', (event) => { const target = event.target.closest('[data-action]'); if (!target) return; handleUiAction(target.getAttribute('data-action'), event); }); }
function handleUiAction(action, event){ if (action === 'validate-case') { validateCase(); } else if (action === 'run-case') { runCase(); } else if (action === 'load-demo') { loadTemplate('ipn-with-cover'); } }
// JSON helpers
// Workflow helpers
// Project helpers
// Form helpers
// Wheel helpers
// Validation/run helpers
function validateCase(){}
function runCase(){}
// Results helpers
// Export helpers
// Support/diagnostics helpers
// Initialization
function initializeLocalUi(){
  if (__localUiInitialized) return;
  __localUiInitialized = true;
  try {
    if (typeof restoreActiveTab === 'function') { restoreActiveTab(); }
    if (typeof restoreSession === 'function') { restoreSession(); }
    if (typeof renderBetaReadiness === 'function') { renderBetaReadiness(); }
    if (typeof renderGuidedDemo === 'function') { renderGuidedDemo(); }
    if (typeof renderDocumentationPortal === 'function') { renderDocumentationPortal(); }
    if (typeof renderRcStatus === 'function') { renderRcStatus(); }
    if (typeof updateCompactSummary === 'function') { updateCompactSummary(); }
    setupActionHandlers();
    setAppShellStatus('Local UI initialized.');
  } catch (_error) {
    setAppShellStatus('Local UI initialization error.');
  }
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeLocalUi);
} else {
  initializeLocalUi();
}
"""


def render_local_ui_body_html() -> str:
    return '<div class="app-shell"></div>'


def render_local_ui_shell_html() -> str:
    return f'<!doctype html><html><head><link rel="stylesheet" href="/assets/local_ui.css"></head><body>{render_local_ui_body_html()}<script src="/assets/local_ui.js"></script></body></html>'
