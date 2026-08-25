import asyncio

from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskSummaryResponse,
)
from app.services.domain_client_protocols import RiskWorkspaceClient
from app.services.risk_mandate_client_protocols import (
    RiskMandateCashSource,
    RiskMandateManageClient,
)
from app.services.risk_mandate_concentration import compose_concentration_mandate_comparison
from app.services.risk_mandate_source_loading import load_risk_mandate_sources
from app.services.risk_mandate_sources import RiskMandateSources
from app.services.risk_mandate_summary import compose_summary_mandate_comparison
from app.services.risk_workspace_requests import (
    RiskConcentrationRequestContext,
    RiskSummaryRequestContext,
)
from app.services.risk_workspace_response_loading import (
    load_concentration_response,
    load_summary_response,
)


class RiskWorkspaceMandateServiceMixin:
    _risk_client: RiskWorkspaceClient
    _manage_client: RiskMandateManageClient | None
    _cash_source: RiskMandateCashSource | None

    async def _load_summary_with_mandate(
        self,
        context: RiskSummaryRequestContext,
    ) -> WorkbenchRiskSummaryResponse:
        risk_response, mandate_sources = await asyncio.gather(
            load_summary_response(
                risk_client=self._risk_client,
                context=context,
            ),
            self._load_mandate_sources(
                portfolio_id=context.portfolio_id,
                correlation_id=context.correlation_id,
                as_of_date=context.as_of_date,
            ),
        )
        return compose_summary_mandate_comparison(
            response=risk_response,
            sources=mandate_sources,
        )

    async def _load_concentration_with_mandate(
        self,
        context: RiskConcentrationRequestContext,
    ) -> WorkbenchRiskConcentrationResponse:
        risk_response, mandate_sources = await asyncio.gather(
            load_concentration_response(
                risk_client=self._risk_client,
                context=context,
            ),
            self._load_mandate_sources(
                portfolio_id=context.portfolio_id,
                correlation_id=context.correlation_id,
                as_of_date=context.as_of_date,
            ),
        )
        return compose_concentration_mandate_comparison(
            response=risk_response,
            sources=mandate_sources,
        )

    async def _load_mandate_sources(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> RiskMandateSources:
        if self._manage_client is None or self._cash_source is None:
            return RiskMandateSources(
                mandate=None,
                health=None,
                cash=None,
                mandate_failure_reason=(
                    "Mandate comparison sources are not configured for this runtime."
                ),
            )
        return await load_risk_mandate_sources(
            manage_client=self._manage_client,
            cash_source=self._cash_source,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
