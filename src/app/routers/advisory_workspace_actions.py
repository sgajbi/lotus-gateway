from fastapi import APIRouter

from app.contracts.advisory_workspaces import (
    AdvisoryWorkspaceBodyRequest,
    AdvisoryWorkspaceEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


@router.post(
    "",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Create Advisory Workspace",
    description=(
        "Creates a stateful or stateless advisory workspace through lotus-advise. Use this "
        "for interactive proposal drafting where Advise owns context resolution, evaluation, "
        "replay evidence, save versions, and lifecycle handoff."
    ),
)
async def create_workspace(
    request: AdvisoryWorkspaceBodyRequest,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().create_workspace(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
