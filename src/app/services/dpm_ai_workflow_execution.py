"""Validate lotus-ai workflow execution before exposing it through DPM routes."""

from dataclasses import dataclass
from typing import Any, NoReturn

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution


@dataclass(frozen=True, slots=True)
class DpmAiWorkflowExecutionExpectation:
    """Source identities expected for one governed DPM workflow handoff."""

    pack_id: str
    workflow_surface: str
    pack_version: str = "v1"
    workflow_authority_owner: str = "lotus-manage"


DPM_PROOF_PACK_PM_MEMO_EXECUTION = DpmAiWorkflowExecutionExpectation(
    pack_id="dpm_pm_memo.pack",
    workflow_surface="dpm-proof-pack-ai-evidence",
)
DPM_WAVE_PM_MEMO_EXECUTION = DpmAiWorkflowExecutionExpectation(
    pack_id="dpm_wave_pm_memo.pack",
    workflow_surface="dpm-wave-ai-evidence",
)
DPM_OPERATIONS_HANDOFF_EXECUTION = DpmAiWorkflowExecutionExpectation(
    pack_id="dpm_operations_handoff_summary.pack",
    workflow_surface="dpm-operations-handoff-ai-evidence",
)
DPM_EXCEPTION_SUMMARY_EXECUTION = DpmAiWorkflowExecutionExpectation(
    pack_id="dpm_exception_summary.pack",
    workflow_surface="dpm-exception-summary-ai-evidence",
)
DPM_OUTCOME_REVIEW_NARRATIVE_EXECUTION = DpmAiWorkflowExecutionExpectation(
    pack_id="outcome_review_narrative.pack",
    workflow_surface="dpm-outcome-review-ai-evidence",
)
DPM_PM_OPERATING_QUALITY_EXECUTION = DpmAiWorkflowExecutionExpectation(
    pack_id="pm_quality_summary.pack",
    workflow_surface="dpm-pm-quality-ai-evidence",
)


def validate_dpm_ai_workflow_execution(
    payload: dict[str, Any],
    *,
    upstream_status: int,
    correlation_id: str,
    expectation: DpmAiWorkflowExecutionExpectation,
) -> DpmAiWorkflowExecution:
    """Return a safe typed projection or fail closed on source-contract drift."""

    try:
        execution = DpmAiWorkflowExecution.model_validate(payload)
    except ValidationError:
        _raise_invalid_contract(upstream_status)

    run = execution.workflow_pack_run
    audit = execution.execution.audit
    if (
        execution.eligibility.allowed is not True
        or audit.authorization.allowed is not True
        or audit.authorization.caller_identity_bound is not True
        or run.pack_id != expectation.pack_id
        or run.pack_version != expectation.pack_version
        or run.registration_ref != f"{expectation.pack_id}@{expectation.pack_version}"
        or run.caller_app != "lotus-gateway"
        or run.correlation_id != correlation_id
        or run.workflow_surface != expectation.workflow_surface
        or run.workflow_authority_owner != expectation.workflow_authority_owner
        or audit.authorization.caller_app != "lotus-gateway"
        or audit.authorization.authenticated_caller_app != "lotus-gateway"
    ):
        _raise_invalid_contract(upstream_status)
    return execution


def _raise_invalid_contract(upstream_status: int) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": "lotus-ai",
            "upstream_status": upstream_status,
            "error_code": "AI_WORKFLOW_EXECUTION_CONTRACT_INVALID",
            "detail": "AI workflow output could not be safely verified.",
        },
    )
