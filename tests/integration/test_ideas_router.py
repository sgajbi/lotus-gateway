import pytest
from fastapi.testclient import TestClient

from app.contracts.idea_examples import IDEA_CANDIDATE_DETAIL_EXAMPLE, IDEA_REVIEW_QUEUE_EXAMPLE
from app.main import app


def _headers() -> dict[str, str]:
    return {
        "X-Caller-Subject": "advisor-123",
        "X-Caller-Roles": "advisor",
        "X-Caller-Capabilities": "idea.review.queue.read,idea.candidate.detail.read",
        "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
        "X-Caller-Book-Ids": "book-advisor-001",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
        "X-Caller-Client-Ids": "client-001",
        "X-Correlation-Id": "corr-idea-router",
    }


def test_idea_review_queue_route_preserves_source_payload_and_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _queue(self, *, evaluated_at_utc, caller_headers, correlation_id):
        captured["evaluated_at_utc"] = evaluated_at_utc
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        payload = dict(IDEA_REVIEW_QUEUE_EXAMPLE)
        payload["sourceAuthority"] = "lotus-idea"
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_advisor_review_queue",
        _queue,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/review-queues/advisor?evaluatedAtUtc=2026-06-21T10:10:00Z",
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sourceAuthority"] == "lotus-idea"
    assert body["items"][0]["rank"] == 1
    assert body["items"][0]["candidate"]["sourceSignalIds"] == ["signal_high_cash_8d57adbf52f7f5a7"]
    assert body["supportedFeaturePromoted"] is False
    assert "gatewayRank" not in str(body)
    assert captured == {
        "evaluated_at_utc": "2026-06-21T10:10:00Z",
        "caller_headers": {
            "X-Caller-Subject": "advisor-123",
            "X-Caller-Roles": "advisor",
            "X-Caller-Capabilities": "idea.review.queue.read,idea.candidate.detail.read",
            "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
            "X-Caller-Book-Ids": "book-advisor-001",
            "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
            "X-Caller-Client-Ids": "client-001",
        },
        "correlation_id": "corr-idea-router",
    }


def test_idea_review_queue_route_allows_active_queue_without_evaluation_time(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _queue(self, *, evaluated_at_utc, caller_headers, correlation_id):
        captured["evaluated_at_utc"] = evaluated_at_utc
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        payload = dict(IDEA_REVIEW_QUEUE_EXAMPLE)
        payload["sourceAuthority"] = "lotus-idea"
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_advisor_review_queue",
        _queue,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/review-queues/advisor",
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json()["sourceAuthority"] == "lotus-idea"
    assert captured["evaluated_at_utc"] is None
    assert captured["caller_headers"] == {
        "X-Caller-Subject": "advisor-123",
        "X-Caller-Roles": "advisor",
        "X-Caller-Capabilities": "idea.review.queue.read,idea.candidate.detail.read",
        "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
        "X-Caller-Book-Ids": "book-advisor-001",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
        "X-Caller-Client-Ids": "client-001",
    }
    assert captured["correlation_id"] == "corr-idea-router"


def test_idea_candidate_detail_route_preserves_source_refs_without_enrichment(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _detail(self, *, candidate_id, caller_headers, correlation_id):
        captured["candidate_id"] = candidate_id
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        payload = dict(IDEA_CANDIDATE_DETAIL_EXAMPLE)
        payload["candidate"] = dict(payload["candidate"])
        payload["candidate"]["candidateId"] = candidate_id
        payload["sourceAuthority"] = "lotus-idea"
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_candidate_detail",
        _detail,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7",
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["candidate"]["candidateId"] == "idea_high_cash_8d57adbf52f7f5a7"
    assert body["sourceAuthority"] == "lotus-idea"
    assert body["evidence"]["sourceRefs"][0]["sourceSystem"] == "lotus-core"
    assert body["supportedFeaturePromoted"] is False
    assert "gatewayScore" not in str(body)
    assert "grantsDownstreamAuthority" not in str(body)
    assert captured == {
        "candidate_id": "idea_high_cash_8d57adbf52f7f5a7",
        "caller_headers": {
            "X-Caller-Subject": "advisor-123",
            "X-Caller-Roles": "advisor",
            "X-Caller-Capabilities": "idea.review.queue.read,idea.candidate.detail.read",
            "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
            "X-Caller-Book-Ids": "book-advisor-001",
            "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
            "X-Caller-Client-Ids": "client-001",
        },
        "correlation_id": "corr-idea-router",
    }


def test_idea_route_blocks_source_supported_feature_promotion(monkeypatch) -> None:
    async def _queue(self, *, evaluated_at_utc, caller_headers, correlation_id):
        payload = dict(IDEA_REVIEW_QUEUE_EXAMPLE)
        payload["supportedFeaturePromoted"] = True
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_advisor_review_queue",
        _queue,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/review-queues/advisor?evaluatedAtUtc=2026-06-21T10:10:00Z",
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_supported_feature_claim_invalid"


def test_idea_route_maps_upstream_failures_without_raw_payload(monkeypatch) -> None:
    async def _detail(self, *, candidate_id, caller_headers, correlation_id):
        return 500, {"detail": "postgres traceback idea.internal source payload"}

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_candidate_detail",
        _detail,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7",
        headers=_headers(),
    )

    assert response.status_code == 502
    body = response.json()
    assert body["detail"]["code"] == "idea_candidate_unavailable"
    assert "postgres" not in str(body).lower()
    assert "idea.internal" not in str(body)


@pytest.mark.parametrize(
    ("method_name", "route"),
    [
        (
            "get_advisor_review_queue",
            "/api/v1/ideas/review-queues/advisor?evaluatedAtUtc=2026-06-21T10:10:00Z",
        ),
        (
            "get_candidate_detail",
            "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7",
        ),
    ],
)
def test_idea_read_routes_preserve_source_permission_denial_without_payload_leakage(
    monkeypatch,
    method_name,
    route,
) -> None:
    async def _denied(self, **kwargs):
        return 403, {
            "detail": "tenant-private-bank-sg:portfolio:PB_SG_GLOBAL_BAL_001 denied by authz"
        }

    monkeypatch.setattr(f"app.clients.lotus_idea_client.LotusIdeaClient.{method_name}", _denied)

    response = TestClient(app).get(route, headers=_headers())

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["code"] == "idea_permission_denied"
    assert "PB_SG_GLOBAL_BAL_001" not in str(body)
    assert "authz" not in str(body).lower()


@pytest.mark.parametrize(
    ("method_name", "path", "body", "payload_key", "payload"),
    [
        (
            "record_candidate_review_action",
            "/review-actions",
            {
                "reviewId": "review-001",
                "action": "approve_for_conversion",
                "reasonCodes": ["review_required"],
                "decidedAtUtc": "2026-06-21T10:15:00Z",
            },
            "reviewDecision",
            {
                "reviewId": "review-001",
                "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
                "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
                "action": "approve_for_conversion",
                "resultingPosture": "approved_for_conversion",
                "actorRole": "advisor",
                "reasonCodes": ["review_required"],
                "decidedAtUtc": "2026-06-21T10:15:00Z",
                "suppressionReason": None,
                "snoozedUntilUtc": None,
                "grantsDownstreamAuthority": False,
            },
        ),
        (
            "record_candidate_feedback",
            "/feedback",
            {
                "feedbackId": "feedback-001",
                "outcome": "useful",
                "reasonCodes": ["review_required"],
                "recordedAtUtc": "2026-06-21T10:16:00Z",
            },
            "feedbackEvent",
            {
                "feedbackId": "feedback-001",
                "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
                "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
                "outcome": "useful",
                "actorRole": "advisor",
                "reasonCodes": ["review_required"],
                "recordedAtUtc": "2026-06-21T10:16:00Z",
            },
        ),
        (
            "record_candidate_conversion_intent",
            "/conversion-intents",
            {
                "conversionIntentId": "conversion-001",
                "target": "report_evidence",
                "reasonCodes": ["review_required"],
                "requestedAtUtc": "2026-06-21T10:17:00Z",
            },
            "conversionIntent",
            {
                "conversionIntentId": "conversion-001",
                "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
                "target": "report_evidence",
                "sourceStatus": "approved_for_conversion",
                "targetSourceAuthority": "lotus-report",
                "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
                "evidenceContentHash": "sha256:evidence-lineage",
                "sourceSignalIds": ["signal_high_cash_8d57adbf52f7f5a7"],
                "boundary": "intent_only",
                "reasonCodes": ["review_required"],
                "requestedAtUtc": "2026-06-21T10:17:00Z",
                "grantsDownstreamAuthority": False,
            },
        ),
    ],
)
def test_idea_candidate_action_routes_forward_source_owned_mutations(
    monkeypatch,
    method_name,
    path,
    body,
    payload_key,
    payload,
) -> None:
    captured: dict[str, object] = {}

    async def _action(
        self,
        *,
        candidate_id,
        body,
        caller_headers,
        correlation_id,
        idempotency_key,
        causation_id,
    ):
        captured.update(
            {
                "candidate_id": candidate_id,
                "body": body,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
                "idempotency_key": idempotency_key,
                "causation_id": causation_id,
            }
        )
        return 200, {
            payload_key: payload,
            "persistence": {
                "decision": "accepted",
                "candidateId": candidate_id,
                "lifecycleStatus": "generated",
                "reviewPosture": "advisor_review_required",
                "auditEventType": "idea.candidate.action.recorded",
            },
            "durableStorageBacked": True,
            "supportedFeaturePromoted": False,
        }

    monkeypatch.setattr(f"app.clients.lotus_idea_client.LotusIdeaClient.{method_name}", _action)
    headers = {
        **_headers(),
        "Idempotency-Key": "idea-action-idem-001",
        "X-Causation-Id": "workflow-parent-001",
        "X-Lotus-Trusted-Caller-Context": "trusted-context-opaque",
    }
    response = TestClient(app).post(
        f"/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7{path}",
        json=body,
        headers=headers,
    )

    assert response.status_code == 200
    response_body = response.json()
    assert response_body[payload_key]["candidateId"] == "idea_high_cash_8d57adbf52f7f5a7"
    assert response_body["supportedFeaturePromoted"] is False
    assert captured["candidate_id"] == "idea_high_cash_8d57adbf52f7f5a7"
    assert captured["body"] == body
    assert captured["idempotency_key"] == "idea-action-idem-001"
    assert captured["causation_id"] == "workflow-parent-001"
    assert captured["correlation_id"] == "corr-idea-router"
    assert captured["caller_headers"] == {
        "X-Caller-Subject": "advisor-123",
        "X-Caller-Roles": "advisor",
        "X-Caller-Capabilities": "idea.review.queue.read,idea.candidate.detail.read",
        "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
        "X-Caller-Book-Ids": "book-advisor-001",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
        "X-Caller-Client-Ids": "client-001",
        "X-Lotus-Trusted-Caller-Context": "trusted-context-opaque",
    }


def test_idea_candidate_action_rejects_body_authority_override(monkeypatch) -> None:
    async def _action(*args, **kwargs):
        raise AssertionError("Gateway must not forward an authority override body field.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_review_action",
        _action,
    )
    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/review-actions",
        json={
            "reviewId": "review-001",
            "action": "approve_for_conversion",
            "reasonCodes": ["review_required"],
            "decidedAtUtc": "2026-06-21T10:15:00Z",
            "authorizedScope": {"portfolioIds": ["other-portfolio"]},
        },
        headers={**_headers(), "Idempotency-Key": "idea-action-idem-override"},
    )

    assert response.status_code == 422
    assert "authorizedScope" in str(response.json())


def test_idea_candidate_action_requires_idempotency_before_upstream_call(monkeypatch) -> None:
    async def _action(*args, **kwargs):
        raise AssertionError("Gateway must not call Lotus Idea without Idempotency-Key.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_review_action",
        _action,
    )

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/review-actions",
        json={
            "reviewId": "review-001",
            "action": "approve_for_conversion",
            "reasonCodes": ["review_required"],
            "decidedAtUtc": "2026-06-21T10:15:00Z",
        },
        headers=_headers(),
    )

    assert response.status_code == 422
    assert "Idempotency-Key" in str(response.json())


def test_idea_candidate_action_preserves_source_permission_denial_without_payload_leakage(
    monkeypatch,
) -> None:
    async def _action(self, **kwargs):
        return 403, {
            "detail": "advisor-123 cannot record feedback for client-001 on candidate payload"
        }

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _action,
    )

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/feedback",
        json={
            "feedbackId": "feedback-001",
            "outcome": "useful",
            "reasonCodes": ["review_required"],
            "recordedAtUtc": "2026-06-21T10:16:00Z",
        },
        headers={**_headers(), "Idempotency-Key": "idea-action-idem-denied"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["code"] == "idea_permission_denied"
    assert "advisor-123" not in str(body)
    assert "client-001" not in str(body)


@pytest.mark.parametrize("upstream_status", [409, 422])
def test_idea_candidate_action_preserves_source_conflict_and_validation_status(
    monkeypatch, upstream_status
) -> None:
    async def _action(self, **kwargs):
        return upstream_status, {"detail": "source-internal-detail"}

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _action,
    )
    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/feedback",
        json={
            "feedbackId": "feedback-001",
            "outcome": "useful",
            "reasonCodes": ["review_required"],
            "recordedAtUtc": "2026-06-21T10:16:00Z",
        },
        headers={**_headers(), "Idempotency-Key": "idea-action-idem-error"},
    )

    assert response.status_code == upstream_status
    assert "source-internal-detail" not in str(response.json())
