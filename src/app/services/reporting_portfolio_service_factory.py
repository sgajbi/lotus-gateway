from app.config import settings
from app.services.reporting_client_factory import build_reporting_client
from app.services.reporting_portfolio_service import ReportingPortfolioService


def reporting_portfolio_service_signature() -> tuple[object, ...]:
    return (
        settings.reporting_aggregation_base_url,
        settings.contract_version,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_reporting_portfolio_service() -> ReportingPortfolioService:
    return ReportingPortfolioService(
        reporting_client=build_reporting_client(),
        contract_version=settings.contract_version,
    )
