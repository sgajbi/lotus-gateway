from typing import Any

from fastapi import HTTPException, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisory_workspaces import AdvisoryWorkspaceEnvelopeResponse


class AdvisoryWorkspaceService:
    def __init__(self, advise_client: AdviseClient):
        self._advise_client = advise_client

    async def create_workspace(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_advisory_workspace(
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_workspace(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_advisory_workspace(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def apply_draft_action(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.apply_advisory_workspace_draft_action(
            workspace_id=workspace_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def evaluate_workspace(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.evaluate_advisory_workspace(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def save_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.save_advisory_workspace(
            workspace_id=workspace_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def list_saved_versions(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.list_advisory_workspace_saved_versions(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_saved_version_replay_evidence(
        self,
        workspace_id: str,
        workspace_version_id: str,
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_advisory_workspace_saved_version_replay_evidence(
            workspace_id=workspace_id,
            workspace_version_id=workspace_version_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def resume_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.resume_advisory_workspace(
            workspace_id=workspace_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def compare_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.compare_advisory_workspace(
            workspace_id=workspace_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def request_rationale(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.request_advisory_workspace_rationale(
            workspace_id=workspace_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def review_rationale(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.review_advisory_workspace_rationale(
            workspace_id=workspace_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def handoff_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.handoff_advisory_workspace(
            workspace_id=workspace_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    def _envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> AdvisoryWorkspaceEnvelopeResponse:
        return AdvisoryWorkspaceEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            detail: str | dict[str, Any] = upstream_payload
            if not isinstance(detail, str):
                detail = str(detail)
            raise HTTPException(status_code=upstream_status, detail=detail)
