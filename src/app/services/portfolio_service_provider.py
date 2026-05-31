from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.portfolio_service import PortfolioService
from app.services.portfolio_service_factory import (
    build_portfolio_performance_workspace_service,
    build_portfolio_service,
    portfolio_service_signature,
)
from app.services.service_provider_cache import resolve_cached_service

_PORTFOLIO_SERVICE: PortfolioService | None = None
_PORTFOLIO_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_PERFORMANCE_WORKSPACE_SERVICE: PerformanceWorkspaceService | None = None
_PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def portfolio_service() -> PortfolioService:
    global _PORTFOLIO_SERVICE, _PORTFOLIO_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _PORTFOLIO_SERVICE,
        _PORTFOLIO_SERVICE_SIGNATURE,
        portfolio_service_signature(),
        build_portfolio_service,
    )
    _PORTFOLIO_SERVICE = service
    _PORTFOLIO_SERVICE_SIGNATURE = signature
    return service


def portfolio_performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _PERFORMANCE_WORKSPACE_SERVICE,
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE,
        portfolio_service_signature(),
        build_portfolio_performance_workspace_service,
    )
    _PERFORMANCE_WORKSPACE_SERVICE = service
    _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return service
