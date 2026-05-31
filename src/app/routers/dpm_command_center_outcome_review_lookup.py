from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Query

from app.contracts.dpm_command_center import DpmOutcomeReviewGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


@dataclass(frozen=True)
class OutcomeReviewListFilters:
    portfolio_id: str | None
    rebalance_run_id: str | None
    wave_id: str | None
    state: str | None
    source_system: str | None
    source_type: str | None
    limit: int
    offset: int | None
    source_scan_limit: int | None
    cursor: str | None

    def as_filters(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "rebalance_run_id": self.rebalance_run_id,
            "wave_id": self.wave_id,
            "state": self.state,
            "source_system": self.source_system,
            "source_type": self.source_type,
            "limit": self.limit,
            "offset": self.offset,
            "source_scan_limit": self.source_scan_limit,
            "cursor": self.cursor,
        }


async def _list_outcome_reviews(
    filters: OutcomeReviewListFilters,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().list_outcome_reviews(
        filters=filters.as_filters(),
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
    return await _list_outcome_reviews(
        OutcomeReviewListFilters(
            portfolio_id=portfolio_id,
            rebalance_run_id=rebalance_run_id,
            wave_id=wave_id,
            state=state,
            source_system=source_system,
            source_type=source_type,
            limit=limit,
            offset=offset,
            source_scan_limit=source_scan_limit,
            cursor=cursor,
        )
    )
