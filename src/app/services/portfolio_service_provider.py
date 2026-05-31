from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.portfolio_service import PortfolioService
from app.services.portfolio_service_factory import (
    build_portfolio_performance_workspace_service,
    build_portfolio_service,
    portfolio_service_signature,
)

_PORTFOLIO_SERVICE: PortfolioService | None = None
_PORTFOLIO_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_PERFORMANCE_WORKSPACE_SERVICE: PerformanceWorkspaceService | None = None
_PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def portfolio_service() -> PortfolioService:
    global _PORTFOLIO_SERVICE, _PORTFOLIO_SERVICE_SIGNATURE
    signature = portfolio_service_signature()
    if _PORTFOLIO_SERVICE is None or _PORTFOLIO_SERVICE_SIGNATURE != signature:
        _PORTFOLIO_SERVICE = build_portfolio_service()
        _PORTFOLIO_SERVICE_SIGNATURE = signature
    return _PORTFOLIO_SERVICE


def portfolio_performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    signature = portfolio_service_signature()
    if (
        _PERFORMANCE_WORKSPACE_SERVICE is None
        or _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE != signature
    ):
        _PERFORMANCE_WORKSPACE_SERVICE = build_portfolio_performance_workspace_service()
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return _PERFORMANCE_WORKSPACE_SERVICE
