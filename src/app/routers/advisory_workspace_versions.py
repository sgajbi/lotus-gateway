from fastapi import APIRouter, Path

from app.contracts.advisory_workspaces import (
    AdvisoryWorkspaceBodyRequest,
    AdvisoryWorkspaceEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_workspace_common import WORKSPACE_ID_PATH
from app.services.advisory_service_provider import advisory_workspace_service

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


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
    return await advisory_workspace_service().save_workspace(
        workspace_id=workspace_id,
        body=request.body,
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
    return await advisory_workspace_service().list_saved_versions(
        workspace_id=workspace_id,
        correlation_id=correlation_id_var.get(),
    )


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


@router.post(
    "/{workspace_id}/resume",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Resume Saved Advisory Workspace Version",
    description=(
        "Restores a saved advisory workspace version into the editable draft through lotus-advise."
    ),
)
async def resume_workspace(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().resume_workspace(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{workspace_id}/compare",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Compare Advisory Workspace Draft",
    description=(
        "Compares the current workspace draft against a saved version through lotus-advise. "
        "Gateway preserves the returned comparison evidence unchanged."
    ),
)
async def compare_workspace(
    request: AdvisoryWorkspaceBodyRequest,
    workspace_id: str = WORKSPACE_ID_PATH,
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await advisory_workspace_service().compare_workspace(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
