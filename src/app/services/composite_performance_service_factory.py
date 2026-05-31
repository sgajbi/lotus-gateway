from app.services.analytics_client_factory import (
    build_performance_analytics_client,
    performance_analytics_client_signature,
)
from app.services.composite_performance_service import CompositePerformanceService


def composite_performance_service_signature() -> tuple[object, ...]:
    return performance_analytics_client_signature()


def build_composite_performance_service() -> CompositePerformanceService:
    return CompositePerformanceService(analytics_client=build_performance_analytics_client())
