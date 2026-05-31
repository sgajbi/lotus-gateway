from app.services.intake_service import IntakeService
from app.services.lotus_core_client_factory import (
    build_lotus_core_ingestion_client,
    build_lotus_core_query_client,
)


def build_intake_service() -> IntakeService:
    return IntakeService(
        lotus_core_ingestion_client=build_lotus_core_ingestion_client(),
        lotus_core_query_client=build_lotus_core_query_client(),
    )
