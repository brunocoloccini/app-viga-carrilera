from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

SCRIPT=Path('scripts/collect_local_ui_support_bundle.py')

def run(*args):
    return subprocess.run([sys.executable,str(SCRIPT),*args],capture_output=True,text=True)

def test_script_exists():
    assert SCRIPT.exists()

def test_help_mentions_options():
    r=run('--help')
    assert r.returncode==0
    for t in ['--project','--case-path','--output','--include-health-check','--compact']:
        assert t in r.stdout

def test_invalid_args_exit_2():
    r=run('--unknown')
    assert r.returncode==2

def test_repository_bundle(tmp_path):
    out=tmp_path/'support_bundle.json'
    r=run('--output',str(out))
    assert r.returncode==0
    data=json.loads(out.read_text())
    assert data['generated_by']=='collect_local_ui_support_bundle.py'
    assert 'python_version' in data and 'platform' in data and 'notes' in data

def test_case_path_bundle(tmp_path):
    case=tmp_path/'case.json'
    case.write_text(json.dumps({'meta':{'case_id':'c1'},'section':{'base_shape_id':'s1'},'material':{'id':'m1'},'loads':{'wheels':[{},{}]}}))
    out=tmp_path/'bundle.json'
    r=run('--case-path',str(case),'--output',str(out))
    assert r.returncode==0
    data=json.loads(out.read_text())
    assert data['case_path']
    assert data['case_summary']['wheel_count']==2

def test_project_bundle_and_invalid_name(tmp_path):
    root=tmp_path/'projects'
    proj=root/'test_project'
    proj.mkdir(parents=True)
    (proj/'input_case.json').write_text(json.dumps({'meta':{'case_id':'p1'}}))
    out=tmp_path/'bundle.json'
    r=run('--projects-root',str(root),'--project','test_project','--output',str(out))
    assert r.returncode==0
    data=json.loads(out.read_text())
    assert data['project']['name']=='test_project'
    bad=run('--projects-root',str(root),'--project','bad name','--output',str(out))
    assert bad.returncode==1

def test_compact_mode(tmp_path):
    out=tmp_path/'c.json'
    r=run('--output',str(out),'--compact')
    assert r.returncode==0
    txt=out.read_text()
    assert '\n  ' not in txt
    json.loads(txt)
