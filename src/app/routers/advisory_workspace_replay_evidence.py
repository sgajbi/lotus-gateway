from fastapi import APIRouter, Path

from app.contracts.advisory_workspaces import AdvisoryWorkspaceEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


@router.get(
    "/{workspace_id}/saved-versions/{workspace_version_id}/replay-evidence",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Get Saved Advisory Workspace Replay Evidence",
    description=(
        "Returns replay evidence for a saved advisory workspace version from lotus-advise, "
        "preserving source hashes and lifecycle continuity without Gateway-side inference."
    ),
)
async def get_saved_version_replay_evidence(
    workspace_id: str = WORKSPACE_ID_PATH,
    workspace_version_id: str = Path(
        ...,
        description="Saved advisory workspace version identifier returned by lotus-advise.",
        examples=["awv_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().get_saved_version_replay_evidence(
        workspace_id=workspace_id,
        workspace_version_id=workspace_version_id,
        correlation_id=correlation_id_var.get(),
    )
