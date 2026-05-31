from fastapi import APIRouter

from app.contracts.advisory_workspaces import AdvisoryWorkspaceEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


async def _list_saved_versions(workspace_id: str) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().list_saved_versions(
        workspace_id=workspace_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{workspace_id}/saved-versions",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="List Saved Advisory Workspace Versions",
    description=(
        "Returns saved advisory workspace versions from lotus-advise for resume, compare, "
        "and support evidence workflows. Gateway does not reconstruct workspace history locally."
    ),
)
async def list_saved_versions(
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _list_saved_versions(workspace_id)
