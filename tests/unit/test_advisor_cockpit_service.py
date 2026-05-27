import pytest
from fastapi import HTTPException

from app.services.advisor_cockpit_service import AdvisorCockpitService


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.status = 200
        self.payload: dict[str, object] = {
            "items": [
                {
                    "action_item_id": "cockpit_action_001",
                    "status": "PENDING_REVIEW",
                    "priority": "HIGH",
                    "owner_role": "ADVISOR",
                    "unsupported_capabilities": ["CLIENT_READY_PUBLICATION"],
                }
            ],
            "supportability": {
                "gateway_posture": "SUPPORTED_BY_LOTUS_GATEWAY_RFC0026",
                "workbench_posture": "CANONICAL_WORKBENCH_PROOF_PASSED_RFC0026",
                "client_ready_publication": "BLOCKED",
            },
        }

    async def list_advisor_cockpit_actions(
        self,
        *,
        params: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "list_advisor_cockpit_actions",
                {"params": params, "correlation_id": correlation_id},
            )
        )
        return self.status, self.payload

    async def acknowledge_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        body: dict[str, object],
        params: dict[str, object],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "acknowledge_advisor_cockpit_action",
                {
                    "action_item_id": action_item_id,
                    "body": body,
                    "params": params,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload


@pytest.mark.asyncio
async def test_advisor_cockpit_service_preserves_advise_owned_action_posture() -> None:
    advise_client = _FakeAdviseClient()
    service = AdvisorCockpitService(advise_client=advise_client)  # type: ignore[arg-type]

    response = await service.list_actions(
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "advisor_id": "advisor_sg_001",
            "role": "ADVISOR",
        },
        correlation_id="corr-cockpit-list",
    )

    assert response.correlation_id == "corr-cockpit-list"
    assert response.data == advise_client.payload
    assert response.data["supportability"]["client_ready_publication"] == "BLOCKED"
    assert advise_client.calls == [
        (
            "list_advisor_cockpit_actions",
            {
                "params": {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "advisor_id": "advisor_sg_001",
                    "role": "ADVISOR",
                },
                "correlation_id": "corr-cockpit-list",
            },
        )
    ]


@pytest.mark.asyncio
async def test_advisor_cockpit_service_propagates_acknowledgement_conflict() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.status = 409
    advise_client.payload = {"detail": "ADVISOR_COCKPIT_ACKNOWLEDGEMENT_IDEMPOTENCY_CONFLICT"}
    service = AdvisorCockpitService(advise_client=advise_client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc:
        await service.acknowledge_action(
            action_item_id="cockpit_action_001",
            body={"action_item_version": 1, "acknowledged_by": "advisor_sg_001"},
            params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
            idempotency_key="idem-cockpit-ack",
            correlation_id="corr-cockpit-ack",
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == {"detail": "ADVISOR_COCKPIT_ACKNOWLEDGEMENT_IDEMPOTENCY_CONFLICT"}
    assert advise_client.calls == [
        (
            "acknowledge_advisor_cockpit_action",
            {
                "action_item_id": "cockpit_action_001",
                "body": {"action_item_version": 1, "acknowledged_by": "advisor_sg_001"},
                "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
                "idempotency_key": "idem-cockpit-ack",
                "correlation_id": "corr-cockpit-ack",
            },
        )
    ]
