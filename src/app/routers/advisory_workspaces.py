from fastapi import APIRouter, Header, Path

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisory_workspaces import (
    AdvisoryWorkspaceBodyRequest,
    AdvisoryWorkspaceEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_workspace_service import AdvisoryWorkspaceService

router = APIRouter(prefix="/api/v1/advisory-workspaces", tags=["advisory-workspaces"])


def _advisory_workspace_service() -> AdvisoryWorkspaceService:
    return AdvisoryWorkspaceService(
        advise_client=AdviseClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        )
    )


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
    return await _advisory_workspace_service().create_workspace(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{workspace_id}",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Get Advisory Workspace",
    description="Returns the current advisory workspace session from lotus-advise.",
)
async def get_workspace(
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().get_workspace(
        workspace_id=workspace_id,
        correlation_id=correlation_id_var.get(),
    )


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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().apply_draft_action(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{workspace_id}/evaluate",
    response_model=AdvisoryWorkspaceEnvelopeResponse,
    summary="Evaluate Advisory Workspace",
    description="Re-evaluates the current advisory workspace draft through lotus-advise.",
)
async def evaluate_workspace(
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().evaluate_workspace(
        workspace_id=workspace_id,
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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().save_workspace(
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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().list_saved_versions(
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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
    workspace_version_id: str = Path(
        ...,
        description="Saved advisory workspace version identifier returned by lotus-advise.",
        examples=["awv_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().get_saved_version_replay_evidence(
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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().resume_workspace(
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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().compare_workspace(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().request_rationale(
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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().review_rationale(
        workspace_id=workspace_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


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
    workspace_id: str = Path(
        ...,
        description="Advisory workspace identifier returned by lotus-advise.",
        examples=["aws_001"],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for workspace-to-proposal handoff.",
        examples=["idem-workspace-handoff-1"],
    ),
) -> AdvisoryWorkspaceEnvelopeResponse:
    return await _advisory_workspace_service().handoff_workspace(
        workspace_id=workspace_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
