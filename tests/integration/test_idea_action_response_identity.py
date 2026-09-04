"""Review/conversion success evidence must bind to the exact submitted action (issue #694).

Lotus Idea owns lifecycle transitions, persistence, replay, and audit. Gateway must not
acknowledge a shape-valid source success that describes a different immutable event.

The faithful source echo is asserted from lotus-idea's shipped contract: review decisions
canonicalize reason codes (the action-owned reason first, exactly once), while conversion
intents echo the submitted reason codes verbatim.
"""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.contracts.idea_examples import (
    IDEA_CONVERSION_INTENT_EXAMPLE,
    IDEA_REVIEW_ACTION_EXAMPLE,
)
from app.main import app

_CANDIDATE_ID = "idea_high_cash_8d57adbf52f7f5a7"
_REVIEW_PATH = f"/api/v1/ideas/candidates/{_CANDIDATE_ID}/review-actions"
_CONVERSION_PATH = f"/api/v1/ideas/candidates/{_CANDIDATE_ID}/conversion-intents"


def _headers() -> dict[str, str]:
    return {
        "X-Caller-Subject": "advisor-123",
        "X-Caller-Roles": "advisor",
        "X-Caller-Capabilities": "idea.review.queue.read,idea.candidate.detail.read",
        "X-Caller-Tenant-Ids": "tenant-private-bank-sg",
        "X-Caller-Book-Ids": "book-advisor-001",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
        "X-Caller-Client-Ids": "client-001",
        "X-Correlation-Id": "corr-idea-action-identity",
        "Idempotency-Key": "idea-action-idem-001",
    }


def _review_request() -> dict[str, object]:
    return {
        "reviewId": "review-001",
        "action": "approve_for_conversion",
        "reasonCodes": ["review_required"],
        "decidedAtUtc": "2026-06-21T10:15:00Z",
    }


def _conversion_request() -> dict[str, object]:
    return {
        "conversionIntentId": "conversion-001",
        "target": "report_evidence",
        "reasonCodes": ["review_required"],
        "requestedAtUtc": "2026-06-21T10:17:00Z",
    }


def _stub_source(monkeypatch: pytest.MonkeyPatch, method: str, payload: dict[str, object]) -> None:
    async def _action(self, **kwargs):
        return 200, deepcopy(payload)

    monkeypatch.setattr(f"app.clients.lotus_idea_client.LotusIdeaClient.{method}", _action)


def _refuse_source(monkeypatch: pytest.MonkeyPatch, method: str) -> None:
    async def _action(self, **kwargs):
        raise AssertionError("Gateway must reject this request before calling Lotus Idea.")

    monkeypatch.setattr(f"app.clients.lotus_idea_client.LotusIdeaClient.{method}", _action)


@pytest.mark.parametrize(
    ("field", "changed_value"),
    (
        ("reviewId", "review-different"),
        ("candidateId", "idea_high_cash_different_candidate"),
        ("action", "reject"),
        # Verbatim echo without the Idea-owned reason first is not the shipped source contract.
        ("reasonCodes", ["review_required"]),
        ("reasonCodes", ["review_required", "review_approved_for_conversion"]),
        ("reasonCodes", ["review_approved_for_conversion"]),
        ("reasonCodes", ["review_approved_for_conversion", "review_no_action"]),
        ("decidedAtUtc", "2026-06-21T10:16:00Z"),
        ("suppressionReason", "manual_suppression"),
        ("snoozedUntilUtc", "2026-06-22T10:15:00Z"),
    ),
)
def test_review_action_rejects_evidence_for_a_different_action(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    changed_value: object,
) -> None:
    payload = deepcopy(IDEA_REVIEW_ACTION_EXAMPLE)
    payload["reviewDecision"][field] = changed_value
    _stub_source(monkeypatch, "record_candidate_review_action", payload)

    response = TestClient(app).post(_REVIEW_PATH, json=_review_request(), headers=_headers())

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_review_evidence_mismatch"


@pytest.mark.parametrize(
    "submitted_reason_codes",
    (
        ["review_required"],
        ["review_approved_for_conversion", "review_required"],
        ["review_required", "review_approved_for_conversion"],
    ),
)
def test_review_action_accepts_source_canonical_reason_codes(
    monkeypatch: pytest.MonkeyPatch,
    submitted_reason_codes: list[str],
) -> None:
    _stub_source(monkeypatch, "record_candidate_review_action", IDEA_REVIEW_ACTION_EXAMPLE)
    request = {**_review_request(), "reasonCodes": submitted_reason_codes}

    response = TestClient(app).post(_REVIEW_PATH, json=request, headers=_headers())

    assert response.status_code == 200
    assert response.json()["reviewDecision"]["reasonCodes"] == [
        "review_approved_for_conversion",
        "review_required",
    ]


def test_review_action_rejects_success_without_decision_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = deepcopy(IDEA_REVIEW_ACTION_EXAMPLE)
    del payload["reviewDecision"]
    _stub_source(monkeypatch, "record_candidate_review_action", payload)

    response = TestClient(app).post(_REVIEW_PATH, json=_review_request(), headers=_headers())

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_review_action_accepts_equivalent_zoned_decision_instant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = deepcopy(IDEA_REVIEW_ACTION_EXAMPLE)
    payload["reviewDecision"]["decidedAtUtc"] = "2026-06-21T12:15:00+02:00"
    _stub_source(monkeypatch, "record_candidate_review_action", payload)

    response = TestClient(app).post(_REVIEW_PATH, json=_review_request(), headers=_headers())

    assert response.status_code == 200
    assert response.json()["reviewDecision"]["reviewId"] == "review-001"


@pytest.mark.parametrize(
    ("field", "naive_instant"),
    (
        ("decidedAtUtc", "2026-06-21T10:15:00"),
        ("snoozedUntilUtc", "2026-06-22T10:15:00"),
    ),
)
def test_review_action_rejects_naive_instants_before_fanout(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    naive_instant: str,
) -> None:
    _refuse_source(monkeypatch, "record_candidate_review_action")
    request = {**_review_request(), field: naive_instant}

    response = TestClient(app).post(_REVIEW_PATH, json=request, headers=_headers())

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "changed_value"),
    (
        ("conversionIntentId", "conversion-different"),
        ("candidateId", "idea_high_cash_different_candidate"),
        ("target", "advise_proposal"),
        ("reasonCodes", ["review_no_action"]),
        ("reasonCodes", ["review_required", "review_no_action"]),
        ("requestedAtUtc", "2026-06-21T10:18:00Z"),
    ),
)
def test_conversion_intent_rejects_evidence_for_a_different_action(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    changed_value: object,
) -> None:
    payload = deepcopy(IDEA_CONVERSION_INTENT_EXAMPLE)
    payload["conversionIntent"][field] = changed_value
    _stub_source(monkeypatch, "record_candidate_conversion_intent", payload)

    response = TestClient(app).post(
        _CONVERSION_PATH, json=_conversion_request(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_conversion_evidence_mismatch"


def test_conversion_intent_rejects_success_without_intent_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = deepcopy(IDEA_CONVERSION_INTENT_EXAMPLE)
    del payload["conversionIntent"]
    _stub_source(monkeypatch, "record_candidate_conversion_intent", payload)

    response = TestClient(app).post(
        _CONVERSION_PATH, json=_conversion_request(), headers=_headers()
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "idea_contract_invalid"


def test_conversion_intent_accepts_equivalent_zoned_request_instant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = deepcopy(IDEA_CONVERSION_INTENT_EXAMPLE)
    payload["conversionIntent"]["requestedAtUtc"] = "2026-06-21T12:17:00+02:00"
    _stub_source(monkeypatch, "record_candidate_conversion_intent", payload)

    response = TestClient(app).post(
        _CONVERSION_PATH, json=_conversion_request(), headers=_headers()
    )

    assert response.status_code == 200
    assert response.json()["conversionIntent"]["conversionIntentId"] == "conversion-001"


def test_conversion_intent_rejects_naive_request_instant_before_fanout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refuse_source(monkeypatch, "record_candidate_conversion_intent")
    request = {**_conversion_request(), "requestedAtUtc": "2026-06-21T10:17:00"}

    response = TestClient(app).post(_CONVERSION_PATH, json=request, headers=_headers())

    assert response.status_code == 422
