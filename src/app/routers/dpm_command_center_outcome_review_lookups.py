from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import DpmOutcomeReviewGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


async def _get_run_outcome_review(
    *,
    rebalance_run_id: str,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_run_outcome_review(
        rebalance_run_id=rebalance_run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/runs/{rebalance_run_id}/outcome-review",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get run outcome review",
    description=(
        "What: resolves the outcome review linked to one manage rebalance run. When: call this "
        "from run-centric command-center views that need post-trade outcome state. How: Gateway "
        "delegates run lookup to manage and returns the linked RFC-0042 review payload."
    ),
)
async def get_run_outcome_review(
    rebalance_run_id: str = Path(
        ...,
        description="Manage-owned rebalance-run identifier.",
        examples=["rr_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _get_run_outcome_review(
        rebalance_run_id=rebalance_run_id,
    )
