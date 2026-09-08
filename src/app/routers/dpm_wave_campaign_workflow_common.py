from typing import Any

from fastapi import APIRouter, Request

from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.routers.query_params import query_params_with_repeated_values

UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign workflow view.",
    conflict_description="lotus-manage rejected the campaign workflow view request as conflicting.",
    invalid_payload_description=(
        "lotus-manage rejected the campaign workflow view payload as invalid."
    ),
    unavailable_description="lotus-manage campaign workflow views are unavailable or degraded.",
)


def campaign_workflow_query_params(request: Request) -> dict[str, Any]:
    return query_params_with_repeated_values(request.query_params)


def campaign_wave_router() -> APIRouter:
    """One campaign-wave router construction, not twenty-five identical copies.

    The campaign surface is split across twenty-five modules so each route keeps
    its own OpenAPI description, and every one of them mounts under the same
    prefix and tag. Repeating that construction is how one module ends up mounted
    somewhere its siblings are not, which no test would catch because each file
    is individually correct.
    """

    return APIRouter(
        prefix="/api/v1/dpm/command-center/waves",
        tags=["DPM Command Center"],
    )
