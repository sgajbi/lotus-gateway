from app.contracts.dpm_command_center import DpmOutcomeReviewErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description=(
        "lotus-manage could not find the requested PM operating quality resource."
    ),
    conflict_description="lotus-manage rejected the PM operating quality request as conflicting.",
    invalid_payload_description=(
        "lotus-manage rejected the PM operating quality payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage PM operating quality authority is unavailable or degraded."
    ),
)
