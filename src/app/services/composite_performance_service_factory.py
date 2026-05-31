from app.services.analytics_client_factory import build_performance_analytics_client
from app.services.composite_performance_service import CompositePerformanceService


def build_composite_performance_service() -> CompositePerformanceService:
    return CompositePerformanceService(analytics_client=build_performance_analytics_client())
