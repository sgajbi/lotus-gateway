from app.services.analytics_client_factory import (
    build_performance_analytics_client,
    performance_analytics_client_signature,
)
from app.services.dpm_service_factory import build_manage_client, manage_client_signature
from app.services.foundation_service import FoundationService
from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)
from app.services.reporting_client_factory import build_reporting_client, reporting_client_signature


def foundation_service_signature() -> tuple[object, ...]:
    return (
        *lotus_core_query_client_signature(),
        *performance_analytics_client_signature(),
        *manage_client_signature(),
        *reporting_client_signature(),
    )


def build_foundation_service() -> FoundationService:
    return FoundationService(
        lotus_core_query_client=build_lotus_core_query_client(),
        analytics_client=build_performance_analytics_client(),
        dpm_client=build_manage_client(),
        reporting_client=build_reporting_client(),
    )
