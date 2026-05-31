from app.contracts.dpm_waves import DpmWaveErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_WAVE_LOOKUP_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested rebalance wave.",
    conflict_description="lotus-manage rejected the rebalance-wave request as conflicting.",
    invalid_payload_description="lotus-manage rejected the rebalance-wave payload as invalid.",
    unavailable_description="lotus-manage rebalance-wave authority is unavailable or degraded.",
)
