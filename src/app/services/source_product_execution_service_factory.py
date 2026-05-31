from app.services.lotus_core_client_factory import build_lotus_core_query_client
from app.services.source_product_execution_service import SourceProductExecutionService


def build_source_product_execution_service() -> SourceProductExecutionService:
    return SourceProductExecutionService(
        lotus_core_query_client=build_lotus_core_query_client(),
    )
