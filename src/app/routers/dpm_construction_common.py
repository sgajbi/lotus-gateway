from app.contracts.dpm_construction import DpmConstructionErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_CONSTRUCTION_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmConstructionErrorDetail,
    conflict_description="lotus-manage rejected the construction request.",
    invalid_payload_description="lotus-manage rejected the construction payload as invalid.",
    unavailable_description="lotus-manage construction authority is unavailable or degraded.",
)
