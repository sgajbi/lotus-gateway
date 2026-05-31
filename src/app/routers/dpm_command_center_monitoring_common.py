from app.contracts.dpm_command_center import DpmOutcomeReviewErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description="lotus-manage could not find the requested command-center resource.",
    conflict_description="lotus-manage rejected the command-center request as conflicting.",
    invalid_payload_description="lotus-manage rejected the command-center payload as invalid.",
    unavailable_description="lotus-manage command-center authority is unavailable or degraded.",
)
