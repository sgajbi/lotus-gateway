"""Advisory-policy writes carry the caller's scope, and refuse before reaching Advise.

These routes used to send `X-Tenant-Id: tenant_sg_001` from a module constant,
with the role and capability chosen by Gateway and the actor read out of the
request body behind a fallback. Nothing was admitted, so nothing could be
propagated.

The transport is patched at `AdviseClient._post` / `_get` rather than at the
client's public methods, so every layer under test is the real one: the route
admits, the service threads, the client builds the outbound headers. A fake
standing in for the client would be asserting against the fake's own shape --
which is how a previous set of fakes in this estate hid four defects at once.

Two claims are made here, and they are different:

* **Refusal happens before I/O.** Not merely that the response is 400 or 403,
  but that `_post` was never reached. A caller without scope must not touch
  lotus-advise at all.
* **What is forwarded is the caller's.** The outbound `X-Tenant-Id` is the one
  the caller presented, and the seeded constant appears nowhere.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app

# The tenant the routes used to assert unconditionally. Named here so a
# reintroduction fails loudly rather than passing as "some tenant".
RETIRED_MINTED_TENANT = "tenant_sg_001"

CALLER_TENANT = "tenant_ch_004"
CALLER_ACTOR = "advisor_zoe"
CALLER_LEGAL_ENTITY = "CH_ZURICH"

# route -> (method, path, body, required role, required capability, idempotency)
WRITE_ROUTES: dict[str, tuple[str, str, dict[str, Any], str, str, str | None]] = {
    "policy_pack.validate": (
        "post",
        "/api/v1/advisory-policy-packs/pp_sg/versions/2026.05/validate",
        {"body": {"requested_by": "someone_else"}},
        "POLICY_STEWARD",
        "advisory.policy_pack.validate",
        "idem-validate-1",
    ),
    "policy_pack.activate": (
        "post",
        "/api/v1/advisory-policy-packs/pp_sg/versions/2026.05/activate",
        {"body": {"activated_by": "someone_else"}},
        "POLICY_CHECKER",
        "advisory.policy_pack.activate",
        "idem-activate-1",
    ),
    "policy_evaluation.finalize": (
        "post",
        "/api/v1/proposals/pp_001/versions/ppv_001/policy-evaluations",
        {"body": {"created_by": "someone_else"}},
        "ADVISOR",
        "advisory.policy_evaluation.finalize",
        "idem-create-1",
    ),
    "policy_evaluation.review_event": (
        "post",
        "/api/v1/advisory-policy-evaluations/pev_001/events",
        {"body": {"actor_id": "someone_else"}},
        "COMPLIANCE_REVIEWER",
        "advisory.policy_evaluation.review_event",
        None,
    ),
    "policy_evaluation.sign_off": (
        "post",
        "/api/v1/advisory-policy-evaluations/pev_001/sign-off-decisions",
        {"body": {"decided_by": "someone_else"}},
        "POLICY_CHECKER",
        "advisory.policy_evaluation.sign_off",
        None,
    ),
    "policy_evaluation.report_package": (
        "post",
        "/api/v1/advisory-policy-evaluations/pev_001/report-packages",
        {"body": {"requested_by": "someone_else"}},
        "POLICY_CHECKER",
        "advisory.policy_evaluation.report_package",
        None,
    ),
    "policy_evaluation.ai_evidence": (
        "post",
        "/api/v1/advisory-policy-evaluations/pev_001/ai-evidence",
        {"body": {"requested_by": "someone_else"}},
        "COMPLIANCE_REVIEWER",
        "advisory.policy_evaluation.ai_evidence",
        None,
    ),
}


class _Transport:
    """Records every outbound call the real client would have made."""

    def __init__(self) -> None:
        self.posts: list[dict[str, Any]] = []
        self.gets: list[dict[str, Any]] = []

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        transport = self

        async def _post(  # noqa: ANN001
            self, path, body, headers, operation, params=None
        ) -> tuple[int, dict[str, Any]]:
            _ = self
            transport.posts.append({"path": path, "headers": headers, "operation": operation})
            return 200, {"accepted": True}

        async def _get(self, path, params, headers, operation) -> tuple[int, dict[str, Any]]:  # noqa: ANN001
            _ = self
            transport.gets.append({"path": path, "headers": headers})
            # The evaluation-action paths read the record first to derive the
            # authorized proposal/portfolio headers.
            return 200, {"proposal_id": "pp_001", "portfolio_id": "PORT_001"}

        monkeypatch.setattr("app.clients.advise_client.AdviseClient._post", _post)
        monkeypatch.setattr("app.clients.advise_client.AdviseClient._get", _get)


def _headers(
    *,
    role: str | None,
    capabilities: str | None,
    tenant: str | None = CALLER_TENANT,
    actor: str | None = CALLER_ACTOR,
    legal_entity: str | None = CALLER_LEGAL_ENTITY,
    idempotency_key: str | None,
) -> dict[str, str]:
    sent = {
        "X-Correlation-Id": "corr-policy-scope",
        "X-Actor-Id": actor,
        "X-Tenant-Id": tenant,
        "X-Legal-Entity-Code": legal_entity,
        "X-Role": role,
        "X-Caller-Capabilities": capabilities,
        "Idempotency-Key": idempotency_key,
    }
    return {name: value for name, value in sent.items() if value is not None}


@pytest.mark.parametrize("operation", sorted(WRITE_ROUTES))
def test_admitted_scope_is_what_reaches_advise(operation, monkeypatch) -> None:
    """The caller's tenant, actor and role travel outbound; the constant does not."""
    method, path, body, role, capability, idempotency_key = WRITE_ROUTES[operation]
    transport = _Transport()
    transport.install(monkeypatch)

    response = getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(
            role=role,
            capabilities=f"{capability},unrelated.capability",
            idempotency_key=idempotency_key,
        ),
    )

    assert response.status_code == 200, response.text
    assert len(transport.posts) == 1, "exactly one upstream write per request"
    sent = transport.posts[0]["headers"]

    assert sent["X-Tenant-Id"] == CALLER_TENANT
    assert sent["X-Actor-Id"] == CALLER_ACTOR
    assert sent["X-Legal-Entity-Code"] == CALLER_LEGAL_ENTITY
    assert sent["X-Role"] == role
    # The capability EXERCISED, not the caller's whole set: the outbound claim is
    # as narrow as the act, so an unrelated capability the caller happens to hold
    # is not asserted to Advise.
    assert sent["X-Capabilities"] == capability
    # Gateway is genuinely the calling service; that claim stays.
    assert sent["X-Service-Identity"] == "lotus-gateway"


@pytest.mark.parametrize("operation", sorted(WRITE_ROUTES))
def test_the_retired_constant_is_never_sent(operation, monkeypatch) -> None:
    """No outbound header carries the seeded tenant, whatever the caller sent."""
    method, path, body, role, capability, idempotency_key = WRITE_ROUTES[operation]
    transport = _Transport()
    transport.install(monkeypatch)

    getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(role=role, capabilities=capability, idempotency_key=idempotency_key),
    )

    for call in transport.posts + transport.gets:
        assert RETIRED_MINTED_TENANT not in call["headers"].values(), (
            f"{operation} still asserts the seeded tenant: {call['headers']}"
        )


@pytest.mark.parametrize("operation", sorted(WRITE_ROUTES))
def test_missing_caller_context_is_refused_before_any_upstream_call(operation, monkeypatch) -> None:
    """400, and lotus-advise is never contacted.

    The status code alone would be satisfied by a route that calls upstream and
    then discards the result, so the absence of the outbound call is the claim.
    """
    method, path, body, _role, _capability, idempotency_key = WRITE_ROUTES[operation]
    transport = _Transport()
    transport.install(monkeypatch)

    response = getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(role=None, capabilities=None, idempotency_key=idempotency_key),
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "advisory_policy_caller_context_missing"
    assert transport.posts == [], "refused callers must not reach lotus-advise"
    assert transport.gets == [], "not even the record read that derives scope headers"


@pytest.mark.parametrize("operation", sorted(WRITE_ROUTES))
def test_a_foreign_role_is_refused_before_any_upstream_call(operation, monkeypatch) -> None:
    """A caller with the capability but the wrong role is refused, and does no I/O."""
    method, path, body, _role, capability, idempotency_key = WRITE_ROUTES[operation]
    transport = _Transport()
    transport.install(monkeypatch)

    response = getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(
            role="CLIENT_SERVICE_AGENT",
            capabilities=capability,
            idempotency_key=idempotency_key,
        ),
    )

    assert response.status_code == 403, response.text
    assert response.json()["code"] == "advisory_policy_access_denied"
    assert transport.posts == []
    assert transport.gets == []


@pytest.mark.parametrize("operation", sorted(WRITE_ROUTES))
def test_a_missing_capability_is_refused_before_any_upstream_call(operation, monkeypatch) -> None:
    """The right role without the capability is still refused.

    Role and capability are checked together and refused identically, so the
    response cannot be used to work out which of the two was lacking.
    """
    method, path, body, role, _capability, idempotency_key = WRITE_ROUTES[operation]
    transport = _Transport()
    transport.install(monkeypatch)

    response = getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(
            role=role,
            capabilities="advisory.something.else",
            idempotency_key=idempotency_key,
        ),
    )

    assert response.status_code == 403, response.text
    assert response.json()["code"] == "advisory_policy_access_denied"
    assert transport.posts == []


@pytest.mark.parametrize("operation", sorted(WRITE_ROUTES))
def test_the_body_cannot_supply_the_actor(operation, monkeypatch) -> None:
    """Authority in a business payload would let the caller choose their own scope.

    Every body in this suite carries `someone_else` in the field the old code read
    the actor from. The outbound actor must be the admitted one regardless.
    """
    method, path, body, role, capability, idempotency_key = WRITE_ROUTES[operation]
    transport = _Transport()
    transport.install(monkeypatch)

    getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(role=role, capabilities=capability, idempotency_key=idempotency_key),
    )

    assert transport.posts[0]["headers"]["X-Actor-Id"] == CALLER_ACTOR
    assert "someone_else" not in transport.posts[0]["headers"].values()


def test_a_malformed_tenant_is_refused(monkeypatch) -> None:
    """Tenant travels outbound as authority, so its shape is validated too.

    An unconstrained value would let a caller put ambiguous or header-breaking
    text into a field lotus-advise reads as scope.
    """
    method, path, body, role, capability, idempotency_key = WRITE_ROUTES[
        "policy_evaluation.finalize"
    ]
    transport = _Transport()
    transport.install(monkeypatch)

    response = getattr(TestClient(app), method)(
        path,
        json=body,
        headers=_headers(
            role=role,
            capabilities=capability,
            tenant="tenant with spaces",
            idempotency_key=idempotency_key,
        ),
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "advisory_policy_caller_context_invalid"
    assert transport.posts == []


def test_read_routes_are_unchanged_by_this_slice(monkeypatch) -> None:
    """Reads still require no caller context — deliberately, and it is a known gap.

    This slice corrects the WRITES, which minted authority. The read paths send no
    tenant at all, which is a separate defect with its own issue rather than
    something silently folded in here. Pinning the current behaviour keeps that
    honest: if reads start refusing, this test fails and the claim gets revisited.
    """
    transport = _Transport()
    transport.install(monkeypatch)

    response = TestClient(app).get(
        "/api/v1/advisory-policy-evaluations/pev_001",
        headers={"X-Correlation-Id": "corr-policy-read"},
    )

    assert response.status_code == 200
    assert len(transport.gets) == 1
    assert "X-Tenant-Id" not in transport.gets[0]["headers"]
