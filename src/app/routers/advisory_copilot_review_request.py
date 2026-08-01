from typing import Annotated

from fastapi import Depends, Header

from app.services.advisory_copilot_review_access_policy import (
    AdvisoryCopilotReviewCallerContext,
    require_advisory_copilot_review_caller_context,
)


def advisory_copilot_review_caller_context(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    legal_entity_code: Annotated[str | None, Header(alias="X-Legal-Entity-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
    principal_status: Annotated[str | None, Header(alias="X-Principal-Status")] = None,
    authorized_proposal_id: Annotated[str | None, Header(alias="X-Authorized-Proposal-Id")] = None,
    authorized_portfolio_id: Annotated[
        str | None, Header(alias="X-Authorized-Portfolio-Id")
    ] = None,
) -> AdvisoryCopilotReviewCallerContext:
    return require_advisory_copilot_review_caller_context(
        actor_id=actor_id,
        tenant_id=tenant_id,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
        principal_status=principal_status,
        authorized_proposal_id=authorized_proposal_id,
        authorized_portfolio_id=authorized_portfolio_id,
    )


AdvisoryCopilotReviewCaller = Annotated[
    AdvisoryCopilotReviewCallerContext,
    Depends(advisory_copilot_review_caller_context),
]
