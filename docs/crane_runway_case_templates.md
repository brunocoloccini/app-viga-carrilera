# Crane runway case templates

Built-in case templates are available for beta JSON workflows and always emit `schema_version: "1.0"`.

Template IDs:
- `ipn-with-cover`
- `ipn-without-cover`
- `ipn-no-rail-eccentricity`

Use `scripts/create_crane_runway_case_template.py --list` to list available templates.
Use `scripts/create_crane_runway_case_template.py --template <ID> --output <PATH>` to generate a JSON case.
