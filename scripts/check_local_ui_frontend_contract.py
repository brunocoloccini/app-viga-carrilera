#!/usr/bin/env python
from __future__ import annotations
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path
from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi

def has_all(text, items):
    missing=[x for x in items if x not in text]
    return len(missing)==0, missing

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--json',action='store_true')
    ap.add_argument('--verbose',action='store_true')
    ap.add_argument('--fail-on-node-missing',action='store_true')
    ap.add_argument('--output')
    ap.add_argument('--no-node',action='store_true')
    args=ap.parse_args()
    ui=CraneRunwayLocalWebUi()
    html=ui.render_index_html()
    css=ui.handle_request('GET','/assets/local_ui.css').body
    js=ui.handle_request('GET','/assets/local_ui.js').body
    contract=json.loads(ui.handle_request('GET','/assets/frontend_contract.json').body)
    checks={}
    checks['html_tabs']={'passed':has_all(html,contract['required_tabs'])[0]}
    checks['html_panels']={'passed':has_all(html,contract['required_panels'])[0]}
    aok=all(((f'data-action="{a}"' in html) or (a in js)) for a in contract['required_actions'])
    checks['actions']={'passed':aok}
    checks['javascript_functions']={'passed':all((f'function {f}' in js) or (f in js) for f in contract['required_functions'])}
    checks['storage_keys']={'passed':all(k in js for k in contract['required_storage_keys'])}
    checks['css_design_system']={'passed':all(t in css for t in ['--color-bg','.app-shell','.app-card','.tab-button','.primary-action'])}
    if args.no_node:
      node_passed=True; node_status='disabled'
    else:
      node=shutil.which('node')
      if not node:
        node_passed=not args.fail_on_node_missing; node_status='missing'
      else:
        with tempfile.TemporaryDirectory() as d:
          p=Path(d)/'local_ui.js'; p.write_text(js,encoding='utf-8')
          r=subprocess.run([node,'--check',str(p)],capture_output=True,text=True)
          node_passed=(r.returncode==0); node_status='pass' if node_passed else 'fail'
    checks['javascript_syntax']={'passed':node_passed,'status':node_status}
    overall=all(v['passed'] for v in checks.values())
    report={'overall_passed':overall,'checks':checks}
    if args.output: Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if args.json:
      print(json.dumps(report))
    else:
      names=['html_tabs','html_panels','actions','javascript_functions','storage_keys','css_design_system','javascript_syntax']
      print('LOCAL UI FRONTEND CONTRACT CHECK')
      for i,n in enumerate(names,1):
        print(f'[{i}/7] {n} ... ' + ('PASS' if checks[n]['passed'] else 'FAIL'))
      print('RESULT: ' + ('PASS' if overall else 'FAIL'))
    raise SystemExit(0 if overall else 1)
if __name__=='__main__': main()
