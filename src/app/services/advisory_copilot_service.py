from typing import Any

from app.contracts.advisory_copilot import AdvisoryCopilotEnvelopeResponse
from app.services.advisory_copilot_client_protocols import AdvisoryCopilotClient
from app.services.upstream_envelope import (
    ProductSafeServiceErrorConfig,
    build_gateway_envelope,
    raise_configured_product_safe_service_error,
)

ADVISORY_COPILOT_ERROR_CONFIG = ProductSafeServiceErrorConfig(
    source_service="lotus-advise",
    error_code="ADVISE_ADVISORY_COPILOT_UPSTREAM_ERROR",
    default_detail="lotus-advise advisory copilot request failed.",
)


class AdvisoryCopilotService:
    def __init__(self, advise_client: AdvisoryCopilotClient):
        self._advise_client = advise_client

    async def create_evidence_packet(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.create_advisory_copilot_evidence_packet(
            body=self._upstream_body(body),
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def create_evidence_packet_from_proposal_version(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.create_advisory_copilot_evidence_packet_from_proposal_version(
            body=self._upstream_body(body),
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_evidence_packet(
        self,
        *,
        evidence_packet_id: str,
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_advisory_copilot_evidence_packet(
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
        upstream_status, upstream_payload = await self._advise_client.run_advisory_copilot_action(
            body=self._upstream_body(body),
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_run(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_advisory_copilot_run(
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
        upstream_status, upstream_payload = await self._advise_client.review_advisory_copilot_run(
            run_id=run_id,
            body=self._upstream_body(body),
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_supportability(
        self,
        *,
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_advisory_copilot_supportability(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def list_proposal_version_runs(
        self,
        *,
        proposal_id: str,
        version_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.list_advisory_copilot_proposal_version_runs(
            proposal_id=proposal_id,
            version_id=version_id,
            params=params,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    def _envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> AdvisoryCopilotEnvelopeResponse:
        return build_gateway_envelope(
            AdvisoryCopilotEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise_configured_product_safe_service_error(
            upstream_status,
            upstream_payload,
            config=ADVISORY_COPILOT_ERROR_CONFIG,
        )

    def _upstream_body(self, body: dict[str, Any]) -> dict[str, Any]:
        inner_body = body.get("body")
        if isinstance(inner_body, dict):
            return inner_body
        return body
