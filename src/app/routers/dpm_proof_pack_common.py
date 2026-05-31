from app.contracts.dpm_proof_packs import DpmProofPackErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_PROOF_PACK_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmProofPackErrorDetail,
    not_found_description="lotus-manage could not find the requested proof pack or source.",
    conflict_description="lotus-manage rejected the proof-pack request as conflicting.",
    invalid_payload_description="lotus-manage rejected the proof-pack payload as invalid.",
    unavailable_description="lotus-manage proof-pack authority is unavailable or degraded.",
)
