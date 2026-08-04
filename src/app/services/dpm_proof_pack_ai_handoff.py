"""Compose the governed proof-pack PM memo handoff to lotus-ai."""

from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution
from app.contracts.dpm_proof_packs import (
    DpmProofPackMemoGatewayResponse,
    DpmProofPackMemoRequest,
    DpmProofPackSupportability,
)
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_ai_workflow_execution import (
    DPM_PROOF_PACK_PM_MEMO_EXECUTION,
    validate_dpm_ai_workflow_execution,
)
from app.services.lotus_ai_workflow import build_workflow_pack_task_request
from app.services.upstream_envelope import raise_product_safe_service_error

_BLOCKED_ACTIONS = [
    "place_orders",
    "approve_rebalance",
    "override_controls",
    "invent_missing_evidence",
    "contact_client",
]
_UNSUPPORTED_CLAIMS = [
    "client_contact",
    "trade_approval",
    "portfolio_manager_scoring",
    "execution_instruction",
]


@dataclass(frozen=True)
class ProofPackAiEvidenceInput:
    """Manage-owned input and posture for a proof-pack AI handoff."""

    upstream_status: int
    payload: dict[str, Any]
    supportability: DpmProofPackSupportability


def build_proof_pack_pm_memo_request(
    request: DpmProofPackMemoRequest,
) -> dict[str, object]:
    """Return the bounded business request passed to the governed task."""

    return {
        "requested_outputs": request.requested_outputs,
        "audience": request.audience,
    }


async def execute_proof_pack_pm_memo_workflow(
    *,
    lotus_ai_client: LotusAiWorkflowClient,
    proof_pack_id: str,
    correlation_id: str,
    ai_evidence_input: ProofPackAiEvidenceInput,
    memo_request: dict[str, object],
) -> tuple[int, DpmAiWorkflowExecution]:
    """Execute and validate the proof-pack PM memo workflow."""

    ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
        pack_id="dpm_pm_memo.pack",
        version="v1",
        environment="DEVELOPMENT",
        caller_identity_class="INTERNAL_SERVICE",
        workflow_surface="dpm-proof-pack-ai-evidence",
        task_request=build_workflow_pack_task_request(
            correlation_id=correlation_id,
            summary=(
                "Generate review-gated proof-pack PM memo from bounded AI evidence "
                f"for {proof_pack_id}."
            ),
            payload=_task_payload(ai_evidence_input, memo_request),
            source_refs=_source_refs(ai_evidence_input.payload, proof_pack_id),
        ),
        correlation_id=correlation_id,
    )
    if ai_status >= status.HTTP_400_BAD_REQUEST:
        raise_product_safe_service_error(
            ai_status,
            ai_payload,
            source_service="lotus-ai",
            error_code="AI_PROOF_PACK_PM_MEMO_UPSTREAM_ERROR",
            default_detail="lotus-ai proof-pack PM memo request failed",
        )
    return ai_status, validate_dpm_ai_workflow_execution(
        ai_payload,
        upstream_status=ai_status,
        correlation_id=correlation_id,
        expectation=DPM_PROOF_PACK_PM_MEMO_EXECUTION,
    )


def build_proof_pack_pm_memo_response(
    *,
    correlation_id: str,
    ai_evidence_input: ProofPackAiEvidenceInput,
    memo_request: dict[str, object],
    ai_upstream_status: int,
    data: DpmAiWorkflowExecution,
) -> DpmProofPackMemoGatewayResponse:
    """Return the Workbench-facing proof-pack memo execution envelope."""

    return DpmProofPackMemoGatewayResponse(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        manage_upstream_status=ai_evidence_input.upstream_status,
        ai_upstream_status=ai_upstream_status,
        supportability=ai_evidence_input.supportability,
        ai_evidence_input=ai_evidence_input.payload,
        memo_request=memo_request,
        data=data,
    )


def _task_payload(
    ai_evidence_input: ProofPackAiEvidenceInput,
    memo_request: dict[str, object],
) -> dict[str, object]:
    return {
        "ai_evidence_input": ai_evidence_input.payload,
        "memo_request": memo_request,
        "supportability": {
            "source_state": ai_evidence_input.supportability.state,
            "reason_codes": ai_evidence_input.supportability.reason_codes,
            "blocked_actions": _BLOCKED_ACTIONS,
            "requires_human_review": True,
            "unsupported_claims": _UNSUPPORTED_CLAIMS,
        },
    }


def _source_refs(payload: dict[str, Any], proof_pack_id: str) -> list[str]:
    source_refs: list[str] = []
    for key in ("source_refs", "sourceRefs"):
        value = payload.get(key)
        if isinstance(value, list):
            source_refs.extend(str(item) for item in value if item)

    evidence_ref = payload.get("evidence_ref") or payload.get("ai_evidence_input_ref")
    if evidence_ref:
        source_refs.append(f"lotus-manage:proof-pack-ai-evidence:{evidence_ref}")
    payload_proof_pack_id = payload.get("proof_pack_id")
    if payload_proof_pack_id:
        source_refs.append(f"lotus-manage:proof-pack:{payload_proof_pack_id}")
    source_refs.append(f"lotus-manage:proof-pack-ai-evidence:{proof_pack_id}")
    return sorted(set(source_refs))
