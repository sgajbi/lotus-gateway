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
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> AdvisoryCopilotEnvelopeResponse:
        scoped_caller_headers = await self._resource_scoped_review_headers(
            run_id=run_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        upstream_status, upstream_payload = await self._advise_client.review_advisory_copilot_run(
            run_id=run_id,
            body=self._upstream_body(body),
            idempotency_key=idempotency_key,
            caller_headers=scoped_caller_headers,
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

    async def _resource_scoped_review_headers(
        self,
        *,
        run_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> dict[str, str]:
        if caller_headers.get("X-Authorized-Portfolio-Id") and caller_headers.get(
            "X-Authorized-Proposal-Id"
        ):
            return caller_headers

        upstream_status, upstream_payload = await self._advise_client.get_advisory_copilot_run(
            run_id=run_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        run = upstream_payload.get("run")
        if not isinstance(run, dict):
            return caller_headers

        scoped_headers = dict(caller_headers)
        if portfolio_id := self._string_field(run, "portfolio_id"):
            scoped_headers.setdefault("X-Authorized-Portfolio-Id", portfolio_id)
        if proposal_id := self._string_field(run, "proposal_id"):
            scoped_headers.setdefault("X-Authorized-Proposal-Id", proposal_id)
        return scoped_headers

    def _string_field(self, payload: dict[str, Any], field: str) -> str | None:
        value = payload.get(field)
        if not isinstance(value, str):
            return None
        stripped = value.strip()
        return stripped or None
