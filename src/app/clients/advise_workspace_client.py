from __future__ import annotations

from typing import Any


class AdviseWorkspaceClientMixin:
    async def create_advisory_workspace(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/workspaces",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.create",
        )

    async def get_advisory_workspace(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/workspaces/{workspace_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.get",
        )

    async def apply_advisory_workspace_draft_action(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/draft-actions",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.draft-action",
        )

    async def evaluate_advisory_workspace(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/evaluate",
            body={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.evaluate",
        )

    async def save_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/save",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.save",
        )

    async def list_advisory_workspace_saved_versions(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/workspaces/{workspace_id}/saved-versions",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.saved-versions.list",
        )

    async def get_advisory_workspace_saved_version_replay_evidence(
        self,
        workspace_id: str,
        workspace_version_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/workspaces/{workspace_id}/saved-versions/"
            f"{workspace_version_id}/replay-evidence",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.saved-versions.replay-evidence",
        )

    async def resume_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/resume",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.resume",
        )

    async def compare_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/compare",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.compare",
        )

    async def request_advisory_workspace_rationale(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/assistant/rationale",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.assistant.rationale",
        )

    async def review_advisory_workspace_rationale(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/assistant/rationale/review-actions",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.assistant.rationale.review-actions",
        )

    async def handoff_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/handoff",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.workspaces.handoff",
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
