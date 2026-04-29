# Crane runway serviceability criteria model (V1-026)

## Purpose

This module adds a generic, configurable serviceability checking layer for **vertical deflection** results.
It evaluates calculated deflection demands against user-defined limits and reports pass/fail with utilization.

This is intentionally **not** a design-code implementation. No CIRSOC/CISC/AISC-specific defaults are embedded.

## Scope in V1-026

- Generic deflection limit model (`DeflectionLimit`)
- Result container for pass/fail checks (`ServiceabilityCheckResult`)
- Checker for moving and fixed deflection outputs (`DeflectionServiceabilityChecker`)
- Optional grouped criteria set (`DeflectionCriteriaSet`)

## Supported limit forms

1. **Span/N**
   - Limit type: `span_divisor`
   - Allowable = `span / N`

2. **Absolute deflection limit**
   - Limit type: `absolute`
   - Allowable = user value converted to internal mm

3. **Combined minimum of span/N and absolute**
   - Limit type: `minimum_of_span_divisor_and_absolute`
   - Allowable = `min(span/N, absolute_limit)`

## Sign convention

Deflection analysis uses:

- Positive wheel load = downward
- Positive deflection = downward

Serviceability checks compare calculated positive downward deflection demand against positive allowable limits.

## Analysis vs criteria

- Deflection analyzers compute structural response (demand).
- Serviceability criteria define acceptance thresholds (allowable).
- The checker combines these to produce utilization and pass/fail.

This separation keeps analysis reusable and criteria configurable.

## Future steps

- Code-specific preset criteria sets (e.g., CIRSOC/CISC/AISC as opt-in presets)
- Lateral deflection serviceability criteria
- Crane class / service class presets
- Structured report generation
