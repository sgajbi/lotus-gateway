from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_CAMPAIGN_DEFINITION_LOOKUP_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign definition.",
    conflict_description="lotus-manage rejected the campaign-definition request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign-definition payload as invalid.",
    unavailable_description=(
        "lotus-manage campaign-definition authority is unavailable or degraded."
    ),
)
