from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings


def build_lotus_core_ingestion_client() -> LotusCoreIngestionClient:
    return LotusCoreIngestionClient(
        base_url=settings.portfolio_data_ingestion_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def build_lotus_core_query_client() -> LotusCoreQueryClient:
    return LotusCoreQueryClient(
        base_url=settings.portfolio_data_query_base_url,
        control_plane_base_url=settings.portfolio_data_control_plane_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
