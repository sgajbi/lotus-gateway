from app.services.intake_service import IntakeService
from app.services.lotus_core_client_factory import (
    build_lotus_core_ingestion_client,
    build_lotus_core_query_client,
    lotus_core_ingestion_client_signature,
    lotus_core_query_client_signature,
)


def intake_service_signature() -> tuple[object, ...]:
    return (
        *lotus_core_ingestion_client_signature(),
        *lotus_core_query_client_signature(),
    )


def build_intake_service() -> IntakeService:
    return IntakeService(
        lotus_core_ingestion_client=build_lotus_core_ingestion_client(),
        lotus_core_query_client=build_lotus_core_query_client(),
    )
