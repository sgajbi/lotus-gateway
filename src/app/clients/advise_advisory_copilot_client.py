from __future__ import annotations

from typing import Any


class AdviseAdvisoryCopilotClientMixin:
    async def create_advisory_copilot_evidence_packet(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/copilot/evidence-packets",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.copilot.evidence-packets.create",
        )

    async def create_advisory_copilot_evidence_packet_from_proposal_version(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/copilot/evidence-packets/from-proposal-version",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.copilot.evidence-packets.from-proposal-version",
        )

    async def get_advisory_copilot_evidence_packet(
        self,
        *,
        evidence_packet_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/copilot/evidence-packets/{evidence_packet_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.copilot.evidence-packets.get",
        )

    async def run_advisory_copilot_action(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/copilot/actions",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.copilot.actions.run",
        )

    async def get_advisory_copilot_run(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/copilot/actions/{run_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.copilot.actions.get",
        )

    async def review_advisory_copilot_run(
        self,
        *,
        run_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/copilot/actions/{run_id}/reviews",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.copilot.actions.review",
        )

    async def get_advisory_copilot_supportability(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/copilot/supportability",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.copilot.supportability",
        )

    async def list_advisory_copilot_proposal_version_runs(
        self,
        *,
        proposal_id: str,
        version_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_id}/copilot-runs",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="advise.advisory.copilot.proposal-version-runs.list",
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

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
