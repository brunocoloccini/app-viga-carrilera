# Local UI Beta Distribution

Use this guide when handing off the local UI beta to another user.

## Recommended handoff target

Share a specific branch/tag/commit (preferred: a tagged commit for the beta handoff).

## Required commands before handoff

1. `PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest`
2. `PYTHONPATH=src pytest -q`
3. `PYTHONPATH=src python scripts/print_local_ui_beta_info.py --check-files`
4. `PYTHONPATH=src python scripts/create_local_ui_demo_project.py --overwrite --run`

## Demo project command

- `PYTHONPATH=src python scripts/create_local_ui_demo_project.py --overwrite --run`

## Launch command

- `PYTHONPATH=src python scripts/launch_crane_runway_ui.py`

## Support bundle command

- `PYTHONPATH=src python scripts/collect_local_ui_support_bundle.py --output out/support_bundle.json`

## Do not rely on these for handoff

- browser `localStorage`
- uncommitted `out/` files
- generated `projects/` workspaces unless exported/archived

## Security warning

- Keep service bound to `127.0.0.1` for local use.
- do not expose UI publicly.
- Project endpoints can write local files under `projects/`.
