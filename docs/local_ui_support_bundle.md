# Local UI Support Bundle

Use **Support Bundle** panel to collect beta diagnostics. It includes current JSON case, validation/run responses, warnings, project/run selections, and browser diagnostics. Review before sharing because case data may be present.

## Browser workflow
1. Refresh Support Bundle Preview.
2. Review preview table (bundle_version, generated_at, parse status, case summary, response presence).
3. Download Support Bundle JSON or Copy Support Bundle JSON.
4. Use Issue Report Helper to generate/copy a report template.

## CLI collector
- `PYTHONPATH=src python scripts/collect_local_ui_support_bundle.py --output out/support_bundle.json`
- `PYTHONPATH=src python scripts/collect_local_ui_support_bundle.py --project mi_viga --output out/mi_viga_support_bundle.json`
- `PYTHONPATH=src python scripts/collect_local_ui_support_bundle.py --case-path projects/mi_viga/input_case.json --output out/case_support_bundle.json`

## Limitations
- Not an engineering report.
- Not a code-compliance record.
- No PDF/DOCX export.
- Review before sharing.
- May include case data.
