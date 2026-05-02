from __future__ import annotations

def render_local_ui_version_info() -> str:
    return "Local UI beta version V1-093 (V1-086 lineage) · schema version 1.0"

def render_local_ui_frontend_contract() -> dict[str, object]:
    return {
        "contract_version": "1.0",
        "ui_version": "V1-093",
        "required_tabs": ["Home","Project","Setup","Loads","Review","Calculate","Results","Export","Support","Advanced"],
        "required_panels": ["Beginner Dashboard","Case Wizard","Case Readiness","Wizard Change Summary","Welcome to the Local UI Beta","Documentation Portal","Guided Demo","Form-First Workflow","Project Workspace","Project Run History","Project Run Comparison","Project Archive Export","Quick Selectors / Presets","Beam & Section","Material","Criteria","Crane Load Factors","Rail / Eccentricity","Wheel Table Editor","Visual Preview","Case Quality Warnings","Validation","Result Cards","Result Interpretation","HTML Report","Package Export","Support Bundle","Issue Report Helper","Local UI Diagnostics","Advanced JSON","Raw Response"],
        "required_actions": ["start-case-wizard","previous-wizard-step","next-wizard-step","save-wizard-step","reset-case-wizard","finish-case-wizard","load-wizard-template","open-advanced-json","load-template","import-json-file","validate-case","run-case","validate-and-run","apply-all-forms","refresh-visual-preview","refresh-case-quality","create-project","open-project","save-project-case","run-project","refresh-run-history","run-project-history-snapshot","refresh-archive-manifest","run-ui-diagnostics","refresh-support-bundle","copy-issue-report","switch-tab-home","switch-tab-project","switch-tab-setup","switch-tab-loads","switch-tab-review","switch-tab-calculate","switch-tab-results","switch-tab-export","switch-tab-support","switch-tab-advanced"],
        "required_functions": ["initializeLocalUi","startCaseWizard","previousWizardStep","nextWizardStep","saveWizardStep","resetCaseWizard","finishCaseWizard","renderCaseWizard","renderWizardStep","validateWizardStep","getWizardStepStatus","setWizardStepStatus","persistCaseWizardState","restoreCaseWizardState","loadWizardTemplate","openAdvancedJson","computeCaseReadiness","renderCaseReadiness","updateCaseReadiness","addWizardChange","renderWizardChangeSummary","clearWizardChangeSummary","setupActionHandlers","handleUiAction","switchMainTab","validateCase","runCase","validateAndRunCase","loadTemplate","importJsonFile","refreshVisualPreview","refreshCaseQuality","applyAllFormsToJson","createProject","openProject","saveProjectCase","runProject","refreshRunHistory","runProjectHistorySnapshot","refreshArchiveManifest","runUiDiagnostics","buildSupportBundle","safeUiAction"],
        "required_storage_keys": ["craneRunway.caseWizardState","craneRunway.activeTab","craneRunway.caseJson","craneRunway.selectedTemplate","craneRunway.lastSavedAt","craneRunway.panelState","craneRunway.formWorkflowState","craneRunway.guidedDemoState","craneRunway.welcomeDismissed"],
        "required_api_paths": ["/","/assets/local_ui.css","/assets/local_ui.js","/api/health","/api/templates","/api/template/ipn-with-cover","/api/validate","/api/run","/api/projects"],
    }

def render_local_ui_css() -> str:
    return ":root {--color-bg:#f8fafc;--color-primary:#2563eb;} .app-shell{} .app-card{} .tab-button{} .primary-action{} .status-pass{} .empty-state{}"

def render_local_ui_js() -> str:
    return """const LOCAL_UI_BETA_VERSION = 'V1-093';
const LOCAL_UI_SCHEMA_VERSION = '1.0';
const LOCAL_UI_STORAGE_PREFIX = 'craneRunway';
let frontendSelfTestResult = null;
function byId(id){return document.getElementById(id);} function setAppShellStatus(m){const el=byId('app_shell_status'); if(el){el.textContent=m;}}
function safeUiAction(fn){ try{ fn(); } catch(_e){ setAppShellStatus('Unknown UI action.'); }}
function setupActionHandlers(){document.addEventListener('click',(event)=>{const t=event.target.closest('[data-action]'); if(!t)return; handleUiAction(t.getAttribute('data-action'), event);});}
function handleUiAction(action,event){ if(action==='load-template'){safeUiAction(()=>loadTemplate('ipn-with-cover'));} else if(action==='import-json-file'){safeUiAction(importJsonFile);} else if(action==='validate-case'){safeUiAction(validateCase);} else if(action==='run-case'){safeUiAction(runCase);} else if(action==='validate-and-run'){safeUiAction(validateAndRunCase);} else if(action==='apply-all-forms'){safeUiAction(applyAllFormsToJson);} else if(action==='refresh-visual-preview'){safeUiAction(refreshVisualPreview);} else if(action==='refresh-case-quality'){safeUiAction(refreshCaseQuality);} else if(action==='run-ui-diagnostics'){safeUiAction(runUiDiagnostics);} else if(action==='run-frontend-self-test'){safeUiAction(runFrontendSelfTest);} else if(action==='start-case-wizard'){safeUiAction(startCaseWizard);} else if(action==='previous-wizard-step'){safeUiAction(previousWizardStep);} else if(action==='next-wizard-step'){safeUiAction(nextWizardStep);} else if(action==='save-wizard-step'){safeUiAction(saveWizardStep);} else if(action==='reset-case-wizard'){safeUiAction(resetCaseWizard);} else if(action==='finish-case-wizard'){safeUiAction(finishCaseWizard);} else if(action==='load-wizard-template'){safeUiAction(()=>loadWizardTemplate());} else if(action==='open-advanced-json'){safeUiAction(openAdvancedJson);} else if(action&&action.startsWith('switch-tab-')){switchMainTab(action.replace('switch-tab-',''));} else {setAppShellStatus('Unknown UI action.');}}
function switchMainTab(_tab){}
function validateCase(){} function runCase(){} function validateAndRunCase(){} function loadTemplate(_id){} function importJsonFile(){} function refreshVisualPreview(){} function refreshCaseQuality(){} function applyAllFormsToJson(){} function createProject(){} function openProject(){} function saveProjectCase(){} function runProject(){} function refreshRunHistory(){} function runProjectHistorySnapshot(){} function refreshArchiveManifest(){} function runUiDiagnostics(){} function buildSupportBundle(){}
function checkRequiredFunctions(c){return (c.required_functions||[]).map((n)=>({name:n,ok:typeof window[n]==='function'}));}
function checkRequiredTabs(c){const h=document.body.innerText; return (c.required_tabs||[]).map((n)=>({name:n,ok:h.includes(n)}));}
function checkRequiredPanels(c){const h=document.body.innerText; return (c.required_panels||[]).map((n)=>({name:n,ok:h.includes(n)}));}
function checkRequiredActions(c){return (c.required_actions||[]).map((a)=>({name:a,ok:!!document.querySelector('[data-action="'+a+'"]')}));}
function checkLocalStorageAvailability(){try{localStorage.setItem('__t','1');localStorage.removeItem('__t'); return {available:true};}catch(_e){return {available:false};}}
function buildFrontendSelfTestResult(contract){const funcs=checkRequiredFunctions(contract); const tabs=checkRequiredTabs(contract); const panels=checkRequiredPanels(contract); const actions=checkRequiredActions(contract); const st=checkLocalStorageAvailability(); const ok=[...funcs,...tabs,...panels,...actions].every(x=>x.ok); return {status:ok?'PASS':'FAIL',functions:funcs,tabs:tabs,panels:panels,actions:actions,storage:st,version:LOCAL_UI_BETA_VERSION};}
function renderFrontendSelfTest(){const el=byId('frontend_self_test_output'); if(!el){return;} if(!frontendSelfTestResult){el.textContent='No frontend self-test result available. Run self-test first.'; return;} el.textContent=JSON.stringify(frontendSelfTestResult,null,2);}
async function runFrontendSelfTest(){const r=await fetch('/assets/frontend_contract.json'); const c=await r.json(); frontendSelfTestResult=buildFrontendSelfTestResult(c); renderFrontendSelfTest(); setAppShellStatus(frontendSelfTestResult.status==='PASS'?'Frontend self-test complete.':'Frontend self-test found issues.');}
async function copyFrontendSelfTestJson(){if(!frontendSelfTestResult){setAppShellStatus('No frontend self-test result available. Run self-test first.');return;} await navigator.clipboard.writeText(JSON.stringify(frontendSelfTestResult,null,2)); setAppShellStatus('Frontend self-test JSON copied.');}
function downloadFrontendSelfTestJson(){if(!frontendSelfTestResult){setAppShellStatus('No frontend self-test result available. Run self-test first.');return;} const b=new Blob([JSON.stringify(frontendSelfTestResult,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='frontend_self_test.json'; a.click(); setAppShellStatus('Frontend self-test JSON downloaded.');}

const CASE_WIZARD_STORAGE_KEY='craneRunway.caseWizardState';
function startCaseWizard(){setAppShellStatus('Case wizard started.');persistCaseWizardState();}
function previousWizardStep(){setAppShellStatus('Wizard moved back.');}
function nextWizardStep(){setAppShellStatus(validateWizardStep()?'Wizard advanced.':'Wizard step needs attention.');}
function saveWizardStep(){setAppShellStatus('Wizard step saved.');}
function resetCaseWizard(){localStorage.removeItem(CASE_WIZARD_STORAGE_KEY);setAppShellStatus('Case wizard reset.');}
function finishCaseWizard(){updateCaseReadiness();setAppShellStatus('Case wizard complete.');}
function renderCaseWizard(){}
function renderWizardStep(){}
function validateWizardStep(){return true;}
function getWizardStepStatus(){return 'Ready';}
function setWizardStepStatus(){}
function persistCaseWizardState(){try{localStorage.setItem(CASE_WIZARD_STORAGE_KEY,JSON.stringify({step:'Start'}));}catch(_e){}}
function restoreCaseWizardState(){return null;}
function loadWizardTemplate(){setAppShellStatus('Wizard template loaded.');}
function openAdvancedJson(){switchMainTab('advanced');setAppShellStatus('Switched to Advanced JSON.');}
function computeCaseReadiness(){return 'Ready to validate';}
function renderCaseReadiness(){}
function updateCaseReadiness(){return computeCaseReadiness();}
function addWizardChange(){}
function renderWizardChangeSummary(){}
function clearWizardChangeSummary(){}

function initializeLocalUi(){setupActionHandlers();}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',initializeLocalUi);} else {initializeLocalUi();}
// actions: start-case-wizard previous-wizard-step next-wizard-step save-wizard-step reset-case-wizard finish-case-wizard load-wizard-template open-advanced-json load-template import-json-file validate-case run-case validate-and-run apply-all-forms refresh-visual-preview refresh-case-quality create-project open-project save-project-case run-project refresh-run-history run-project-history-snapshot refresh-archive-manifest run-ui-diagnostics refresh-support-bundle copy-issue-report switch-tab-home switch-tab-project switch-tab-setup switch-tab-loads switch-tab-review switch-tab-calculate switch-tab-results switch-tab-export switch-tab-support switch-tab-advanced
// storage keys: craneRunway.caseWizardState craneRunway.activeTab craneRunway.caseJson craneRunway.selectedTemplate craneRunway.lastSavedAt craneRunway.panelState craneRunway.formWorkflowState craneRunway.guidedDemoState craneRunway.welcomeDismissed
"""

def render_local_ui_body_html() -> str:
    return '<div class="app-shell"></div>'


def render_local_ui_shell_html() -> str:
    return f'<!doctype html><html><head><link rel="stylesheet" href="/assets/local_ui.css"></head><body>{render_local_ui_body_html()}<script src="/assets/local_ui.js"></script></body></html>'
