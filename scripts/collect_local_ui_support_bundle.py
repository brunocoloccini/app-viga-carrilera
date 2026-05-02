from __future__ import annotations
import argparse, json, os, platform, re, subprocess, sys
from datetime import datetime, UTC
from pathlib import Path

SAFE_NAME=re.compile(r'^[A-Za-z0-9_-]+$')

def summarize_case(data):
    return {
        'case_id': data.get('meta',{}).get('case_id'),
        'base_shape_id': data.get('section',{}).get('base_shape_id'),
        'material_id': data.get('material',{}).get('id'),
        'wheel_count': len(data.get('loads',{}).get('wheels',[]) or []),
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description='Collect local UI support bundle.')
    ap.add_argument('--project')
    ap.add_argument('--projects-root', default='projects')
    ap.add_argument('--case-path')
    ap.add_argument('--output', required=True)
    ap.add_argument('--include-health-check', action='store_true')
    ap.add_argument('--pretty', action='store_true', default=True)
    ap.add_argument('--compact', action='store_true')
    args=ap.parse_args(argv)

    repo=Path.cwd().resolve()
    bundle={
        'bundle_version':'1.0','generated_at':datetime.now(UTC).isoformat(),'generated_by':'collect_local_ui_support_bundle.py',
        'repository_root':str(repo),'python_version':sys.version,'platform':platform.platform(),
        'file_flags':{p:(repo/p).exists() for p in [
            'scripts/serve_crane_runway_ui.py','scripts/launch_crane_runway_ui.py','scripts/run_local_ui_rc_check.py','docs/local_ui_beta_manual_qa_checklist.md']},
        'notes':['Support bundle for beta debugging.','Review before sharing.','Results require engineering review.','Not an official design-code compliance record.']
    }
    try:
        if args.project:
            if not SAFE_NAME.fullmatch(args.project):
                raise ValueError('Invalid project name. Use only letters, numbers, dash, and underscore.')
            root=Path(args.projects_root)
            proj=root/args.project
            bundle['project']={'name':args.project,'projects_root':str(root)}
            case_path=proj/'input_case.json'
            if case_path.exists():
                text=case_path.read_text(encoding='utf-8')
                data=json.loads(text)
                bundle['project']['input_case_path']=str(case_path)
                bundle['project']['case_summary']=summarize_case(data)
            outputs=proj/'outputs'
            bundle['project']['outputs_exists']=outputs.exists()
            hist=proj/'run_history'
            if hist.exists():
                bundle['project']['run_history_ids']=sorted([p.name for p in hist.iterdir() if p.is_dir()])
        if args.case_path:
            cp=Path(args.case_path)
            text=cp.read_text(encoding='utf-8')
            data=json.loads(text)
            bundle['case_path']=str(cp)
            bundle['case_summary']=summarize_case(data)
        if args.include_health_check:
            cmd=[sys.executable,'scripts/run_beta_health_check.py','--skip-pytest']
            env=dict(os.environ); env['PYTHONPATH']='src'
            proc=subprocess.run(cmd,capture_output=True,text=True,env=env)
            lines=(proc.stdout+'\n'+proc.stderr).splitlines()
            bundle['health_check']={'exit_code':proc.returncode,'tail':lines[-20:]}
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out=Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.compact:
        out.write_text(json.dumps(bundle,separators=(',',':')), encoding='utf-8')
    else:
        out.write_text(json.dumps(bundle,indent=2,ensure_ascii=False), encoding='utf-8')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
