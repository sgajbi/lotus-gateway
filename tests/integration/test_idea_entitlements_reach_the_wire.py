"""The caller's entitlement set survives all the way onto the outbound request.

`tests/unit/test_caller_entitlements_forwarded_whole.py` proves the ingress
dependency and `as_idea_context()` do not narrow. That is not the whole path: the
client builds its own outbound headers afterwards, through
`_idea_headers` / `_idea_mutation_headers` and `build_upstream_headers`. A
truncation introduced there corrupts the real request while every unit case stays
green, because none of them reach the wire.

These drive a registered route with the real `LotusIdeaClient` and capture what
the transport was actually handed. Both shapes are covered: the plain read, and
the receipt write, which additionally carries idempotency and causation and so
merges two header maps rather than one.
"""

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.contracts.idea_examples import IDEA_CANDIDATE_DETAIL_EXAMPLE
from app.main import app

# Distinct per field, multi-valued, and deliberately unsorted: a shared value
# could be asserted from the wrong header and still pass, and a sorted one cannot
# detect a reordering.
_ENTITLEMENTS = {
    "X-Caller-Roles": "reviewer,advisor,supervisor",
    "X-Caller-Capabilities": "idea.review,idea.convert,idea.suppress",
    "X-Caller-Tenant-Ids": "tenant-sg,tenant-hk,tenant-ch",
    "X-Caller-Book-Ids": "BOOK_SG_2,BOOK_SG_1,BOOK_HK_9",
    "X-Caller-Portfolio-Ids": "PB_SG_2,PB_SG_1,PB_HK_7",
    "X-Caller-Client-Ids": "CL_9,CL_2,CL_5",
}


class _CapturingAsyncClient:
    """Records what the transport was handed, and answers with a canned payload."""

    calls: list[dict[str, Any]] = []
    payload: dict[str, Any] = {}
    status: int = 200

    def __init__(self, timeout: float, **_: object) -> None:
        self._timeout = timeout

    async def __aenter__(self) -> "_CapturingAsyncClient":
        return self

    async def __aexit__(self, *_: object) -> bool:
        return False

    def _respond(self, method: str, url: str, headers: dict[str, str] | None) -> httpx.Response:
        type(self).calls.append({"method": method, "url": url, "headers": headers or {}})
        return httpx.Response(
            type(self).status,
            json=type(self).payload,
            request=httpx.Request(method, url),
        )

    async def get(self, url, params=None, headers=None):  # noqa: ANN001, ANN201
        return self._respond("GET", url, headers)

    async def post(self, url, json=None, data=None, files=None, params=None, headers=None):  # noqa: ANN001, ANN201
        return self._respond("POST", url, headers)


@pytest.fixture()
def outbound(monkeypatch: pytest.MonkeyPatch) -> type[_CapturingAsyncClient]:
    _CapturingAsyncClient.calls = []
    _CapturingAsyncClient.payload = {}
    _CapturingAsyncClient.status = 200
    monkeypatch.setattr("httpx.AsyncClient", _CapturingAsyncClient)
    return _CapturingAsyncClient


def _request_headers(**overrides: str) -> dict[str, str]:
    headers = {
        "X-Caller-Subject": "advisor_1",
        "X-Correlation-Id": "corr-entitlements",
        **_ENTITLEMENTS,
    }
    headers.update(overrides)
    return headers


def test_a_candidate_read_puts_every_entitlement_on_the_wire_unchanged(outbound) -> None:  # noqa: ANN001
    outbound.payload = IDEA_CANDIDATE_DETAIL_EXAMPLE

    response = TestClient(app).get(
        "/api/v1/ideas/candidates/idea_cand_1",
        headers=_request_headers(),
    )

    assert response.status_code == 200
    assert outbound.calls, "the route did not reach the transport"
    sent = outbound.calls[0]["headers"]
    for header, value in _ENTITLEMENTS.items():
        assert sent[header] == value, f"{header} was altered between ingress and the wire"
    assert sent["X-Correlation-Id"] == "corr-entitlements"
    assert sent["X-Caller-Service"] == "lotus-gateway"


def test_a_receipt_write_puts_every_entitlement_on_the_wire_unchanged(outbound) -> None:  # noqa: ANN001
    outbound.status = 201
    outbound.payload = {
        "receipt": {
            "receiptId": "rcpt_1",
            "candidateId": "idea_cand_1",
            "schemaVersion": "lotus-idea.candidate-presentation-receipt.v1",
            "surface": "advisor_review_queue",
            "producer": "lotus-workbench",
            "tenantId": "tenant-sg",
            "presentedAtUtc": "2026-05-03T09:00:00Z",
            "rankAtPresentation": 1,
            "visibleCandidateCount": 5,
            "queueSnapshotDigest": "sha256:" + "a" * 64,
            "queuePolicyVersion": "queue.v1",
            "rankingPolicyVersion": "ranking.v1",
            "candidateMaterialVersion": 3,
            "candidateEvidenceVersion": 7,
        },
        "persistenceDecision": "accepted",
        "durableStorageBacked": True,
        "effectivenessMeasurementStatus": "stored_consumer_certification_pending",
        "certificationStatus": "not_certified",
        "certificationBlockers": [],
        "supportedFeaturePromoted": False,
    }

    response = TestClient(app).post(
        "/api/v1/ideas/candidates/idea_cand_1/presentation-receipts",
        headers=_request_headers(
            **{"Idempotency-Key": "receipt-idem-1", "X-Causation-Id": "cause-1"}
        ),
        json={
            "tenantId": "tenant-sg",
            "presentedAtUtc": "2026-05-03T09:00:00Z",
            "rankAtPresentation": 1,
            "visibleCandidateCount": 5,
            "queueSnapshotDigest": "sha256:" + "a" * 64,
            "queuePolicyVersion": "queue.v1",
            "rankingPolicyVersion": "ranking.v1",
            "candidateMaterialVersion": 3,
            "candidateEvidenceVersion": 7,
        },
    )

    assert response.status_code in (200, 201), response.text
    assert outbound.calls, "the route did not reach the transport"
    sent = outbound.calls[0]["headers"]
    for header, value in _ENTITLEMENTS.items():
        assert sent[header] == value, f"{header} was altered between ingress and the wire"
    # The mutation builder merges a second header map; these must survive that merge
    # alongside the entitlements rather than replacing them.
    assert sent["Idempotency-Key"] == "receipt-idem-1"
    assert sent["X-Causation-Id"] == "cause-1"
    assert sent["X-Correlation-Id"] == "corr-entitlements"


def test_entitlement_order_reaches_the_wire_as_the_caller_sent_it(outbound) -> None:  # noqa: ANN001
    """A sorted or de-duplicated forward still contains every entry.

    Only an exact comparison of the whole string can tell a faithful forward from
    a rewritten one, so this pins the sequence rather than the membership.
    """
    outbound.payload = IDEA_CANDIDATE_DETAIL_EXAMPLE

    TestClient(app).get(
        "/api/v1/ideas/candidates/idea_cand_1",
        headers=_request_headers(),
    )

    sent = outbound.calls[0]["headers"]["X-Caller-Tenant-Ids"]
    assert sent.split(",") == ["tenant-sg", "tenant-hk", "tenant-ch"]
    assert sent != ",".join(sorted(["tenant-sg", "tenant-hk", "tenant-ch"]))
