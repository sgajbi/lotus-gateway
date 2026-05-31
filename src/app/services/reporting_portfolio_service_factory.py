from app.config import settings
from app.services.reporting_client_factory import build_reporting_client
from app.services.reporting_portfolio_service import ReportingPortfolioService


def build_reporting_portfolio_service() -> ReportingPortfolioService:
    return ReportingPortfolioService(
        reporting_client=build_reporting_client(),
        contract_version=settings.contract_version,
    )
