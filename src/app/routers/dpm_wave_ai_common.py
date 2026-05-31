from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_WAVE_AI_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested rebalance wave AI evidence.",
    conflict_description=(
        "lotus-manage rejected the rebalance-wave AI handoff request as conflicting."
    ),
    invalid_payload_description=(
        "lotus-manage rejected the rebalance-wave AI handoff payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage rebalance-wave AI handoff authority is unavailable or degraded."
    ),
)
