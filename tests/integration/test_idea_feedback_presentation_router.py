from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.contracts.idea_examples import (
    IDEA_FEEDBACK_EXAMPLE,
    IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE,
    IDEA_REVIEW_QUEUE_EXAMPLE,
)
from app.main import app

_CANDIDATE_ID = "idea_high_cash_8d57adbf52f7f5a7"
_FEEDBACK_PATH = f"/api/v1/ideas/candidates/{_CANDIDATE_ID}/feedback"
_PRESENTATION_PATH = f"/api/v1/ideas/candidates/{_CANDIDATE_ID}/presentation-receipts"
_FEEDBACK_CASES = (
    ("useful", "relevant"),
    ("not_useful", "not_relevant"),
    ("not_useful", "already_known"),
    ("not_useful", "wrong_timing"),
    ("not_useful", "insufficient_evidence"),
    ("not_useful", "wrong_priority"),
    ("not_useful", "duplicate"),
    ("not_useful", "client_specific_constraint"),
)


def _headers() -> dict[str, str]:
    return {
        "X-Caller-Subject": "advisor-123",
        "X-Caller-Roles": "advisor",
        "X-Caller-Capabilities": (
            "idea.feedback.record,idea.presentation-receipt.record,idea.review.queue.read"
        ),
        "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
        "X-Correlation-Id": "corr-idea-governed-actions",
        "Idempotency-Key": "idea-governed-action-001",
        "X-Causation-Id": "visible-queue-render-001",
    }


def _feedback_payload(outcome: str = "useful", reason: str = "relevant") -> dict[str, object]:
    return {
        "feedbackId": f"feedback-{reason}",
        "taxonomyVersion": "idea-feedback-taxonomy-v1",
        "outcome": outcome,
        "reason": reason,
        "recordedAtUtc": "2026-06-21T10:16:00Z",
    }


def _feedback_success_payload() -> dict[str, object]:
    payload = deepcopy(IDEA_FEEDBACK_EXAMPLE)
    payload["feedbackEvent"].update(_feedback_payload())
    payload["feedbackEvent"]["candidateId"] = _CANDIDATE_ID
    payload["persistence"]["candidateId"] = _CANDIDATE_ID
    return payload


def _presentation_payload() -> dict[str, object]:
    return {
        "tenantId": "tenant-private-bank-sg",
        "presentedAtUtc": "2026-06-21T10:16:00Z",
        "rankAtPresentation": 25,
        "visibleCandidateCount": 1,
        "queueSnapshotDigest": f"sha256:{'a' * 64}",
        "queuePolicyVersion": "idea-deterministic-ranking-v1",
        "rankingPolicyVersion": "idle-liquidity-v1",
        "candidateMaterialVersion": 1,
        "candidateEvidenceVersion": 1,
    }


@pytest.mark.parametrize(("outcome", "reason"), _FEEDBACK_CASES)
def test_governed_feedback_taxonomy_is_forwarded_and_returned_without_translation(
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
    reason: str,
) -> None:
    captured: dict[str, object] = {}

    async def _feedback(self, **kwargs):
        captured.update(kwargs)
        body = kwargs["body"]
        return 200, {
            "feedbackEvent": {
                **body,
                "candidateId": kwargs["candidate_id"],
                "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
                "actorRole": "advisor",
            },
            "persistence": {
                "decision": "accepted",
                "candidateId": kwargs["candidate_id"],
                "lifecycleStatus": "generated",
                "reviewPosture": "advisor_review_required",
                "auditEventType": "idea.candidate.feedback.recorded",
            },
            "durableStorageBacked": True,
            "supportedFeaturePromoted": False,
        }

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _feedback,
    )
    payload = _feedback_payload(outcome, reason)

    response = TestClient(app).post(_FEEDBACK_PATH, json=payload, headers=_headers())

    assert response.status_code == 200
    event = response.json()["feedbackEvent"]
    assert (event["taxonomyVersion"], event["outcome"], event["reason"]) == (
        "idea-feedback-taxonomy-v1",
        outcome,
        reason,
    )
    assert captured["body"] == payload
    assert captured["idempotency_key"] == "idea-governed-action-001"
    assert captured["causation_id"] == "visible-queue-render-001"
    assert "reasonCodes" not in str(captured["body"])


@pytest.mark.parametrize(
    "payload",
    (
        {**_feedback_payload(), "taxonomyVersion": "idea-feedback-taxonomy-v0"},
        {key: value for key, value in _feedback_payload().items() if key != "taxonomyVersion"},
        {**_feedback_payload(), "reason": "advisor_feedback"},
        {**_feedback_payload(), "outcome": "too_late"},
        {**_feedback_payload(), "reasonCodes": ["review_required"]},
        {**_feedback_payload(), "feedbackId": "   "},
        {**_feedback_payload(), "recordedAtUtc": "2026-06-21T10:16:00"},
    ),
)
def test_feedback_rejects_drifted_or_legacy_transport_before_fanout(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> None:
    async def _feedback(*args, **kwargs):
        raise AssertionError("Invalid feedback transport must not reach Lotus Idea.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _feedback,
    )

    response = TestClient(app).post(_FEEDBACK_PATH, json=payload, headers=_headers())

    assert response.status_code == 422


def test_feedback_preserves_source_owned_invalid_combination_code_without_payload_leakage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _feedback(self, **kwargs):
        assert kwargs["body"] == _feedback_payload("useful", "not_relevant")
        return 400, {
            "code": "feedback_taxonomy_combination_invalid",
            "detail": "candidate and client source internals must not escape",
        }

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _feedback,
    )

    response = TestClient(app).post(
        _FEEDBACK_PATH,
        json=_feedback_payload("useful", "not_relevant"),
        headers=_headers(),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "feedback_taxonomy_combination_invalid"
    assert "source internals" not in response.text


@pytest.mark.parametrize("source_code", ("idempotency_conflict", "review_identity_conflict"))
def test_feedback_preserves_allowlisted_source_conflict_codes_safely(
    monkeypatch: pytest.MonkeyPatch,
    source_code: str,
) -> None:
    async def _feedback(self, **kwargs):
        return 409, {
            "code": source_code,
            "detail": "candidate client tenant and database internals",
        }

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _feedback,
    )

    response = TestClient(app).post(
        _FEEDBACK_PATH,
        json=_feedback_payload(),
        headers=_headers(),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == source_code
    assert "database internals" not in response.text


@pytest.mark.parametrize(
    ("field", "changed_value"),
    (
        ("feedbackId", "feedback-different"),
        ("candidateId", "idea_high_cash_different_candidate"),
        ("outcome", "not_useful"),
        ("reason", "wrong_timing"),
        ("recordedAtUtc", "2026-06-21T10:17:00Z"),
    ),
)
def test_feedback_rejects_persisted_event_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    changed_value: object,
) -> None:
    async def _feedback(self, **kwargs):
        payload = _feedback_success_payload()
        payload["feedbackEvent"][field] = changed_value
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _feedback,
    )

    response = TestClient(app).post(_FEEDBACK_PATH, json=_feedback_payload(), headers=_headers())

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_feedback_evidence_mismatch"


def test_feedback_rejects_success_without_persisted_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _feedback(self, **kwargs):
        payload = _feedback_success_payload()
        del payload["feedbackEvent"]
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_feedback",
        _feedback,
    )

    response = TestClient(app).post(_FEEDBACK_PATH, json=_feedback_payload(), headers=_headers())

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


@pytest.mark.parametrize(
    ("source_status", "decision"),
    ((201, "accepted"), (200, "replayed")),
)
def test_presentation_receipt_preserves_source_status_body_and_lineage(
    monkeypatch: pytest.MonkeyPatch,
    source_status: int,
    decision: str,
) -> None:
    captured: dict[str, object] = {}

    async def _presentation(self, **kwargs):
        captured.update(kwargs)
        response = deepcopy(IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE)
        response["persistenceDecision"] = decision
        return source_status, response

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )
    payload = _presentation_payload()

    response = TestClient(app).post(_PRESENTATION_PATH, json=payload, headers=_headers())

    assert response.status_code == source_status
    assert response.json()["persistenceDecision"] == decision
    assert response.json()["receipt"] == IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE["receipt"]
    assert response.json()["supportedFeaturePromoted"] is False
    assert captured["candidate_id"] == _CANDIDATE_ID
    assert captured["body"] == payload
    assert captured["idempotency_key"] == "idea-governed-action-001"
    assert captured["causation_id"] == "visible-queue-render-001"
    assert captured["correlation_id"] == "corr-idea-governed-actions"


@pytest.mark.parametrize(
    "payload",
    (
        {key: value for key, value in _presentation_payload().items() if key != "tenantId"},
        {**_presentation_payload(), "unexpected": "alias"},
        {**_presentation_payload(), "presentedAtUtc": "2026-06-21T10:16:00"},
        {**_presentation_payload(), "presentedAtUtc": "2026-06-21T11:16:00+01:00"},
        {**_presentation_payload(), "rankAtPresentation": 0},
        {**_presentation_payload(), "visibleCandidateCount": 101},
        {**_presentation_payload(), "queueSnapshotDigest": "sha256:not-a-digest"},
        {**_presentation_payload(), "candidateEvidenceVersion": 0},
    ),
)
def test_presentation_receipt_rejects_malformed_transport_before_fanout(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> None:
    async def _presentation(*args, **kwargs):
        raise AssertionError("Malformed presentation receipt must not reach Lotus Idea.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(_PRESENTATION_PATH, json=payload, headers=_headers())

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field_name",
    (
        "rankAtPresentation",
        "visibleCandidateCount",
        "candidateMaterialVersion",
        "candidateEvidenceVersion",
    ),
)
@pytest.mark.parametrize("invalid_value", (True, "1"))
def test_presentation_receipt_rejects_coerced_integer_evidence_before_fanout(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    invalid_value: object,
) -> None:
    async def _presentation(*args, **kwargs):
        raise AssertionError("Coerced presentation evidence must not reach Lotus Idea.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH,
        json={**_presentation_payload(), field_name: invalid_value},
        headers=_headers(),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("idempotency_key", (None, "", "   "))
def test_presentation_receipt_requires_nonblank_idempotency_key_before_fanout(
    monkeypatch: pytest.MonkeyPatch,
    idempotency_key: str | None,
) -> None:
    async def _presentation(*args, **kwargs):
        raise AssertionError("Receipt without stable identity must not reach Lotus Idea.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )
    headers = _headers()
    if idempotency_key is None:
        del headers["Idempotency-Key"]
    else:
        headers["Idempotency-Key"] = idempotency_key

    response = TestClient(app).post(
        _PRESENTATION_PATH,
        json=_presentation_payload(),
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("source_status", "source_code"),
    (
        (400, "invalid_request"),
        (403, "permission_denied"),
        (404, "candidate_not_found"),
        (409, "presentation_receipt_identity_conflict"),
        (409, "presentation_receipt_candidate_state_conflict"),
        (503, "durable_repository_not_configured"),
        (503, "durable_repository_unavailable"),
        (503, "service_restoring"),
        (503, "service_recovery_degraded"),
        (503, "service_draining"),
        (503, "presentation_receipt_unavailable"),
    ),
)
def test_presentation_receipt_preserves_allowlisted_source_problem_codes_safely(
    monkeypatch: pytest.MonkeyPatch,
    source_status: int,
    source_code: str,
) -> None:
    async def _presentation(self, **kwargs):
        return source_status, {
            "code": source_code,
            "detail": "candidate client tenant and database internals",
        }

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH, json=_presentation_payload(), headers=_headers()
    )

    assert response.status_code == source_status
    assert response.json()["detail"]["code"] == source_code
    assert "database internals" not in response.text


@pytest.mark.parametrize(
    ("source_status", "source_code"),
    ((422, "invalid_request"), (400, "unrecognized_receipt_failure")),
)
def test_presentation_receipt_rejects_non_allowlisted_source_problem(
    monkeypatch: pytest.MonkeyPatch,
    source_status: int,
    source_code: str,
) -> None:
    async def _presentation(self, **kwargs):
        return source_status, {
            "code": source_code,
            "detail": "candidate client tenant and database internals",
        }

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH, json=_presentation_payload(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == ("idea_presentation_receipt_problem_invalid")
    assert "database internals" not in response.text


def test_presentation_receipt_rejects_unexpected_success_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _presentation(self, **kwargs):
        return 202, deepcopy(IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE)

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH, json=_presentation_payload(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_presentation_receipt_status_invalid"


@pytest.mark.parametrize(
    ("source_status", "decision"),
    ((201, "replayed"), (200, "accepted")),
)
def test_presentation_receipt_rejects_status_decision_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    source_status: int,
    decision: str,
) -> None:
    async def _presentation(self, **kwargs):
        payload = deepcopy(IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE)
        payload["persistenceDecision"] = decision
        return source_status, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH, json=_presentation_payload(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == ("idea_presentation_receipt_decision_invalid")


@pytest.mark.parametrize(
    ("field", "changed_value"),
    (
        ("candidateId", "idea_high_cash_different_candidate"),
        ("tenantId", "tenant-private-bank-hk"),
        ("presentedAtUtc", "2026-06-21T10:17:00Z"),
        ("rankAtPresentation", 24),
        ("visibleCandidateCount", 2),
        ("queueSnapshotDigest", f"sha256:{'b' * 64}"),
        ("queuePolicyVersion", "idea-deterministic-ranking-v2"),
        ("rankingPolicyVersion", "idle-liquidity-v2"),
        ("candidateMaterialVersion", 2),
        ("candidateEvidenceVersion", 2),
    ),
)
def test_presentation_receipt_rejects_persisted_evidence_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    changed_value: object,
) -> None:
    async def _presentation(self, **kwargs):
        payload = deepcopy(IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE)
        payload["receipt"][field] = changed_value
        return 201, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH, json=_presentation_payload(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == ("idea_presentation_receipt_evidence_mismatch")


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        ("missing_receipt", "idea_contract_invalid"),
        ("promoted_feature", "idea_supported_feature_claim_invalid"),
        ("non_durable_success", "idea_contract_invalid"),
        ("invalid_receipt_rank", "idea_contract_invalid"),
    ),
)
def test_presentation_receipt_rejects_untruthful_source_success_payload(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_code: str,
) -> None:
    async def _presentation(self, **kwargs):
        payload = deepcopy(IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE)
        if mutation == "missing_receipt":
            del payload["receipt"]
        elif mutation == "promoted_feature":
            payload["supportedFeaturePromoted"] = True
        elif mutation == "non_durable_success":
            payload["durableStorageBacked"] = False
        else:
            payload["receipt"]["rankAtPresentation"] = True
        return 201, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).post(
        _PRESENTATION_PATH, json=_presentation_payload(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == expected_code


def test_queue_retrieval_never_synthesizes_presentation_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _queue(self, **kwargs):
        return 200, IDEA_REVIEW_QUEUE_EXAMPLE

    async def _presentation(*args, **kwargs):
        raise AssertionError("Queue retrieval must not record presentation evidence.")

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_advisor_review_queue",
        _queue,
    )
    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.record_candidate_presentation_receipt",
        _presentation,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/review-queues/advisor",
        headers=_headers(),
    )

    assert response.status_code == 200
    candidate = response.json()["items"][0]["candidate"]
    assert (candidate["materialVersion"], candidate["evidenceVersion"]) == (1, 1)


@pytest.mark.parametrize(
    "version_field",
    ("materialVersion", "evidenceVersion", "scorePolicyVersion"),
)
def test_queue_rejects_missing_source_versions_before_workbench_consumption(
    monkeypatch: pytest.MonkeyPatch,
    version_field: str,
) -> None:
    async def _queue(self, **kwargs):
        payload = deepcopy(IDEA_REVIEW_QUEUE_EXAMPLE)
        del payload["items"][0]["candidate"][version_field]
        return 200, payload

    monkeypatch.setattr(
        "app.clients.lotus_idea_client.LotusIdeaClient.get_advisor_review_queue",
        _queue,
    )

    response = TestClient(app).get(
        "/api/v1/ideas/review-queues/advisor",
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"
