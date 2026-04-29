"""High-level crane runway calculation workflow orchestration (V1-035)."""

from __future__ import annotations

from dataclasses import dataclass, field

from section_core.units.dimensions import Dimension
from section_core.units.quantity import Quantity

from .biaxial_stress import ElasticBiaxialStressAnalyzer
from .deflection_envelope import SimpleSpanMovingDeflectionEnvelopeAnalyzer
from .demand_summary import CraneRunwayDemandSummary, CraneRunwayDemandSummaryBuilder
from .envelope import SimpleSpanMovingLoadEnvelopeAnalyzer
from .envelope_curves import SimpleSpanEnvelopeCurveAnalyzer
from .lateral_analysis import ElasticLateralBendingStressAnalyzer, SimpleSpanRunwayBeamLateralAnalyzer
from .loads import CraneLoadModel, CraneWheelGroup, WheelLoad
from .rail_eccentricity import RailEccentricityModel
from .reporting import CraneRunwayDemandSummaryFormatter
from .serviceability import DeflectionCriteriaSet, DeflectionLimit, DeflectionServiceabilityChecker
from .stress import ElasticVerticalBendingStressAnalyzer
from .stress_criteria import ElasticStressCriteriaChecker, StressCriteriaSet, StressLimit


class CraneRunwayWorkflowError(ValueError):
    """Base error for crane runway workflow input or execution."""


class InvalidCraneRunwayWorkflowInputError(CraneRunwayWorkflowError):
    """Invalid workflow input payload."""


class CraneRunwayWorkflowExecutionError(CraneRunwayWorkflowError):
    """Error while executing the workflow."""


@dataclass
class CraneRunwayWorkflowInput:
    workflow_id: str
    span_internal_mm: float
    section: object
    crane_load_model: CraneLoadModel
    movement_step_internal_mm: float
    station_step_internal_mm: float
    E_internal_MPa: float
    serviceability_limits: list[DeflectionLimit] | None = None
    stress_limits: list[StressLimit] | None = None
    rail_eccentricity_model: RailEccentricityModel | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise InvalidCraneRunwayWorkflowInputError("workflow_id is required.")
        if self.span_internal_mm <= 0:
            raise InvalidCraneRunwayWorkflowInputError("span_internal_mm must be > 0.")
        if self.section is None:
            raise InvalidCraneRunwayWorkflowInputError("section is required.")
        if self.crane_load_model is None:
            raise InvalidCraneRunwayWorkflowInputError("crane_load_model is required.")
        if self.movement_step_internal_mm <= 0:
            raise InvalidCraneRunwayWorkflowInputError("movement_step_internal_mm must be > 0.")
        if self.station_step_internal_mm <= 0:
            raise InvalidCraneRunwayWorkflowInputError("station_step_internal_mm must be > 0.")
        if self.E_internal_MPa <= 0:
            raise InvalidCraneRunwayWorkflowInputError("E_internal_MPa must be > 0.")

    @classmethod
    def from_values(
        cls,
        *,
        workflow_id: str,
        span: float,
        span_unit: str,
        section: object,
        crane_load_model: CraneLoadModel,
        movement_step: float,
        movement_step_unit: str,
        station_step: float,
        station_step_unit: str,
        E: float,
        E_unit: str,
        serviceability_limits: list[DeflectionLimit] | None = None,
        stress_limits: list[StressLimit] | None = None,
        rail_eccentricity_model: RailEccentricityModel | None = None,
        warnings: list[str] | None = None,
        metadata: dict | None = None,
    ) -> CraneRunwayWorkflowInput:
        try:
            span_q = Quantity(span, span_unit, Dimension.LENGTH)
            move_q = Quantity(movement_step, movement_step_unit, Dimension.LENGTH)
            station_q = Quantity(station_step, station_step_unit, Dimension.LENGTH)
            e_q = Quantity(E, E_unit, Dimension.STRESS)
        except Exception as exc:
            raise InvalidCraneRunwayWorkflowInputError(str(exc)) from exc

        return cls(
            workflow_id=workflow_id,
            span_internal_mm=span_q.internal_value,
            section=section,
            crane_load_model=crane_load_model,
            movement_step_internal_mm=move_q.internal_value,
            station_step_internal_mm=station_q.internal_value,
            E_internal_MPa=e_q.internal_value,
            serviceability_limits=serviceability_limits,
            stress_limits=stress_limits,
            rail_eccentricity_model=rail_eccentricity_model,
            warnings=warnings or [],
            metadata=metadata or {},
        )


@dataclass
class CraneRunwayWorkflowResult:
    workflow_id: str
    summary: CraneRunwayDemandSummary
    text_report: str
    markdown_report: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise InvalidCraneRunwayWorkflowInputError("workflow_id is required.")
        if self.summary is None:
            raise InvalidCraneRunwayWorkflowInputError("summary is required.")
        if not self.text_report:
            raise InvalidCraneRunwayWorkflowInputError("text_report is required.")
        if not self.markdown_report:
            raise InvalidCraneRunwayWorkflowInputError("markdown_report is required.")


class CraneRunwayCalculationWorkflow:
    def __init__(self, workflow_input: CraneRunwayWorkflowInput) -> None:
        self.workflow_input = workflow_input

    def run(self) -> CraneRunwayWorkflowResult:
        try:
            wi = self.workflow_input
            warnings = list(wi.warnings)
            metadata = dict(wi.metadata)

            gross = wi.section.gross_elastic_properties()
            nominal_group = wi.crane_load_model.nominal_wheel_group()
            vertical_group = wi.crane_load_model.factored_vertical_wheel_group()
            lateral_group = wi.crane_load_model.generated_lateral_wheel_group()

            vertical_env = SimpleSpanMovingLoadEnvelopeAnalyzer(
                span_internal_mm=wi.span_internal_mm,
                step_internal_mm=wi.movement_step_internal_mm,
            ).analyze_envelope(vertical_group)

            envelope_curves = SimpleSpanEnvelopeCurveAnalyzer(
                span_internal_mm=wi.span_internal_mm,
                movement_step_internal_mm=wi.movement_step_internal_mm,
                station_step_internal_mm=wi.station_step_internal_mm,
            ).analyze_curves(vertical_group)

            deflection_env = SimpleSpanMovingDeflectionEnvelopeAnalyzer(
                span_internal_mm=wi.span_internal_mm,
                E_internal_MPa=wi.E_internal_MPa,
                I_internal_mm4=gross.Iyy_mm4,
                movement_step_internal_mm=wi.movement_step_internal_mm,
                station_step_internal_mm=wi.station_step_internal_mm,
            ).analyze_envelope(vertical_group)

            serviceability_results = []
            if wi.serviceability_limits:
                criteria = DeflectionCriteriaSet(criteria_id=f"{wi.workflow_id}_sls", limits=wi.serviceability_limits)
                serviceability_results = criteria.check_moving_deflection_envelope(deflection_env)

            vertical_stress = ElasticVerticalBendingStressAnalyzer(gross).stress_from_moving_envelope_result(vertical_env)

            representative_offset = vertical_env.max_moment_offset_x_mm if vertical_env.max_moment_offset_x_mm is not None else 0.0
            representative_lateral_group = lateral_group.translated(representative_offset)
            warnings.append(
                "Lateral wheel group translated to representative vertical critical offset for lateral analysis."
            )
            metadata["lateral_position_assumption"] = "representative vertical max-moment offset used for lateral wheel group"
            lateral_analysis = SimpleSpanRunwayBeamLateralAnalyzer(span_internal_mm=wi.span_internal_mm).analyze(representative_lateral_group)
            lateral_stress = ElasticLateralBendingStressAnalyzer(gross).stress_from_lateral_analysis_result(lateral_analysis)

            biaxial_analyzer = ElasticBiaxialStressAnalyzer(gross)
            if vertical_stress.x_internal_mm is not None and lateral_stress.x_internal_mm is not None and vertical_stress.x_internal_mm == lateral_stress.x_internal_mm:
                biaxial = biaxial_analyzer.stress_from_vertical_and_lateral_results(vertical_stress, lateral_stress)
            else:
                warnings.append("Biaxial stress uses representative same-section simplification from separate moment peaks.")
                metadata["biaxial_combination_assumption"] = "combined from independent peak vertical/lateral moments"
                biaxial = biaxial_analyzer.stress_from_moments(
                    vertical_moment_Nmm=vertical_env.max_moment_Nmm,
                    lateral_moment_Nmm=lateral_analysis.max_lateral_moment_Nmm,
                )

            stress_results = []
            if wi.stress_limits:
                stress_criteria = StressCriteriaSet(criteria_id=f"{wi.workflow_id}_stress", limits=wi.stress_limits)
                stress_results = stress_criteria.check_biaxial_stress_result(biaxial)

            torsional_group = None
            if wi.rail_eccentricity_model is not None:
                combined_group = CraneWheelGroup(
                    group_id=f"{wi.workflow_id}_representative_vertical_plus_lateral",
                    wheels=[
                        WheelLoad(
                            wheel_id=f"{v.wheel_id}_VL",
                            position_x_internal_mm=v.position_x_internal_mm,
                            vertical_force_internal_N=v.vertical_force_internal_N,
                            lateral_force_internal_N=l.lateral_force_internal_N,
                        )
                        for v, l in zip(vertical_group.wheels, representative_lateral_group.wheels)
                    ],
                )
                torsional_group = wi.rail_eccentricity_model.torsional_group_from_wheel_group(combined_group)

            summary = CraneRunwayDemandSummaryBuilder.build_basic_summary(
                summary_id=wi.workflow_id,
                span_internal_mm=wi.span_internal_mm,
                section_id=getattr(wi.section, "section_id", None),
                load_model_id=wi.crane_load_model.crane_id,
                gross_properties=gross,
                vertical_envelope=vertical_env,
                deflection_envelope=deflection_env,
                lateral_analysis_result=lateral_analysis,
                biaxial_stress_result=biaxial,
                torsional_load_group=torsional_group,
                serviceability_results=serviceability_results,
                stress_utilization_results=stress_results,
                warnings=warnings,
                metadata=metadata,
            )
            summary.envelope_curves = envelope_curves
            summary.vertical_stress_result = vertical_stress
            summary.lateral_stress_result = lateral_stress

            formatter = CraneRunwayDemandSummaryFormatter()
            return CraneRunwayWorkflowResult(
                workflow_id=wi.workflow_id,
                summary=summary,
                text_report=formatter.format_text(summary),
                markdown_report=formatter.format_markdown(summary),
                metadata={"nominal_wheel_group_id": nominal_group.group_id},
            )
        except CraneRunwayWorkflowError:
            raise
        except Exception as exc:
            raise CraneRunwayWorkflowExecutionError(f"Workflow '{self.workflow_input.workflow_id}' failed: {exc}") from exc
