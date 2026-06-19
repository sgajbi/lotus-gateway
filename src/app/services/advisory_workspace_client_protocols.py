from typing import Any, Protocol


class AdvisoryWorkspaceClient(Protocol):
    async def create_advisory_workspace(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def apply_advisory_workspace_draft_action(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def evaluate_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def save_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_advisory_workspace_saved_versions(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_workspace_saved_version_replay_evidence(
        self,
        *,
        workspace_id: str,
        workspace_version_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def resume_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def compare_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_advisory_workspace_rationale(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def review_advisory_workspace_rationale(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def handoff_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
