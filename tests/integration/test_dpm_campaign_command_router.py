from typing import Any

import pytest

from app.main import app
from tests.support.dpm_caller import governed_dpm_client
from tests.support.dpm_campaign_command_fixtures import (
    STALE_CAMPAIGN_COMMAND_BODIES,
    VALID_CAMPAIGN_COMMAND_BODIES,
)

BASE_PATH = (
    "/api/v1/dpm/command-center/waves/campaign-definitions/"
    "campaign-holdings-202605/versions/2026.05"
)

VALID_ROUTES: list[tuple[str, str, dict[str, Any], str]] = [
    (
        "launch_campaign_definition",
        f"{BASE_PATH}/launch",
        VALID_CAMPAIGN_COMMAND_BODIES[0],
        "launch",
    ),
    (
        "retire_campaign_definition",
        f"{BASE_PATH}/retire",
        VALID_CAMPAIGN_COMMAND_BODIES[1],
        "retire",
    ),
    (
        "supersede_campaign_definition",
        f"{BASE_PATH}/supersede",
        VALID_CAMPAIGN_COMMAND_BODIES[2],
        "supersede",
    ),
    (
        "create_campaign_approval_decision",
        f"{BASE_PATH}/approval-decisions",
        VALID_CAMPAIGN_COMMAND_BODIES[3],
        "approval",
    ),
    (
        "create_campaign_assignment_action",
        f"{BASE_PATH}/assignment-actions",
        VALID_CAMPAIGN_COMMAND_BODIES[4],
        "assignment",
    ),
    (
        "create_campaign_assignment_task",
        f"{BASE_PATH}/assignment-tasks",
        VALID_CAMPAIGN_COMMAND_BODIES[5],
        "task",
    ),
    (
        "transition_campaign_assignment_task",
        f"{BASE_PATH}/assignment-tasks/BRC-TASK-001/transitions",
        VALID_CAMPAIGN_COMMAND_BODIES[6],
        "transition",
    ),
    (
        "create_campaign_maker_checker_control",
        f"{BASE_PATH}/maker-checker-controls",
        VALID_CAMPAIGN_COMMAND_BODIES[7],
        "maker-checker",
    ),
]


@pytest.mark.parametrize(("method_name", "path", "body", "command"), VALID_ROUTES)
def test_campaign_commands_forward_current_manage_shapes_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
    path: str,
    body: dict[str, Any],
    command: str,
) -> None:
    captured: dict[str, Any] = {}

    async def _fake_command(self: object, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        _ = self
        captured.update(kwargs)
        if command == "launch":
            return 201, {
                "wave": {"wave_id": "dwv-campaign-001", "state": "CREATED"},
                "durable": True,
                "supportability": {"supportability_state": "ready"},
                "command": command,
            }
        return 201, {"command": command, "source_ref": "manage-campaign-command-001"}

    monkeypatch.setattr(f"app.clients.dpm_client.DpmClient.{method_name}", _fake_command)

    response = governed_dpm_client(app).post(
        path,
        json={"body": body},
        headers={"X-Correlation-Id": f"corr-gateway-{command}"},
    )

    assert response.status_code == 200
    assert response.json()["upstream_status"] == 201
    assert response.json()["data"]["command"] == command
    assert captured["campaign_id"] == "campaign-holdings-202605"
    assert captured["campaign_version"] == "2026.05"
    assert captured["body"] == body
    assert captured["correlation_id"] == f"corr-gateway-{command}"
    if command == "transition":
        assert captured["task_ref"] == "BRC-TASK-001"


@pytest.mark.parametrize(
    ("method_name", "path", "body"),
    [
        (method_name, path, STALE_CAMPAIGN_COMMAND_BODIES[index])
        for index, (method_name, path, _valid_body, _command) in enumerate(VALID_ROUTES)
    ],
)
def test_stale_campaign_commands_are_rejected_before_upstream_call(
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
    path: str,
    body: dict[str, Any],
) -> None:
    async def _unexpected_upstream_call(self: object, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        _ = (self, kwargs)
        pytest.fail("invalid campaign command reached lotus-manage client")

    monkeypatch.setattr(
        f"app.clients.dpm_client.DpmClient.{method_name}", _unexpected_upstream_call
    )

    response = governed_dpm_client(app).post(
        path,
        json={"body": body},
        headers={"X-Correlation-Id": "corr-invalid-campaign-command"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]
