from fastapi import APIRouter, Path

from app.contracts.workbench import (
    WorkbenchSandboxSessionCreateRequest,
    WorkbenchSandboxStateResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import workbench_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


async def _create_sandbox_session(
    *,
    request: WorkbenchSandboxSessionCreateRequest,
    portfolio_id: str,
) -> WorkbenchSandboxStateResponse:
    service = workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.create_sandbox_session(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        created_by=request.created_by,
        ttl_hours=request.ttl_hours,
    )


@router.post(
    "/{portfolio_id}/sandbox/sessions",
    response_model=WorkbenchSandboxStateResponse,
    summary="Create Workbench Sandbox Session",
    description=(
        "Creates a lotus-core sandbox session for iterative advisory changes and returns the "
        "projected baseline state immediately. Use this route before the first simulated trade "
        "or rebalance adjustment for a portfolio."
    ),
)
async def create_sandbox_session(
    request: WorkbenchSandboxSessionCreateRequest,
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the sandbox session to be created.",
        examples=["PF_1001"],
    ),
) -> WorkbenchSandboxStateResponse:
    return await _create_sandbox_session(
        request=request,
        portfolio_id=portfolio_id,
    )
