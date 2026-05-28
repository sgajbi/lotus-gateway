from __future__ import annotations

from typing import Any

import pytest

from app.services.advisory_copilot_service import AdvisoryCopilotService


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.payload: dict[str, Any] = {"run": {"review_posture": "REVIEW_REQUIRED"}}
        self.status = 200
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def create_copilot_evidence_packet(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(("create_packet", {"body": body, "correlation_id": correlation_id}))
        return self.status, self.payload

    async def run_copilot_action(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        self.calls.append(
            (
                "run_action",
                {
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def review_copilot_run(self, run_id, body, idempotency_key, correlation_id):  # noqa: ANN001
        self.calls.append(
            (
                "review_run",
                {
                    "run_id": run_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def get_copilot_supportability(self, correlation_id):  # noqa: ANN001
        self.calls.append(("supportability", {"correlation_id": correlation_id}))
        return self.status, self.payload


@pytest.mark.asyncio
async def test_advisory_copilot_service_preserves_advise_owned_action_payload() -> None:
    advise_client = _FakeAdviseClient()
    service = AdvisoryCopilotService(advise_client=advise_client)  # type: ignore[arg-type]

    response = await service.run_action(
        body={"evidence_packet_id": "copilot_packet_pb_sg_001"},
        idempotency_key="idem-copilot-action",
        correlation_id="corr-copilot-action",
    )

    assert response.correlation_id == "corr-copilot-action"
    assert response.data == advise_client.payload
    assert advise_client.calls == [
        (
            "run_action",
            {
                "body": {"evidence_packet_id": "copilot_packet_pb_sg_001"},
                "idempotency_key": "idem-copilot-action",
                "correlation_id": "corr-copilot-action",
            },
        )
    ]


@pytest.mark.asyncio
async def test_advisory_copilot_service_propagates_review_conflict() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.status = 409
    advise_client.payload = {"detail": "COPILOT_RUN_REVIEW_POSTURE_TERMINAL"}
    service = AdvisoryCopilotService(advise_client=advise_client)  # type: ignore[arg-type]

    with pytest.raises(Exception) as exc:
        await service.review_run(
            run_id="copilot_run_001",
            body={"action": "REJECT"},
            idempotency_key="idem-copilot-review",
            correlation_id="corr-copilot-review",
        )

    assert getattr(exc.value, "status_code") == 409
    assert advise_client.calls[0] == (
        "review_run",
        {
            "run_id": "copilot_run_001",
            "body": {"action": "REJECT"},
            "idempotency_key": "idem-copilot-review",
            "correlation_id": "corr-copilot-review",
        },
    )
