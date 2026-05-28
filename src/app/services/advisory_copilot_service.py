from typing import Any

from fastapi import HTTPException, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisory_copilot import AdvisoryCopilotEnvelopeResponse


class AdvisoryCopilotService:
    def __init__(self, advise_client: AdviseClient):
        self._advise_client = advise_client

    async def create_evidence_packet(
        self, *, body: dict[str, Any], correlation_id: str
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.create_copilot_evidence_packet(
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_evidence_packet(
        self, *, evidence_packet_id: str, correlation_id: str
    ) -> AdvisoryCopilotEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_copilot_evidence_packet(
            evidence_packet_id=evidence_packet_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def run_action(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.run_copilot_action(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_run(self, *, run_id: str, correlation_id: str) -> AdvisoryCopilotEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_copilot_run(
            run_id=run_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def review_run(
        self,
        *,
        run_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.review_copilot_run(
            run_id=run_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_supportability(self, *, correlation_id: str) -> AdvisoryCopilotEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_copilot_supportability(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def list_proposal_version_runs(
        self, *, proposal_id: str, version_id: str, correlation_id: str
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.list_proposal_version_copilot_runs(
            proposal_id=proposal_id,
            version_id=version_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    def _envelope(
        self, correlation_id: str, upstream_payload: dict[str, Any]
    ) -> AdvisoryCopilotEnvelopeResponse:
        return AdvisoryCopilotEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    def _raise_for_upstream_error(
        self, upstream_status: int, upstream_payload: dict[str, Any]
    ) -> None:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(status_code=upstream_status, detail=upstream_payload)
