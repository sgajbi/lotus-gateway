from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_CAMPAIGN_LIFECYCLE_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description=(
        "lotus-manage could not find the requested campaign definition lifecycle resource."
    ),
    conflict_description="lotus-manage rejected the campaign lifecycle request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign lifecycle payload as invalid.",
    unavailable_description=(
        "lotus-manage campaign lifecycle authority is unavailable or degraded."
    ),
)
