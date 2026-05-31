from fastapi import APIRouter

from app.contracts.advisory_workspaces import AdvisoryWorkspaceEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


async def _evaluate_workspace(workspace_id: str) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().evaluate_workspace(
        workspace_id=workspace_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{workspace_id}/evaluate",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Evaluate Advisory Workspace",
    description="Re-evaluates the current advisory workspace draft through lotus-advise.",
)
async def evaluate_workspace(
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _evaluate_workspace(workspace_id)
