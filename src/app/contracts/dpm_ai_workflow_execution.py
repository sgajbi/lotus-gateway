"""Typed product boundary for governed DPM workflow-pack execution evidence."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.ai_output_validation import (
    WITHHOLDING_VALIDATION_STATES,
    AiOutputValidation,
)
from app.contracts.dpm_ai_execution_audit import (
    DpmAiExecutionEvidenceBundle,
    DpmAiTaskAudit,
)
from app.contracts.dpm_ai_workflow_run import DpmAiWorkflowPackRun


class DpmAiTaskResult(BaseModel):
    """Governed structured output without raw generated message text."""

    model_config = ConfigDict(extra="ignore")

    structured_output: dict[str, object] = Field(
        description="Structured workflow output published by the governed task contract."
    )


class DpmAiTaskExecution(BaseModel):
    """Typed task execution produced by a DPM workflow pack."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["COMPLETED", "REJECTED", "FAILED"] = Field(
        description="Runtime outcome of the lotus-ai task request."
    )
    task_id: str = Field(min_length=1, description="Executed lotus-ai task id.")
    category: str = Field(min_length=1, description="Task category selected for execution.")
    output_label: str = Field(min_length=1, description="Governed output-use label.")
    result: DpmAiTaskResult = Field(description="Governed structured task result.")
    output_validation: AiOutputValidation = Field(
        description=(
            "lotus-ai's deterministic output-validation verdict, preserved so Workbench "
            "can distinguish validated output without backend knowledge."
        ),
    )
    audit: DpmAiTaskAudit = Field(description="Execution audit and provider posture.")
    evidence: DpmAiExecutionEvidenceBundle = Field(
        description="Evidence explaining how the task result was produced."
    )

    @model_validator(mode="after")
    def validate_execution_identity(self) -> Self:
        if self.task_id != self.audit.task_id:
            raise ValueError("execution and audit task ids must match")
        if self.output_label != self.audit.output_label:
            raise ValueError("execution and audit output labels must match")
        if self.output_label != self.audit.safety.output_label:
            raise ValueError("execution and safety output labels must match")
        if self.audit.authorization.task_id != self.task_id:
            raise ValueError("execution and authorization task ids must match")
        if (
            self.status == "COMPLETED"
            and self.output_validation.validation_state in WITHHOLDING_VALIDATION_STATES
        ):
            # lotus-ai withholds a rejected/unavailable-validation output whole and
            # forces a non-COMPLETED status; a completed execution claiming one is
            # source-contract contradiction, not displayable content.
            raise ValueError("a completed execution cannot carry a withholding verdict")
        return self


class DpmAiWorkflowEligibility(BaseModel):
    """Eligibility decision that preceded workflow-pack execution."""

    model_config = ConfigDict(extra="ignore")

    service: Literal["lotus-ai"] = Field(description="Eligibility authority service.")
    version: str = Field(min_length=1, description="lotus-ai service version.")
    pack_id: str = Field(min_length=1, description="Evaluated workflow-pack identifier.")
    requested_version: str = Field(
        min_length=1,
        description="Evaluated workflow-pack version.",
    )
    eligibility_result: str = Field(
        min_length=1,
        description="Source-published eligibility decision.",
    )
    allowed: bool = Field(description="Whether execution was permitted.")
    evaluated_registration_ref: str | None = Field(
        default=None,
        description="Resolved workflow-pack registration reference.",
    )
    caller_app: str = Field(min_length=1, description="Caller evaluated for eligibility.")
    environment: str = Field(min_length=1, description="Environment evaluated for eligibility.")
    caller_identity_class: str = Field(
        min_length=1,
        description="Caller identity class evaluated for eligibility.",
    )
    tenant_scope_applied: bool = Field(
        description="Whether tenant-level eligibility scope was applied."
    )
    workflow_surface_applied: bool = Field(
        description="Whether workflow-surface eligibility scope was applied."
    )


class DpmAiWorkflowExecution(BaseModel):
    """Validated lotus-ai execution envelope safe for DPM product consumers."""

    model_config = ConfigDict(extra="ignore")

    service: Literal["lotus-ai"] = Field(description="Workflow execution authority service.")
    version: str = Field(min_length=1, description="lotus-ai service version.")
    eligibility: DpmAiWorkflowEligibility = Field(
        description="Eligibility decision applied before execution."
    )
    execution: DpmAiTaskExecution = Field(description="Governed task execution result.")
    workflow_pack_run: DpmAiWorkflowPackRun = Field(
        description="Workflow run, review, supportability, evidence, and lineage posture."
    )
    summary: list[str] = Field(description="Source-published summary of the execution posture.")

    @model_validator(mode="after")
    def validate_run_identity(self) -> Self:
        run = self.workflow_pack_run
        audit = self.execution.audit
        eligibility = self.eligibility
        if audit.workflow_pack_run_id != run.run_id:
            raise ValueError("audit and workflow run ids must match")
        if self.execution.task_id != run.task_id:
            raise ValueError("execution and workflow run task ids must match")
        if audit.request_id != run.request_id:
            raise ValueError("audit and workflow run request ids must match")
        if audit.stubbed != run.stubbed:
            raise ValueError("audit and workflow run stub postures must match")
        if audit.provider_mode != run.provider_mode:
            raise ValueError("audit and workflow run provider modes must match")
        if eligibility.pack_id != run.pack_id:
            raise ValueError("eligibility and workflow run pack ids must match")
        if eligibility.requested_version != run.pack_version:
            raise ValueError("eligibility and workflow run pack versions must match")
        if eligibility.caller_app != run.caller_app:
            raise ValueError("eligibility and workflow run callers must match")
        if eligibility.evaluated_registration_ref != run.registration_ref:
            raise ValueError("eligibility and workflow run registrations must match")
        if eligibility.version != self.version:
            raise ValueError("eligibility and execution service versions must match")
        structured_output_keys = self.execution.result.structured_output
        if len(run.structured_output_keys) != len(structured_output_keys) or set(
            run.structured_output_keys
        ) != set(structured_output_keys):
            raise ValueError("workflow run keys must match the structured output")
        return self
