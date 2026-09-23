from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from app.services.advisory_copilot_access_policy import (
    COPILOT_ACTION_RUN,
    COPILOT_PACKET_CREATE,
    COPILOT_PROPOSAL_PACKET_CREATE,
    COPILOT_PROPOSAL_RUNS_READ,
    COPILOT_RESOURCE_READ,
    COPILOT_REVIEW,
    AdvisoryCopilotCallerContext,
    AdvisoryCopilotOperation,
    require_advisory_copilot_caller_context,
)


@dataclass(frozen=True)
class AdvisoryCopilotCallerHeaders:
    actor_id: str
    tenant_id: str
    legal_entity_code: str
    role: str
    capabilities: str
    principal_status: str
    authorized_proposal_id: str | None
    authorized_portfolio_id: str | None


@dataclass(frozen=True)
class AdvisoryCopilotBaseCallerHeaders:
    actor_id: str
    tenant_id: str
    legal_entity_code: str
    role: str
    capabilities: str
    principal_status: str


def advisory_copilot_base_caller_headers(
    actor_id: Annotated[str, Header(alias="X-Actor-Id")],
    tenant_id: Annotated[str, Header(alias="X-Tenant-Id")],
    legal_entity_code: Annotated[str, Header(alias="X-Legal-Entity-Code")],
    role: Annotated[str, Header(alias="X-Role")],
    capabilities: Annotated[str, Header(alias="X-Caller-Capabilities")],
    principal_status: Annotated[str, Header(alias="X-Principal-Status")],
) -> AdvisoryCopilotBaseCallerHeaders:
    return AdvisoryCopilotBaseCallerHeaders(
        actor_id=actor_id,
        tenant_id=tenant_id,
        legal_entity_code=legal_entity_code,
        role=role,
        capabilities=capabilities,
        principal_status=principal_status,
    )


AdvisoryCopilotBaseCallerHeaderInputs = Annotated[
    AdvisoryCopilotBaseCallerHeaders,
    Depends(advisory_copilot_base_caller_headers),
]


def _caller_headers(
    base: AdvisoryCopilotBaseCallerHeaders,
    *,
    authorized_proposal_id: str | None = None,
    authorized_portfolio_id: str | None = None,
) -> AdvisoryCopilotCallerHeaders:
    return AdvisoryCopilotCallerHeaders(
        **base.__dict__,
        authorized_proposal_id=authorized_proposal_id,
        authorized_portfolio_id=authorized_portfolio_id,
    )


def admit_advisory_copilot_caller(
    *,
    operation: AdvisoryCopilotOperation,
    caller_headers: AdvisoryCopilotCallerHeaders,
) -> AdvisoryCopilotCallerContext:
    return require_advisory_copilot_caller_context(
        operation=operation,
        actor_id=caller_headers.actor_id,
        tenant_id=caller_headers.tenant_id,
        legal_entity_code=caller_headers.legal_entity_code,
        role=caller_headers.role,
        capabilities=caller_headers.capabilities,
        principal_status=caller_headers.principal_status,
        authorized_proposal_id=caller_headers.authorized_proposal_id,
        authorized_portfolio_id=caller_headers.authorized_portfolio_id,
    )


def advisory_copilot_packet_caller(
    base: AdvisoryCopilotBaseCallerHeaderInputs,
    authorized_portfolio_id: Annotated[str, Header(alias="X-Authorized-Portfolio-Id")],
    authorized_proposal_id: Annotated[str | None, Header(alias="X-Authorized-Proposal-Id")] = None,
) -> AdvisoryCopilotCallerContext:
    return admit_advisory_copilot_caller(
        operation=COPILOT_PACKET_CREATE,
        caller_headers=_caller_headers(
            base,
            authorized_proposal_id=authorized_proposal_id,
            authorized_portfolio_id=authorized_portfolio_id,
        ),
    )


def advisory_copilot_proposal_packet_caller(
    base: AdvisoryCopilotBaseCallerHeaderInputs,
    authorized_proposal_id: Annotated[str, Header(alias="X-Authorized-Proposal-Id")],
    authorized_portfolio_id: Annotated[str, Header(alias="X-Authorized-Portfolio-Id")],
) -> AdvisoryCopilotCallerContext:
    return admit_advisory_copilot_caller(
        operation=COPILOT_PROPOSAL_PACKET_CREATE,
        caller_headers=_caller_headers(
            base,
            authorized_proposal_id=authorized_proposal_id,
            authorized_portfolio_id=authorized_portfolio_id,
        ),
    )


def advisory_copilot_read_caller(
    base: AdvisoryCopilotBaseCallerHeaderInputs,
    authorized_proposal_id: Annotated[str | None, Header(alias="X-Authorized-Proposal-Id")] = None,
    authorized_portfolio_id: Annotated[
        str | None, Header(alias="X-Authorized-Portfolio-Id")
    ] = None,
) -> AdvisoryCopilotCallerContext:
    return admit_advisory_copilot_caller(
        operation=COPILOT_RESOURCE_READ,
        caller_headers=_caller_headers(
            base,
            authorized_proposal_id=authorized_proposal_id,
            authorized_portfolio_id=authorized_portfolio_id,
        ),
    )


def advisory_copilot_action_caller(
    base: AdvisoryCopilotBaseCallerHeaderInputs,
    authorized_portfolio_id: Annotated[str, Header(alias="X-Authorized-Portfolio-Id")],
    authorized_proposal_id: Annotated[str | None, Header(alias="X-Authorized-Proposal-Id")] = None,
) -> AdvisoryCopilotCallerContext:
    return admit_advisory_copilot_caller(
        operation=COPILOT_ACTION_RUN,
        caller_headers=_caller_headers(
            base,
            authorized_proposal_id=authorized_proposal_id,
            authorized_portfolio_id=authorized_portfolio_id,
        ),
    )


def advisory_copilot_review_caller(
    base: AdvisoryCopilotBaseCallerHeaderInputs,
    authorized_proposal_id: Annotated[str, Header(alias="X-Authorized-Proposal-Id")],
    authorized_portfolio_id: Annotated[str, Header(alias="X-Authorized-Portfolio-Id")],
) -> AdvisoryCopilotCallerContext:
    return admit_advisory_copilot_caller(
        operation=COPILOT_REVIEW,
        caller_headers=_caller_headers(
            base,
            authorized_proposal_id=authorized_proposal_id,
            authorized_portfolio_id=authorized_portfolio_id,
        ),
    )


def advisory_copilot_proposal_runs_caller(
    base: AdvisoryCopilotBaseCallerHeaderInputs,
    authorized_proposal_id: Annotated[str, Header(alias="X-Authorized-Proposal-Id")],
    authorized_portfolio_id: Annotated[
        str | None, Header(alias="X-Authorized-Portfolio-Id")
    ] = None,
) -> AdvisoryCopilotCallerContext:
    return admit_advisory_copilot_caller(
        operation=COPILOT_PROPOSAL_RUNS_READ,
        caller_headers=_caller_headers(
            base,
            authorized_proposal_id=authorized_proposal_id,
            authorized_portfolio_id=authorized_portfolio_id,
        ),
    )


AdvisoryCopilotPacketCaller = Annotated[
    AdvisoryCopilotCallerContext,
    Depends(advisory_copilot_packet_caller),
]
AdvisoryCopilotProposalPacketCaller = Annotated[
    AdvisoryCopilotCallerContext,
    Depends(advisory_copilot_proposal_packet_caller),
]
AdvisoryCopilotReadCaller = Annotated[
    AdvisoryCopilotCallerContext,
    Depends(advisory_copilot_read_caller),
]
AdvisoryCopilotActionCaller = Annotated[
    AdvisoryCopilotCallerContext,
    Depends(advisory_copilot_action_caller),
]
AdvisoryCopilotReviewCaller = Annotated[
    AdvisoryCopilotCallerContext,
    Depends(advisory_copilot_review_caller),
]
AdvisoryCopilotProposalRunsCaller = Annotated[
    AdvisoryCopilotCallerContext,
    Depends(advisory_copilot_proposal_runs_caller),
]
