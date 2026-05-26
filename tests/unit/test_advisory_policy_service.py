import pytest
from fastapi import HTTPException

from app.services.advisory_policy_service import AdvisoryPolicyService


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.status = 200
        self.payload: dict[str, object] = {
            "evaluation_id": "pev_001",
            "client_ready": {"status": "BLOCKED", "blockers": ["requires_compliance_signoff"]},
        }

    async def request_policy_ai_evidence(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "request_policy_ai_evidence",
                {
                    "evaluation_id": evaluation_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def record_policy_sign_off_decision(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "record_policy_sign_off_decision",
                {
                    "evaluation_id": evaluation_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload


@pytest.mark.asyncio
async def test_policy_service_preserves_source_owned_policy_posture() -> None:
    advise_client = _FakeAdviseClient()
    service = AdvisoryPolicyService(advise_client=advise_client)  # type: ignore[arg-type]

    response = await service.request_policy_ai_evidence(
        evaluation_id="pev_001",
        body={"requested_by": "advisor_1", "purpose": "client draft support"},
        idempotency_key="idem-ai-evidence",
        correlation_id="corr-policy-ai",
    )

    assert response.correlation_id == "corr-policy-ai"
    assert response.data == advise_client.payload
    assert response.data["client_ready"] == {
        "status": "BLOCKED",
        "blockers": ["requires_compliance_signoff"],
    }
    assert advise_client.calls == [
        (
            "request_policy_ai_evidence",
            {
                "evaluation_id": "pev_001",
                "body": {"requested_by": "advisor_1", "purpose": "client draft support"},
                "idempotency_key": "idem-ai-evidence",
                "correlation_id": "corr-policy-ai",
            },
        )
    ]


@pytest.mark.asyncio
async def test_policy_service_propagates_advise_rejections_without_rewriting() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.status = 409
    advise_client.payload = {
        "detail": {
            "reason": "client_ready_blocked",
            "blockers": ["requires_supervisory_review"],
        }
    }
    service = AdvisoryPolicyService(advise_client=advise_client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc:
        await service.record_policy_sign_off_decision(
            evaluation_id="pev_001",
            body={"decision": "APPROVE", "decided_by": "compliance_1"},
            idempotency_key=None,
            correlation_id="corr-policy-signoff",
        )

    assert exc.value.status_code == 409
    assert "client_ready_blocked" in str(exc.value.detail)
    assert advise_client.calls == [
        (
            "record_policy_sign_off_decision",
            {
                "evaluation_id": "pev_001",
                "body": {"decision": "APPROVE", "decided_by": "compliance_1"},
                "idempotency_key": None,
                "correlation_id": "corr-policy-signoff",
            },
        )
    ]
