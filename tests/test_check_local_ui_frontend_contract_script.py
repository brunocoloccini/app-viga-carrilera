from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

SCRIPT='scripts/check_local_ui_frontend_contract.py'

def run(*args):
    env=os.environ.copy(); env['PYTHONPATH']='src'; return subprocess.run([sys.executable,SCRIPT,*args],env=env,capture_output=True,text=True)

def test_script_exists(): assert Path(SCRIPT).exists()
def test_help(): r=run('--help'); assert r.returncode==0; assert '--json' in r.stdout and '--verbose' in r.stdout and '--fail-on-node-missing' in r.stdout and '--output' in r.stdout and '--no-node' in r.stdout
def test_invalid_arg(): assert run('--bad-arg').returncode==2
def test_default_run(): assert run('--no-node').returncode==0
def test_json_run(): r=run('--json','--no-node'); assert r.returncode==0; d=json.loads(r.stdout); assert 'overall_passed' in d and 'checks' in d

def test_output_file(tmp_path):
    out=tmp_path/'r.json'; r=run('--no-node','--output',str(out)); assert r.returncode==0 and out.exists(); d=json.loads(out.read_text());
    for k in ['html_tabs','html_panels','actions','javascript_functions','storage_keys','css_design_system','javascript_syntax']: assert k in d['checks']
