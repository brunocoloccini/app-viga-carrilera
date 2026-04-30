# Beta Health Check

## Purpose

The beta health check is a single deterministic developer-tooling script used to confirm the repository is in a sane state before continuing work.

## When to run it

- After merging fixes.
- Before starting a new feature block.
- Before beta handoff.

## What it checks

1. Public API import check.
2. `__all__` binding audit for importable `section_core` modules.
3. Full `pytest -q` test suite.
4. CLI smoke checks.
5. Docs smoke tests.
6. Public API export tests.

## Commands

```bash
PYTHONPATH=src python scripts/run_beta_health_check.py
PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest
PYTHONPATH=src python scripts/run_beta_health_check.py --skip-pytest --quiet
```

## Exit codes

- `0`: all enabled checks passed.
- `1`: one or more enabled checks failed.
- `2`: invalid script arguments.

## Limitations

- This does not prove engineering correctness.
- This does not replace independent verification.
- This does not directly check external Codex UI stale comments.
