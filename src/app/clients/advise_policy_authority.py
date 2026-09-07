"""Outbound authority headers for advisory-policy writes, built from admitted scope.

Every value here that describes WHO is acting now comes from an
`AdvisoryPolicyCallerContext` admitted at the route. This module used to hold
`POLICY_CONTROL_TENANT_ID = "tenant_sg_001"` and a `body_actor` helper that read
the actor out of the request body behind a fallback; both are gone. A constant
that cannot be overridden is not a default, it is an assertion, and authority
arriving in a business payload lets the caller choose the scope their own call
runs under.

The one identity Gateway still asserts is its own: `X-Service-Identity`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.services.advisory_policy_access_policy import (
    POLICY_CONTROL_SERVICE_IDENTITY,
    AdvisoryPolicyCallerContext,
)

HeaderFactory = Callable[[str, dict[str, str] | None], dict[str, str]]
PolicyEvaluationReader = Callable[[str, str], Awaitable[tuple[int, dict[str, Any]]]]


def build_policy_control_headers(
    headers_factory: HeaderFactory,
    correlation_id: str,
    *,
    caller: AdvisoryPolicyCallerContext,
    idempotency_key: str | None = None,
    authorized_proposal_id: str | None = None,
    authorized_portfolio_id: str | None = None,
) -> dict[str, str]:
    extras = {
        "X-Actor-Id": caller.actor_id,
        "X-Role": caller.role,
        "X-Tenant-Id": caller.tenant_id,
        "X-Legal-Entity-Code": caller.legal_entity_code,
        "X-Service-Identity": POLICY_CONTROL_SERVICE_IDENTITY,
        "X-Capabilities": caller.capability,
    }
    if idempotency_key is not None:
        extras["Idempotency-Key"] = idempotency_key
    if authorized_proposal_id is not None:
        extras["X-Authorized-Proposal-Id"] = authorized_proposal_id
    if authorized_portfolio_id is not None:
        extras["X-Authorized-Portfolio-Id"] = authorized_portfolio_id
    return headers_factory(correlation_id, extras)


async def build_policy_evaluation_control_headers(
    *,
    read_policy_evaluation: PolicyEvaluationReader,
    headers_factory: HeaderFactory,
    evaluation_id: str,
    correlation_id: str,
    caller: AdvisoryPolicyCallerContext,
    idempotency_key: str | None,
) -> dict[str, str] | tuple[int, dict[str, Any]]:
    status_code, record = await read_policy_evaluation(evaluation_id, correlation_id)
    if status_code >= 400:
        return status_code, record
    return build_policy_control_headers(
        headers_factory,
        correlation_id,
        caller=caller,
        idempotency_key=idempotency_key,
        authorized_proposal_id=record_value(record, "proposal_id"),
        authorized_portfolio_id=record_value(record, "portfolio_id"),
    )


def evidence_portfolio_id(body: dict[str, Any]) -> str | None:
    """The portfolio named by the evidence bundle, for the authorized-scope header.

    Read from the body deliberately: this is a business reference to what the
    evaluation is ABOUT, not a claim about who may act. The authority headers no
    longer take anything from here.
    """
    evidence_bundle = body.get("evidence_bundle")
    if not isinstance(evidence_bundle, dict):
        return None
    inputs = evidence_bundle.get("inputs")
    if not isinstance(inputs, dict):
        return None
    portfolio_snapshot = inputs.get("portfolio_snapshot")
    if not isinstance(portfolio_snapshot, dict):
        return None
    portfolio_id = str(portfolio_snapshot.get("portfolio_id") or "").strip()
    return portfolio_id or None


def record_value(record: dict[str, Any], key: str) -> str | None:
    value = str(record.get(key) or "").strip()
    return value or None
