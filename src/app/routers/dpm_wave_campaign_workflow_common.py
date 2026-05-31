from typing import Any

from fastapi import Request

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
