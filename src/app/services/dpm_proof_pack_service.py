from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.dpm_proof_packs import (
    DpmProofPackErrorDetail,
    DpmProofPackGatewayResponse,
    DpmProofPackMarkdownResponse,
    DpmProofPackMemoGatewayResponse,
    DpmProofPackMemoRequest,
    DpmProofPackSupportability,
)
from app.services.lotus_ai_workflow import require_lotus_ai_client
from app.services.upstream_client_protocols import DpmProofPackClient, LotusAiWorkflowClient
from app.services.upstream_envelope import (
    build_upstream_status_gateway_envelope,
    raise_product_safe_service_error,
    raise_product_safe_upstream_error,
)


class DpmProofPackService:
    def __init__(
        self,
        dpm_client: DpmProofPackClient,
        lotus_ai_client: LotusAiWorkflowClient | None = None,
    ):
        self._dpm_client = dpm_client
        self._lotus_ai_client = lotus_ai_client

    async def generate_proof_pack(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> DpmProofPackGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.generate_proof_pack(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_proof_pack(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> DpmProofPackGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_proof_pack(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_proof_pack_markdown(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> DpmProofPackMarkdownResponse:
        (
            upstream_status,
            markdown,
            error_payload,
        ) = await self._dpm_client.get_proof_pack_markdown(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            _raise_manage_upstream_error(upstream_status, error_payload)
        return DpmProofPackMarkdownResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            proof_pack_id=proof_pack_id,
            markdown=markdown,
        )

    async def get_proof_pack_report_input(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> DpmProofPackGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_proof_pack_report_input(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_proof_pack_ai_evidence_input(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> DpmProofPackGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_proof_pack_ai_evidence_input(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def request_proof_pack_pm_memo(
        self,
        proof_pack_id: str,
        request: DpmProofPackMemoRequest,
        correlation_id: str,
    ) -> DpmProofPackMemoGatewayResponse:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)

        manage_status, manage_payload = await self._dpm_client.get_proof_pack_ai_evidence_input(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            _raise_manage_upstream_error(manage_status, manage_payload)

        supportability = _supportability_from(manage_payload)
        memo_request: dict[str, object] = {
            "requested_outputs": request.requested_outputs,
            "audience": request.audience,
        }
        task_payload = {
            "ai_evidence_input": manage_payload,
            "memo_request": memo_request,
            "supportability": {
                "source_state": supportability.state,
                "reason_codes": supportability.reason_codes,
                "blocked_actions": [
                    "place_orders",
                    "approve_rebalance",
                    "override_controls",
                    "invent_missing_evidence",
                    "contact_client",
                ],
                "requires_human_review": True,
                "unsupported_claims": [
                    "client_contact",
                    "trade_approval",
                    "portfolio_manager_scoring",
                    "execution_instruction",
                ],
            },
        }
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="dpm_pm_memo.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-proof-pack-ai-evidence",
            task_request={
                "task_id": "explain.v1",
                "input_mode": "STRUCTURED_CONTEXT",
                "caller": {
                    "caller_app": "lotus-gateway",
                    "correlation_id": correlation_id,
                },
                "context": {
                    "summary": (
                        "Generate review-gated proof-pack PM memo from bounded AI evidence "
                        f"for {proof_pack_id}."
                    ),
                    "payload": task_payload,
                    "source_refs": _proof_pack_ai_source_refs(manage_payload, proof_pack_id),
                },
                "expected_output_label": "EXPLANATION_ONLY",
            },
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

        return DpmProofPackMemoGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=manage_status,
            ai_upstream_status=ai_status,
            supportability=supportability,
            ai_evidence_input=manage_payload,
            memo_request=memo_request,
            data=ai_payload,
        )

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmProofPackGatewayResponse:
        _raise_manage_upstream_error(upstream_status, upstream_payload)
        return build_upstream_status_gateway_envelope(
            DpmProofPackGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=_supportability_from(upstream_payload),
            upstream_payload=upstream_payload,
        )


def _supportability_from(payload: dict[str, Any]) -> DpmProofPackSupportability:
    proof_pack = _proof_pack_payload(payload)
    reason_codes = _reason_codes_from_payload(payload, proof_pack)
    return DpmProofPackSupportability(
        state=_proof_pack_state(payload, proof_pack),
        proof_pack_id=_safe_str(proof_pack.get("proof_pack_id") or payload.get("proof_pack_id")),
        reason_codes=sorted(set(reason_codes)),
        section_state_counts=_section_state_counts(proof_pack),
        content_hash=_safe_str(proof_pack.get("content_hash") or payload.get("content_hash")),
        markdown_available=bool(payload.get("markdown_url") or payload.get("markdown")),
        report_input_available=bool(
            payload.get("report_input_url")
            or payload.get("report_input")
            or proof_pack.get("report_input_ref")
        ),
        ai_evidence_input_available=bool(
            payload.get("ai_evidence_input_url")
            or payload.get("ai_evidence_input")
            or proof_pack.get("ai_evidence_input_ref")
        ),
    )


def _proof_pack_payload(payload: dict[str, Any]) -> dict[str, Any]:
    proof_pack = payload.get("proof_pack")
    return proof_pack if isinstance(proof_pack, dict) else payload


def _proof_pack_state(payload: dict[str, Any], proof_pack: dict[str, Any]) -> str:
    state = (
        proof_pack.get("status")
        or proof_pack.get("state")
        or payload.get("supportability_status")
        or payload.get("supportabilityStatus")
        or payload.get("status")
        or "UNKNOWN"
    )
    return str(state)


def _reason_codes_from_payload(
    payload: dict[str, Any],
    proof_pack: dict[str, Any],
) -> list[str]:
    reason_codes = _list_of_strings(payload.get("reason_codes") or payload.get("reasonCodes") or [])
    reason_codes.extend(
        _list_of_strings(proof_pack.get("reason_codes") or proof_pack.get("reasonCodes") or [])
    )
    for section in _sections(proof_pack):
        reason_codes.extend(
            _list_of_strings(section.get("reason_codes") or section.get("reasonCodes") or [])
        )
    return reason_codes


def _section_state_counts(proof_pack: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for section in _sections(proof_pack):
        state = section.get("state") or section.get("status")
        if state is None:
            continue
        state_label = str(state)
        counts[state_label] = counts.get(state_label, 0) + 1
    return counts


def _sections(proof_pack: dict[str, Any]) -> list[dict[str, Any]]:
    sections = proof_pack.get("sections")
    if not isinstance(sections, list):
        return []
    return [section for section in sections if isinstance(section, dict)]


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _safe_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _proof_pack_ai_source_refs(payload: dict[str, Any], proof_pack_id: str) -> list[str]:
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


def _raise_manage_upstream_error(upstream_status: int, payload: dict[str, Any]) -> None:
    raise_product_safe_upstream_error(
        upstream_status,
        payload,
        error_model=DpmProofPackErrorDetail,
        error_code="MANAGE_PROOF_PACK_UPSTREAM_ERROR",
        default_detail="lotus-manage proof-pack request failed",
    )
