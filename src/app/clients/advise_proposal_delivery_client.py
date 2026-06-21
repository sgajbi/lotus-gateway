from __future__ import annotations

from typing import Any

from app.clients.advise_proposal_memo_client import AdviseProposalMemoClientMixin


class AdviseProposalDeliveryClientMixin(AdviseProposalMemoClientMixin):
    async def create_report_request(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/report-requests",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.report-requests.create",
        )

    async def create_execution_handoff(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/execution-handoffs",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.execution-handoffs.create",
        )

    async def get_delivery_summary(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/delivery-summary",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.delivery-summary",
        )

    async def get_delivery_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/delivery-events",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.delivery-events",
        )

    async def get_execution_status(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/execution-status",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.execution-status",
        )

    async def record_execution_update(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/execution-updates",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.execution-updates.record",
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    def _optional_idempotency_headers(
        self,
        correlation_id: str,
        idempotency_key: str | None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError
