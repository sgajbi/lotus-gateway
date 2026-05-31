from fastapi import APIRouter, Query

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmWaveErrorDetail,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign discovery resource.",
    conflict_description="lotus-manage rejected the campaign discovery request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign discovery payload as invalid.",
    unavailable_description="lotus-manage campaign discovery authority is unavailable or degraded.",
)


@router.get(
    "/campaign-discovery",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Discover DPM bulk-review campaigns",
    description=(
        "What: retrieves the bounded manage-owned BulkReviewCampaignDiscovery:v1 read model for "
        "persisted campaign definitions. When: use this for Workbench campaign operating review, "
        "expiry posture, governance posture, and candidate-count context. How: Gateway forwards "
        "filters to lotus-manage and preserves the discovery payload without discovering the "
        "global portfolio universe, recalculating source facts, inferring campaign membership, "
        "running maker-checker workflow, or claiming OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def discover_campaigns(
    campaign_id: str | None = Query(default=None, description="Optional campaign id filter."),
    campaign_status: str | None = Query(
        default="ACTIVE", description="Optional campaign status filter."
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional campaign as-of date filter.",
        examples=["2026-05-14"],
    ),
    active_on: str | None = Query(
        default=None,
        description="Optional ISO date used by lotus-manage to classify expiry posture.",
        examples=["2026-05-16"],
    ),
    include_expired: bool = Query(
        default=False,
        description=(
            "Whether lotus-manage should include expired campaigns when active_on is supplied."
        ),
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum campaigns to return."),
    offset: int = Query(default=0, ge=0, description="Zero-based campaign-discovery offset."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().discover_campaigns(
        filters={
            "campaign_id": campaign_id,
            "campaign_status": campaign_status,
            "as_of_date": as_of_date,
            "active_on": active_on,
            "include_expired": include_expired,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )
