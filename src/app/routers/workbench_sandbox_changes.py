from fastapi import APIRouter, Path

from app.contracts.workbench import (
    WorkbenchSandboxApplyChangesRequest,
    WorkbenchSandboxStateResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import workbench_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


async def _apply_sandbox_changes(
    *,
    request: WorkbenchSandboxApplyChangesRequest,
    portfolio_id: str,
    session_id: str,
) -> WorkbenchSandboxStateResponse:
    service = workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.apply_sandbox_changes(
        portfolio_id=portfolio_id,
        session_id=session_id,
        correlation_id=correlation_id,
        changes=[item.model_dump(exclude_none=True, mode="json") for item in request.changes],
        evaluate_policy=request.evaluate_policy,
    )


@router.post(
    "/{portfolio_id}/sandbox/sessions/{session_id}/changes",
    response_model=WorkbenchSandboxStateResponse,
    summary="Apply Workbench Sandbox Changes",
    description=(
        "Applies ordered sandbox changes to an existing session and returns the refreshed "
        "projected holdings plus optional policy feedback. Use this route for every incremental "
        "what-if adjustment after the session exists."
    ),
)
async def apply_sandbox_changes(
    request: WorkbenchSandboxApplyChangesRequest,
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the sandbox session being updated.",
        examples=["PF_1001"],
    ),
    session_id: str = Path(
        ...,
        description="Active sandbox session identifier that will receive the proposed changes.",
        examples=["sess_1"],
    ),
) -> WorkbenchSandboxStateResponse:
    return await _apply_sandbox_changes(
        request=request,
        portfolio_id=portfolio_id,
        session_id=session_id,
    )
