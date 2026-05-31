from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_WAVE_ACTION_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested rebalance wave action.",
    conflict_description="lotus-manage rejected the rebalance-wave action as conflicting.",
    invalid_payload_description=(
        "lotus-manage rejected the rebalance-wave action payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage rebalance-wave action authority is unavailable or degraded."
    ),
)
