from fastapi import APIRouter, Header

from app.contracts.advisory_workspaces import (
    AdvisoryWorkspaceBodyRequest,
    AdvisoryWorkspaceEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


@router.post(
    "/{workspace_id}/handoff",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Handoff Advisory Workspace to Proposal Lifecycle",
    description=(
        "Persists the evaluated workspace draft into the lotus-advise proposal lifecycle. "
        "Gateway forwards the request and does not synthesize proposal evidence locally."
    ),
)
async def handoff_workspace(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for workspace-to-proposal handoff.",
        examples=["idem-workspace-handoff-1"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().handoff_workspace(
        workspace_id=workspace_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
