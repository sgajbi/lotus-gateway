from datetime import UTC, datetime

from app.config import settings
from app.contracts.portfolio_liquidity import PortfolioProjectedCashflowResponse
from app.services.portfolio_holdings_upstream import holdings_upstream_access
from app.services.portfolio_liquidity_response import build_projected_cashflow_response


class PortfolioProjectedCashflowServiceMixin:
    async def get_portfolio_projected_cashflow(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        horizon_days: int,
        include_projected: bool,
    ) -> PortfolioProjectedCashflowResponse:
        cashflow_result = await holdings_upstream_access(self)._get_cashflow_projection_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            horizon_days=horizon_days,
        )

        return build_projected_cashflow_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            cashflow_result=cashflow_result,
        )
