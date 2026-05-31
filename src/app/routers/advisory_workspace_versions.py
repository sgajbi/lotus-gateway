from fastapi import APIRouter

from app.contracts.advisory_workspaces import (
    AdvisoryWorkspaceBodyRequest,
    AdvisoryWorkspaceEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


async def _save_workspace(
    *,
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().save_workspace(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{workspace_id}/save",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Save Advisory Workspace Version",
    description="Saves the current advisory workspace draft version in lotus-advise.",
)
async def save_workspace(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _save_workspace(
        request=request,
        workspace_id=workspace_id,
    )
