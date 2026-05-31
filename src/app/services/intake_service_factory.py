from app.config import settings
from app.services.intake_service import IntakeService
from app.services.lotus_core_client_factory import (
    build_lotus_core_ingestion_client,
    build_lotus_core_query_client,
)


def intake_service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_ingestion_base_url,
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_intake_service() -> IntakeService:
    return IntakeService(
        lotus_core_ingestion_client=build_lotus_core_ingestion_client(),
        lotus_core_query_client=build_lotus_core_query_client(),
    )
