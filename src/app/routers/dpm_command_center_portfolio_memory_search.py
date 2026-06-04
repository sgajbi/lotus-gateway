from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewErrorDetail,
    DpmPortfolioMemoryGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_command_center_service

_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description="lotus-manage could not find the requested command-center resource.",
    conflict_description="lotus-manage rejected the command-center request as conflicting.",
    invalid_payload_description="lotus-manage rejected the command-center payload as invalid.",
    unavailable_description="lotus-manage command-center authority is unavailable or degraded.",
)

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=_UPSTREAM_ERROR_RESPONSES,
)


@dataclass(frozen=True)
class PortfolioMemorySearchFilters:
    portfolio_ids: list[str] | None
    event_type: str | None
    supportability_state: str | None
    source_system: str | None
    source_type: str | None
    limit: int
    offset: int
    source_scan_limit: int | None

    def as_filters(self) -> dict[str, Any]:
        return {
            "portfolio_ids": self.portfolio_ids,
            "event_type": self.event_type,
            "supportability_state": self.supportability_state,
            "source_system": self.source_system,
            "source_type": self.source_type,
            "limit": self.limit,
            "offset": self.offset,
            "source_scan_limit": self.source_scan_limit,
        }


def build_portfolio_memory_search_filters(
    portfolio_ids: list[str] | None = Query(
        default=None,
        description="Optional repeated portfolio identifiers for bounded persisted memory search.",
        examples=[["PB_SG_GLOBAL_BAL_001", "PB_SG_GLOBAL_INC_002"]],
    ),
    event_type: str | None = Query(
        default=None,
        description="Optional manage-owned portfolio-memory event type filter.",
        examples=["OUTCOME_REVIEW_CREATED"],
    ),
    supportability_state: str | None = Query(
        default=None,
        description="Optional manage-published supportability state filter.",
        examples=["READY"],
    ),
    source_system: str | None = Query(
        default=None,
        description="Optional persisted source-system filter.",
        examples=["lotus-performance"],
    ),
    source_type: str | None = Query(
        default=None,
        description="Optional persisted source-type filter.",
        examples=["PortfolioRealizedTaxSummary:v1"],
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
        description="Maximum number of persisted memory events to return.",
        examples=[25],
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Manage-local offset for bounded persisted memory search.",
        examples=[0],
    ),
    source_scan_limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional Manage-local scan cap for source-lineage facet derivation.",
        examples=[250],
    ),
) -> PortfolioMemorySearchFilters:
    return PortfolioMemorySearchFilters(
        portfolio_ids=portfolio_ids,
        event_type=event_type,
        supportability_state=supportability_state,
        source_system=source_system,
        source_type=source_type,
        limit=limit,
        offset=offset,
        source_scan_limit=source_scan_limit,
    )


async def _search_portfolio_memory(
    filters: PortfolioMemorySearchFilters,
) -> DpmPortfolioMemoryGatewayResponse:
    return await dpm_command_center_service().search_portfolio_memory(
        filters=filters.as_filters(),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/portfolio-memory/search",
    response_model=DpmPortfolioMemoryGatewayResponse,
    summary="Search DPM portfolio memory by persisted source lineage",
    description=(
        "What: forwards bounded manage-local portfolio-memory search filters, including source "
        "system and source type, to lotus-manage. When: use this for source-family posture over "
        "persisted memory evidence before selecting a portfolio timeline. How: Gateway preserves "
        "the Manage search payload, applied filters, source counts, reason codes, boundaries, and "
        "content hashes without querying source-owner stores, discovering the global portfolio "
        "universe, reconstructing raw source payloads, or claiming OMS, execution, client "
        "communication, fill, or settlement truth."
    ),
)
async def search_portfolio_memory(
    filters: PortfolioMemorySearchFilters = Depends(build_portfolio_memory_search_filters),
) -> DpmPortfolioMemoryGatewayResponse:
    return await _search_portfolio_memory(filters)
