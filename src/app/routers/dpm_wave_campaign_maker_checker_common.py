from typing import Any

from fastapi import Request

from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.routers.query_params import query_params_with_repeated_values

UPSTREAM_CAMPAIGN_MAKER_CHECKER_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign workflow resource.",
    conflict_description="lotus-manage rejected the campaign workflow request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign workflow payload as invalid.",
    unavailable_description="lotus-manage campaign workflow authority is unavailable or degraded.",
)


def campaign_maker_checker_query_params(request: Request) -> dict[str, Any]:
    return query_params_with_repeated_values(request.query_params)
