"""Factory functions for Gateway DPM route services and upstream clients."""

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.config import settings
from app.services.dpm_command_center_service import DpmCommandCenterService
from app.services.dpm_construction_service import DpmConstructionService
from app.services.dpm_proof_pack_service import DpmProofPackService
from app.services.dpm_wave_service import DpmWaveService


def manage_client_signature() -> tuple[object, ...]:
    return (
        settings.management_service_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def lotus_ai_client_signature() -> tuple[object, ...]:
    return (
        settings.ai_service_base_url,
        settings.ai_service_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
        settings.lotus_ai_caller_credential,
    )


def dpm_service_signature() -> tuple[object, ...]:
    return (
        *manage_client_signature(),
        *lotus_ai_client_signature(),
    )


def build_manage_client() -> DpmClient:
    return DpmClient(
        base_url=settings.management_service_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def build_lotus_ai_client() -> LotusAiClient:
    return LotusAiClient(
        base_url=settings.ai_service_base_url,
        timeout_seconds=settings.ai_service_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        caller_credential=settings.lotus_ai_caller_credential,
    )


def build_dpm_command_center_service() -> DpmCommandCenterService:
    return DpmCommandCenterService(
        dpm_client=build_manage_client(),
        lotus_ai_client=build_lotus_ai_client(),
    )


def build_dpm_construction_service() -> DpmConstructionService:
    return DpmConstructionService(dpm_client=build_manage_client())


def build_dpm_proof_pack_service() -> DpmProofPackService:
    return DpmProofPackService(
        dpm_client=build_manage_client(),
        lotus_ai_client=build_lotus_ai_client(),
    )


def build_dpm_wave_service() -> DpmWaveService:
    return DpmWaveService(
        dpm_client=build_manage_client(),
        lotus_ai_client=build_lotus_ai_client(),
    )
