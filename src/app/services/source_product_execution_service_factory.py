from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)
from app.services.source_product_execution_service import SourceProductExecutionService


def source_product_execution_service_signature() -> tuple[object, ...]:
    return lotus_core_query_client_signature()


def build_source_product_execution_service() -> SourceProductExecutionService:
    return SourceProductExecutionService(
        lotus_core_query_client=build_lotus_core_query_client(),
    )
