from app.services.dpm_command_center_service import DpmCommandCenterService
from app.services.dpm_construction_service import DpmConstructionService
from app.services.dpm_proof_pack_service import DpmProofPackService
from app.services.dpm_service_factory import (
    build_dpm_command_center_service,
    build_dpm_construction_service,
    build_dpm_proof_pack_service,
    build_dpm_wave_service,
    dpm_service_signature,
)
from app.services.dpm_wave_service import DpmWaveService

_DPM_COMMAND_CENTER_SERVICE: DpmCommandCenterService | None = None
_DPM_COMMAND_CENTER_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_DPM_CONSTRUCTION_SERVICE: DpmConstructionService | None = None
_DPM_CONSTRUCTION_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_DPM_PROOF_PACK_SERVICE: DpmProofPackService | None = None
_DPM_PROOF_PACK_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_DPM_WAVE_SERVICE: DpmWaveService | None = None
_DPM_WAVE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def dpm_command_center_service() -> DpmCommandCenterService:
    global _DPM_COMMAND_CENTER_SERVICE, _DPM_COMMAND_CENTER_SERVICE_SIGNATURE
    signature = dpm_service_signature()
    if _DPM_COMMAND_CENTER_SERVICE is None or _DPM_COMMAND_CENTER_SERVICE_SIGNATURE != signature:
        _DPM_COMMAND_CENTER_SERVICE = build_dpm_command_center_service()
        _DPM_COMMAND_CENTER_SERVICE_SIGNATURE = signature
    return _DPM_COMMAND_CENTER_SERVICE


def dpm_construction_service() -> DpmConstructionService:
    global _DPM_CONSTRUCTION_SERVICE, _DPM_CONSTRUCTION_SERVICE_SIGNATURE
    signature = dpm_service_signature()
    if _DPM_CONSTRUCTION_SERVICE is None or _DPM_CONSTRUCTION_SERVICE_SIGNATURE != signature:
        _DPM_CONSTRUCTION_SERVICE = build_dpm_construction_service()
        _DPM_CONSTRUCTION_SERVICE_SIGNATURE = signature
    return _DPM_CONSTRUCTION_SERVICE


def dpm_proof_pack_service() -> DpmProofPackService:
    global _DPM_PROOF_PACK_SERVICE, _DPM_PROOF_PACK_SERVICE_SIGNATURE
    signature = dpm_service_signature()
    if _DPM_PROOF_PACK_SERVICE is None or _DPM_PROOF_PACK_SERVICE_SIGNATURE != signature:
        _DPM_PROOF_PACK_SERVICE = build_dpm_proof_pack_service()
        _DPM_PROOF_PACK_SERVICE_SIGNATURE = signature
    return _DPM_PROOF_PACK_SERVICE


def dpm_wave_service() -> DpmWaveService:
    global _DPM_WAVE_SERVICE, _DPM_WAVE_SERVICE_SIGNATURE
    signature = dpm_service_signature()
    if _DPM_WAVE_SERVICE is None or _DPM_WAVE_SERVICE_SIGNATURE != signature:
        _DPM_WAVE_SERVICE = build_dpm_wave_service()
        _DPM_WAVE_SERVICE_SIGNATURE = signature
    return _DPM_WAVE_SERVICE
