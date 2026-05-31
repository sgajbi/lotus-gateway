from app.services.dpm_command_center_service import DpmCommandCenterService
from app.services.dpm_construction_service import DpmConstructionService
from app.services.dpm_proof_pack_service import DpmProofPackService
from app.services.dpm_service_factory import (
    build_dpm_command_center_service,
    build_dpm_construction_service,
    build_dpm_proof_pack_service,
    build_dpm_wave_service,
)
from app.services.dpm_wave_service import DpmWaveService


def dpm_command_center_service() -> DpmCommandCenterService:
    return build_dpm_command_center_service()


def dpm_construction_service() -> DpmConstructionService:
    return build_dpm_construction_service()


def dpm_proof_pack_service() -> DpmProofPackService:
    return build_dpm_proof_pack_service()


def dpm_wave_service() -> DpmWaveService:
    return build_dpm_wave_service()
