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

from collections.abc import Callable

from app.services.advisory_policy_access_policy import (
    POLICY_CONTROL_SERVICE_IDENTITY,
    AdvisoryPolicyCallerContext,
)

HeaderFactory = Callable[[str, dict[str, str] | None], dict[str, str]]


def build_policy_control_headers(
    headers_factory: HeaderFactory,
    correlation_id: str,
    *,
    caller: AdvisoryPolicyCallerContext,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    extras = {
        "X-Actor-Id": caller.actor_id,
        "X-Role": caller.role,
        "X-Tenant-Id": caller.tenant_id,
        "X-Legal-Entity-Code": caller.legal_entity_code,
        "X-Service-Identity": POLICY_CONTROL_SERVICE_IDENTITY,
        "X-Capabilities": caller.capability,
    }
    if caller.authorized_proposal_id is not None:
        extras["X-Authorized-Proposal-Id"] = caller.authorized_proposal_id
    if caller.authorized_portfolio_id is not None:
        extras["X-Authorized-Portfolio-Id"] = caller.authorized_portfolio_id
    if idempotency_key is not None:
        extras["Idempotency-Key"] = idempotency_key
    return headers_factory(correlation_id, extras)
