from fastapi.testclient import TestClient

from app.contracts.ideas import IDEA_CANDIDATE_DETAIL_EXAMPLE, IDEA_REVIEW_QUEUE_EXAMPLE
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
