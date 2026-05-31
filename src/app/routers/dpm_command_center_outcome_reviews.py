from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewForwardRequest,
    DpmOutcomeReviewGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


@router.post(
    "/outcome-reviews/preview",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Preview outcome review",
    description=(
        "What: previews a post-trade expected-versus-realized outcome review through the "
        "lotus-manage RFC-0042 authority. When: call this before creating a persisted review "
        "to confirm source readiness, supportability, lineage, and expected review contents. "
        "How: Gateway forwards the request unchanged to manage and returns a BFF envelope with "
        "manage-published supportability; Gateway does not calculate outcome dimensions."
    ),
)
async def preview_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().preview_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Create outcome review",
    description=(
        "What: creates a persisted post-trade outcome review in lotus-manage. When: call this "
        "after execution evidence is available and a DPM or operations workflow needs an "
        "immutable review object. How: Gateway forwards the create payload unchanged and "
        "preserves manage-owned identifiers, state, hashes, lineage, and supportability."
    ),
)
async def create_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().create_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="List outcome reviews",
    description=(
        "What: lists manage-owned RFC-0042 outcome reviews for command-center triage. When: "
        "call this to populate DPM review queues by portfolio, run, wave, state, and source "
        "freshness posture. How: Gateway passes filters to manage and returns the authoritative "
        "list payload with a normalized supportability summary."
    ),
)
async def list_outcome_reviews(
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier filter for the outcome-review queue.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    rebalance_run_id: str | None = Query(
        default=None,
        description="Optional rebalance-run identifier filter.",
        examples=["rr_20260415_001"],
    ),
    wave_id: str | None = Query(
        default=None,
        description="Optional rebalance-wave identifier filter.",
        examples=["wave_20260415_sg_balanced"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional manage-published outcome-review state filter.",
        examples=["READY"],
    ),
    source_system: str | None = Query(
        default=None,
        description="Optional persisted source-system filter for Manage-local lineage facets.",
        examples=["lotus-performance"],
    ),
    source_type: str | None = Query(
        default=None,
        description="Optional persisted source-type filter for Manage-local lineage facets.",
        examples=["PortfolioCashMovementSummary:v1"],
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
        description="Maximum number of outcome-review records to return.",
        examples=[25],
    ),
    offset: int | None = Query(
        default=None,
        ge=0,
        description="Optional Manage-local offset for outcome-review source-lineage search.",
        examples=[0],
    ),
    source_scan_limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional Manage-local scan cap for outcome-review source-lineage facets.",
        examples=[250],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by manage.",
        examples=["or_cursor_0025"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    filters = {
        "portfolio_id": portfolio_id,
        "rebalance_run_id": rebalance_run_id,
        "wave_id": wave_id,
        "state": state,
        "source_system": source_system,
        "source_type": source_type,
        "limit": limit,
        "offset": offset,
        "source_scan_limit": source_scan_limit,
        "cursor": cursor,
    }
    return await dpm_command_center_service().list_outcome_reviews(
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review",
    description=(
        "What: returns one authoritative manage outcome review. When: call this for DPM "
        "detail, evidence inspection, and downstream report or AI handoff readiness checks. "
        "How: Gateway retrieves the manage review by id and preserves the manage payload "
        "without recalculating expected or realized outcomes."
    ),
)
async def get_outcome_review(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )
