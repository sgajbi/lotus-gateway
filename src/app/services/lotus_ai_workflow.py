"""Shared guards and task contracts for governed lotus-ai workflow-pack handoffs."""

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.services.ai_client_protocols import LotusAiWorkflowClient

LOTUS_AI_NOT_CONFIGURED_DETAIL = "lotus-ai workflow-pack execution is not configured for Gateway."


@dataclass(frozen=True, slots=True)
class LotusAiWorkflowTaskContract:
    """Task identity and output-use boundary shared by request and response handling."""

    task_id: str
    output_label: str


DPM_EXPLANATION_TASK_CONTRACT = LotusAiWorkflowTaskContract(
    task_id="explain.v1",
    output_label="EXPLANATION_ONLY",
)


def require_lotus_ai_client(client: LotusAiWorkflowClient | None) -> LotusAiWorkflowClient:
    """Return a configured lotus-ai client or raise the standard Gateway service error."""

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=LOTUS_AI_NOT_CONFIGURED_DETAIL,
        )
    return client


def build_workflow_pack_task_request(
    *,
    correlation_id: str,
    summary: str,
    payload: dict[str, object],
    source_refs: list[str],
    task_contract: LotusAiWorkflowTaskContract = DPM_EXPLANATION_TASK_CONTRACT,
) -> dict[str, object]:
    return {
        "task_id": task_contract.task_id,
        "input_mode": "STRUCTURED_CONTEXT",
        "caller": {
            "caller_app": "lotus-gateway",
            "correlation_id": correlation_id,
        },
        "context": {
            "summary": summary,
            "payload": payload,
            "source_refs": source_refs,
        },
        "expected_output_label": task_contract.output_label,
    }
