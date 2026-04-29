"""Crane runway demand summary/report aggregation (V1-032)."""

from __future__ import annotations

from dataclasses import dataclass, field


class DemandSummaryError(ValueError):
    """Base error for demand summary creation/aggregation."""


class InvalidDemandSummaryError(DemandSummaryError):
    """Invalid demand summary input data."""


@dataclass
class CraneRunwayDemandSummary:
    summary_id: str
    span_internal_mm: float
    section_id: str | None = None
    load_model_id: str | None = None
    gross_properties: object | None = None
    vertical_envelope: object | None = None
    envelope_curves: object | None = None
    deflection_envelope: object | None = None
    vertical_stress_result: object | None = None
    lateral_analysis_result: object | None = None
    lateral_stress_result: object | None = None
    biaxial_stress_result: object | None = None
    torsional_load_group: object | None = None
    serviceability_results: list[object] = field(default_factory=list)
    stress_utilization_results: list[object] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.summary_id:
            raise InvalidDemandSummaryError("summary_id is required.")
        if self.span_internal_mm <= 0:
            raise InvalidDemandSummaryError("span_internal_mm must be > 0.")

    def max_vertical_moment_Nmm(self) -> float | None:
        if self.vertical_envelope is None:
            return None
        return getattr(self.vertical_envelope, "max_moment_Nmm", None)

    def max_vertical_shear_abs_N(self) -> float | None:
        if self.vertical_envelope is None:
            return None
        return getattr(self.vertical_envelope, "max_shear_abs_N", None)

    def max_vertical_deflection_mm(self) -> float | None:
        if self.deflection_envelope is None:
            return None
        return getattr(self.deflection_envelope, "max_deflection_mm", None)

    def max_lateral_moment_Nmm(self) -> float | None:
        if self.lateral_analysis_result is None:
            return None
        return getattr(self.lateral_analysis_result, "max_lateral_moment_Nmm", None)

    def max_biaxial_stress_MPa(self) -> float | None:
        if self.biaxial_stress_result is None:
            return None
        return getattr(self.biaxial_stress_result, "max_abs_stress_MPa", None)

    def max_torsional_input_Nmm(self) -> float | None:
        if self.torsional_load_group is None:
            return None
        loads = getattr(self.torsional_load_group, "torsional_loads", None)
        if not loads:
            return None
        return max(abs(x.torsional_moment_internal_Nmm) for x in loads)

    def serviceability_passed(self) -> bool | None:
        if not self.serviceability_results:
            return None
        return all(r.passed for r in self.serviceability_results)

    def stress_criteria_passed(self) -> bool | None:
        if not self.stress_utilization_results:
            return None
        return all(r.passed for r in self.stress_utilization_results)

    def overall_passed(self) -> bool | None:
        checks = [x for x in [self.serviceability_passed(), self.stress_criteria_passed()] if x is not None]
        if not checks:
            return None
        if any(x is False for x in checks):
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "summary_id": self.summary_id,
            "span_internal_mm": self.span_internal_mm,
            "section_id": self.section_id,
            "load_model_id": self.load_model_id,
            "max_vertical_moment_Nmm": self.max_vertical_moment_Nmm(),
            "max_vertical_shear_abs_N": self.max_vertical_shear_abs_N(),
            "max_vertical_deflection_mm": self.max_vertical_deflection_mm(),
            "max_lateral_moment_Nmm": self.max_lateral_moment_Nmm(),
            "max_biaxial_stress_MPa": self.max_biaxial_stress_MPa(),
            "max_torsional_input_Nmm": self.max_torsional_input_Nmm(),
            "serviceability_passed": self.serviceability_passed(),
            "stress_criteria_passed": self.stress_criteria_passed(),
            "overall_passed": self.overall_passed(),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }


class CraneRunwayDemandSummaryBuilder:
    """Small helper for assembling a summary from partial runway analysis artifacts."""

    @staticmethod
    def build_basic_summary(
        *,
        summary_id: str,
        span_internal_mm: float,
        section_id: str | None = None,
        load_model_id: str | None = None,
        gross_properties: object | None = None,
        vertical_envelope: object | None = None,
        deflection_envelope: object | None = None,
        lateral_analysis_result: object | None = None,
        biaxial_stress_result: object | None = None,
        torsional_load_group: object | None = None,
        serviceability_results: list[object] | None = None,
        stress_utilization_results: list[object] | None = None,
        warnings: list[str] | None = None,
        metadata: dict | None = None,
    ) -> CraneRunwayDemandSummary:
        return CraneRunwayDemandSummary(
            summary_id=summary_id,
            span_internal_mm=span_internal_mm,
            section_id=section_id,
            load_model_id=load_model_id,
            gross_properties=gross_properties,
            vertical_envelope=vertical_envelope,
            deflection_envelope=deflection_envelope,
            lateral_analysis_result=lateral_analysis_result,
            biaxial_stress_result=biaxial_stress_result,
            torsional_load_group=torsional_load_group,
            serviceability_results=serviceability_results or [],
            stress_utilization_results=stress_utilization_results or [],
            warnings=warnings or [],
            metadata=metadata or {},
        )
