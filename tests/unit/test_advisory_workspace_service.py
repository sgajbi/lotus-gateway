import pytest
from fastapi import HTTPException

from app.services.advisory_workspace_service import AdvisoryWorkspaceService


class _FakeAdvisoryWorkspaceClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def create_advisory_workspace(
        self,
        *,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "create_advisory_workspace",
                {"body": body, "correlation_id": correlation_id},
            )
        )
        return 201, {"workspace_id": "aws_1", "workspace_state": "DRAFT"}

    async def get_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "get_advisory_workspace",
                {"workspace_id": workspace_id, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "workspace_state": "DRAFT"}

    async def apply_advisory_workspace_draft_action(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "apply_advisory_workspace_draft_action",
                {"workspace_id": workspace_id, "body": body, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "draft_action": body["action"]}

    async def evaluate_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "evaluate_advisory_workspace",
                {"workspace_id": workspace_id, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "evaluation_state": "SUPPORTED"}

    async def save_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "save_advisory_workspace",
                {"workspace_id": workspace_id, "body": body, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "version_id": "awv_1"}

    async def list_advisory_workspace_saved_versions(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "list_advisory_workspace_saved_versions",
                {"workspace_id": workspace_id, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "versions": [{"version_id": "awv_1"}]}

    async def get_advisory_workspace_saved_version_replay_evidence(
        self,
        *,
        workspace_id: str,
        workspace_version_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "get_advisory_workspace_saved_version_replay_evidence",
                {
                    "workspace_id": workspace_id,
                    "workspace_version_id": workspace_version_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"workspace_id": workspace_id, "replay_hash": "sha256:workspace"}

    async def resume_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "resume_advisory_workspace",
                {"workspace_id": workspace_id, "body": body, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "resumed": True}

    async def compare_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "compare_advisory_workspace",
                {"workspace_id": workspace_id, "body": body, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "comparison_state": "READY"}

    async def request_advisory_workspace_rationale(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "request_advisory_workspace_rationale",
                {"workspace_id": workspace_id, "body": body, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "rationale_state": "REQUESTED"}

    async def review_advisory_workspace_rationale(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "review_advisory_workspace_rationale",
                {"workspace_id": workspace_id, "body": body, "correlation_id": correlation_id},
            )
        )
        return 200, {"workspace_id": workspace_id, "review_state": "APPROVED"}

    async def handoff_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "handoff_advisory_workspace",
                {
                    "workspace_id": workspace_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"workspace_id": workspace_id, "handoff_state": "READY"}


class _ErrorAdvisoryWorkspaceClient(_FakeAdvisoryWorkspaceClient):
    async def get_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        _ = workspace_id, correlation_id
        return 409, {
            "detail": "WORKSPACE_LOCKED",
            "workspace_id": "aws_sensitive",
            "client_name": "Sensitive Client",
        }


@pytest.mark.asyncio
async def test_advisory_workspace_service_preserves_source_payload() -> None:
    client = _FakeAdvisoryWorkspaceClient()
    service = AdvisoryWorkspaceService(advise_client=client)

    created = await service.create_workspace(
        body={"created_by": "advisor_1"},
        correlation_id="corr_workspace_create",
    )
    evaluated = await service.evaluate_workspace(
        workspace_id="aws_1",
        correlation_id="corr_workspace_eval",
    )

    assert created.correlation_id == "corr_workspace_create"
    assert created.data == {"workspace_id": "aws_1", "workspace_state": "DRAFT"}
    assert evaluated.data["evaluation_state"] == "SUPPORTED"
    assert [name for name, _ in client.calls] == [
        "create_advisory_workspace",
        "evaluate_advisory_workspace",
    ]


@pytest.mark.asyncio
async def test_advisory_workspace_handoff_forwards_idempotency_key() -> None:
    client = _FakeAdvisoryWorkspaceClient()
    service = AdvisoryWorkspaceService(advise_client=client)

    result = await service.handoff_workspace(
        workspace_id="aws_1",
        body={"handoff_type": "PROPOSAL"},
        idempotency_key="idem-workspace-handoff-1",
        correlation_id="corr_workspace_handoff",
    )

    assert result.data["handoff_state"] == "READY"
    assert client.calls[0][0] == "handoff_advisory_workspace"
    assert client.calls[0][1]["idempotency_key"] == "idem-workspace-handoff-1"


@pytest.mark.asyncio
async def test_advisory_workspace_upstream_error_is_product_safe() -> None:
    service = AdvisoryWorkspaceService(advise_client=_ErrorAdvisoryWorkspaceClient())

    with pytest.raises(HTTPException) as exc_info:
        await service.get_workspace(
            workspace_id="aws_1",
            correlation_id="corr_workspace_locked",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 409,
        "error_code": "ADVISE_WORKSPACE_UPSTREAM_ERROR",
        "detail": "WORKSPACE_LOCKED",
    }
