from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewForwardRequest,
    DpmOutcomeReviewGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


@dataclass(frozen=True)
class OutcomeReviewCallerContext:
    actor_id: str
    tenant_id: str
    region: str
    role: str
    service_identity: str
    capabilities: str

    def as_upstream_headers(self) -> dict[str, str]:
        return {
            "X-Actor-Id": self.actor_id,
            "X-Tenant-Id": self.tenant_id,
            "X-Region": self.region,
            "X-Role": self.role,
            "X-Service-Identity": self.service_identity,
            "X-Capabilities": self.capabilities,
        }


def outcome_review_caller_context(
    actor_id: Annotated[str, Header(alias="X-Actor-Id", min_length=1)],
    tenant_id: Annotated[str, Header(alias="X-Tenant-Id", min_length=1)],
    region: Annotated[str, Header(alias="X-Region", min_length=1)],
    role: Annotated[str, Header(alias="X-Role", min_length=1)],
    service_identity: Annotated[str, Header(alias="X-Service-Identity", min_length=1)],
    capabilities: Annotated[str, Header(alias="X-Capabilities", min_length=1)],
) -> OutcomeReviewCallerContext:
    return OutcomeReviewCallerContext(
        actor_id=actor_id,
        tenant_id=tenant_id,
        region=region,
        role=role,
        service_identity=service_identity,
        capabilities=capabilities,
    )


async def _create_outcome_review(
    *,
    request: DpmOutcomeReviewForwardRequest,
    idempotency_key: str,
    caller_context: OutcomeReviewCallerContext,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().create_outcome_review(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
        caller_headers=caller_context.as_upstream_headers(),
    )


@router.post(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Create outcome review",
    description=(
        "What: creates a persisted post-trade outcome review in lotus-manage. When: call this "
        "after execution evidence is available and a DPM or operations workflow needs an "
        "immutable review object. How: Gateway forwards the create payload unchanged and "
        "preserves manage-owned identifiers, state, hashes, lineage, and supportability."
    ),
)
async def create_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
    caller_context: Annotated[
        OutcomeReviewCallerContext,
        Depends(outcome_review_caller_context),
    ],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="Caller-supplied idempotency key forwarded unchanged to lotus-manage.",
        ),
    ],
) -> DpmOutcomeReviewGatewayResponse:
    return await _create_outcome_review(
        request=request,
        idempotency_key=idempotency_key,
        caller_context=caller_context,
    )
