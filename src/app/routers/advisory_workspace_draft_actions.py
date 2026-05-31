from fastapi import APIRouter

from app.contracts.advisory_workspaces import (
    AdvisoryWorkspaceBodyRequest,
    AdvisoryWorkspaceEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


@router.post(
    "/{workspace_id}/draft-actions",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Apply Advisory Workspace Draft Action",
    description=(
        "Applies a draft trade, cash-flow, or option action through lotus-advise and returns "
        "the re-evaluated workspace posture."
    ),
)
async def apply_draft_action(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().apply_draft_action(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
