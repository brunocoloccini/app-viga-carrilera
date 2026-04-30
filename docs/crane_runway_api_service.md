# Crane Runway API Service (V1-053)

## Purpose

`section_core.crane_runway.api_service` provides a minimal local application boundary for crane runway case validation and execution.

It wraps existing schema validation, execution, and reporting flows without changing engineering formulas or core analysis behavior.

## Why pure-Python and framework-independent

The service is intentionally implemented as plain Python classes/dataclasses so it can be reused from:

- CLI tools;
- local scripts;
- tests;
- optional future web adapters (FastAPI, etc.).

No mandatory web framework dependency is introduced in `section_core`.

## Validation methods

- `validate_case_dict(data, strict=True)`
- `validate_case_json_text(json_text, strict=True)`

Both return `CraneRunwayApiValidationResponse` with:

- `valid: bool`
- `messages: list[dict]`
- `metadata: dict`

## Execution methods

- `execute_case_dict(data, output_formats=None)`
- `execute_case_json_text(json_text, output_formats=None)`

Execution validates first, then runs the existing `run_crane_runway_case_dict` path only when valid.

## Output formats

Supported `output_formats` values:

- `summary`
- `text`
- `markdown`
- `html`

Default behavior (`output_formats=None`) is `['summary']`.

Unknown output formats return `success=False` with clear error objects.

## Response object shapes

### `CraneRunwayApiValidationResponse`

- `valid`
- `messages`
- `metadata`
- `to_dict()`

### `CraneRunwayApiExecutionResponse`

- `success`
- `summary`
- `text_report`
- `markdown_report`
- `html_report`
- `validation`
- `errors`
- `metadata`
- `to_dict()`

## Future FastAPI/UI integration

This boundary is designed so a future optional FastAPI adapter can map request/response JSON directly to these service methods and dataclasses.

## Limitations (current V1-053 scope)

- No authentication/authorization.
- No database persistence.
- No deployment/runtime infrastructure configuration.
- No direct file-upload handling.
- No report package file-system writing in this service layer.
- No code-specific (CIRSOC/CISC/AISC) checks.
- No replacement for engineering review/approval.
