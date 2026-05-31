from app.config import settings
from app.services.lotus_core_client_factory import build_lotus_core_query_client
from app.services.source_product_execution_service import SourceProductExecutionService


def source_product_execution_service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_source_product_execution_service() -> SourceProductExecutionService:
    return SourceProductExecutionService(
        lotus_core_query_client=build_lotus_core_query_client(),
    )
