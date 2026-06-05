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

    def _response(self, method: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        self.calls.append((method, payload))
        return self.status, self.payload

    async def list_policy_packs(self, *, correlation_id: str) -> tuple[int, dict[str, object]]:
        return self._response("list_policy_packs", {"correlation_id": correlation_id})

    async def get_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "get_policy_pack_version",
            {
                "policy_pack_id": policy_pack_id,
                "policy_version": policy_version,
                "correlation_id": correlation_id,
            },
        )

    async def validate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, object],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "validate_policy_pack_version",
            {
                "policy_pack_id": policy_pack_id,
                "policy_version": policy_version,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )

    async def activate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, object],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "activate_policy_pack_version",
            {
                "policy_pack_id": policy_pack_id,
                "policy_version": policy_version,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )

    async def create_policy_evaluation(
        self,
        *,
        proposal_id: str,
        proposal_version_id: str,
        body: dict[str, object],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "create_policy_evaluation",
            {
                "proposal_id": proposal_id,
                "proposal_version_id": proposal_version_id,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )

    async def get_policy_review_queue(
        self,
        *,
        evaluation_status: str | None,
        portfolio_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "get_policy_review_queue",
            {
                "evaluation_status": evaluation_status,
                "portfolio_id": portfolio_id,
                "correlation_id": correlation_id,
            },
        )

    async def get_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "get_policy_evaluation",
            {"evaluation_id": evaluation_id, "correlation_id": correlation_id},
        )

    async def replay_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "replay_policy_evaluation",
            {"evaluation_id": evaluation_id, "body": body, "correlation_id": correlation_id},
        )

    async def record_policy_evaluation_event(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "record_policy_evaluation_event",
            {
                "evaluation_id": evaluation_id,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )

    async def get_policy_evaluation_lineage(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "get_policy_evaluation_lineage",
            {"evaluation_id": evaluation_id, "correlation_id": correlation_id},
        )

    async def get_policy_sign_off_package(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "get_policy_sign_off_package",
            {"evaluation_id": evaluation_id, "correlation_id": correlation_id},
        )

    async def get_policy_evaluation_workflow(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "get_policy_evaluation_workflow",
            {"evaluation_id": evaluation_id, "correlation_id": correlation_id},
        )

    async def request_policy_ai_evidence(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "request_policy_ai_evidence",
            {
                "evaluation_id": evaluation_id,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )

    async def record_policy_sign_off_decision(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "record_policy_sign_off_decision",
            {
                "evaluation_id": evaluation_id,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )

    async def request_policy_report_package(
        self,
        *,
        evaluation_id: str,
        body: dict[str, object],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        return self._response(
            "request_policy_report_package",
            {
                "evaluation_id": evaluation_id,
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            },
        )


@pytest.mark.asyncio
async def test_policy_service_preserves_source_owned_policy_posture() -> None:
    advise_client = _FakeAdviseClient()
    service = AdvisoryPolicyService(advise_client=advise_client)

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
async def test_policy_service_maps_advise_rejections_to_product_safe_detail() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.status = 409
    advise_client.payload = {
        "detail": {
            "reason": "client_ready_blocked",
            "blockers": ["requires_supervisory_review"],
        }
    }
    service = AdvisoryPolicyService(advise_client=advise_client)

    with pytest.raises(HTTPException) as exc:
        await service.record_policy_sign_off_decision(
            evaluation_id="pev_001",
            body={"decision": "APPROVE", "decided_by": "compliance_1"},
            idempotency_key=None,
            correlation_id="corr-policy-signoff",
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 409,
        "error_code": "ADVISE_POLICY_UPSTREAM_ERROR",
        "detail": "client_ready_blocked",
    }
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
