from fastapi import APIRouter

from app.contracts.advisory_workspaces import AdvisoryWorkspaceEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


async def _get_workspace(workspace_id: str) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().get_workspace(
        workspace_id=workspace_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{workspace_id}",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Get Advisory Workspace",
    description="Returns the current advisory workspace session from lotus-advise.",
)
async def get_workspace(
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _get_workspace(workspace_id)
