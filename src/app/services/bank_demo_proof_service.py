from typing import Any

from fastapi import HTTPException, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.bank_demo_proof import BankDemoProofEnvelopeResponse


class BankDemoProofService:
    def __init__(self, advise_client: AdviseClient):
        self._advise_client = advise_client

    async def get_scenario_contract(self, *, correlation_id: str) -> BankDemoProofEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_bank_demo_proof_scenario_contract(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, upstream_payload=upstream_payload)

    async def get_supported_claim_register(
        self, *, correlation_id: str
    ) -> BankDemoProofEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_bank_demo_supported_claim_register(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, upstream_payload=upstream_payload)

    async def build_proof_pack(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> BankDemoProofEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.build_bank_demo_proof_pack(
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, upstream_payload=upstream_payload)

    def _envelope(
        self,
        *,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> BankDemoProofEnvelopeResponse:
        return BankDemoProofEnvelopeResponse(
            correlationId=correlation_id,
            contractVersion=settings.contract_version,
            data=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(status_code=upstream_status, detail=upstream_payload)
