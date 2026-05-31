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
    "/{workspace_id}/assistant/rationale",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Request Advisory Workspace Rationale",
    description=(
        "Requests an evidence-grounded workspace rationale through lotus-advise and its "
        "Lotus AI seam. Gateway does not generate advisory rationale or prompts locally."
    ),
)
async def request_rationale(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().request_rationale(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{workspace_id}/assistant/rationale/review-actions",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Review Advisory Workspace Rationale Run",
    description=(
        "Applies a bounded review action to the Lotus AI rationale run through lotus-advise, "
        "preserving run-ledger and replacement-lineage posture without Gateway rewriting."
    ),
)
async def review_rationale(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().review_rationale(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
