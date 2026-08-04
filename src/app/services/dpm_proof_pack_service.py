from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.dpm_proof_packs import (
    DpmProofPackErrorDetail,
    DpmProofPackGatewayResponse,
    DpmProofPackMarkdownResponse,
    DpmProofPackMemoGatewayResponse,
    DpmProofPackMemoRequest,
)
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmProofPackClient
from app.services.dpm_proof_pack_ai_handoff import (
    ProofPackAiEvidenceInput,
    build_proof_pack_pm_memo_request,
    build_proof_pack_pm_memo_response,
    execute_proof_pack_pm_memo_workflow,
)
from app.services.dpm_proof_pack_supportability import build_dpm_proof_pack_supportability
from app.services.lotus_ai_workflow import require_lotus_ai_client
from app.services.upstream_envelope import (
    build_product_safe_upstream_status_gateway_envelope,
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
        ai_evidence_input = await self._load_proof_pack_ai_evidence_input(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        memo_request = build_proof_pack_pm_memo_request(request)
        ai_status, ai_payload = await execute_proof_pack_pm_memo_workflow(
            lotus_ai_client=lotus_ai_client,
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
            ai_evidence_input=ai_evidence_input,
            memo_request=memo_request,
        )

        return build_proof_pack_pm_memo_response(
            correlation_id=correlation_id,
            ai_evidence_input=ai_evidence_input,
            memo_request=memo_request,
            ai_upstream_status=ai_status,
            data=ai_payload,
        )

    async def _load_proof_pack_ai_evidence_input(
        self,
        *,
        proof_pack_id: str,
        correlation_id: str,
    ) -> ProofPackAiEvidenceInput:
        manage_status, manage_payload = await self._dpm_client.get_proof_pack_ai_evidence_input(
            proof_pack_id=proof_pack_id,
            correlation_id=correlation_id,
        )
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            _raise_manage_upstream_error(manage_status, manage_payload)
        return ProofPackAiEvidenceInput(
            upstream_status=manage_status,
            payload=manage_payload,
            supportability=build_dpm_proof_pack_supportability(manage_payload),
        )

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmProofPackGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmProofPackGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            upstream_payload=upstream_payload,
            supportability=build_dpm_proof_pack_supportability(upstream_payload),
            error_model=DpmProofPackErrorDetail,
            error_code="MANAGE_PROOF_PACK_UPSTREAM_ERROR",
            default_detail="lotus-manage proof-pack request failed",
        )


def _raise_manage_upstream_error(upstream_status: int, payload: dict[str, Any]) -> None:
    raise_product_safe_upstream_error(
        upstream_status,
        payload,
        error_model=DpmProofPackErrorDetail,
        error_code="MANAGE_PROOF_PACK_UPSTREAM_ERROR",
        default_detail="lotus-manage proof-pack request failed",
    )
