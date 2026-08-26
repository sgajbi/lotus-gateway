import asyncio
from typing import Protocol, cast

from app.config import settings
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.contracts.portfolio_workflow import PortfolioWorkflowResponse
from app.contracts.portfolio_workspace import PortfolioWorkspaceResponse
from app.services.portfolio_workflow import build_workflow_actions


class _PortfolioWorkflowDependencies(Protocol):
    async def get_portfolio_workspace(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioWorkspaceResponse: ...

    async def get_transaction_ledger(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        skip: int,
        limit: int,
    ) -> PortfolioTransactionLedgerResponse: ...


def _workflow_dependencies(service: object) -> _PortfolioWorkflowDependencies:
    return cast(_PortfolioWorkflowDependencies, service)


class PortfolioWorkflowServiceMixin:
    async def get_portfolio_workflow(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioWorkflowResponse:
        dependencies = _workflow_dependencies(self)
        workspace, transactions = await asyncio.gather(
            dependencies.get_portfolio_workspace(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._get_latest_transaction_probe(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
        )
        actions = build_workflow_actions(
            portfolio_id=portfolio_id,
            summary=workspace.summary,
            workflow_cues=workspace.workflow_cues,
            transaction_total=transactions.total,
        )
        return PortfolioWorkflowResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=workspace.as_of_date,
            actions=actions,
        )

    async def _get_latest_transaction_probe(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> PortfolioTransactionLedgerResponse:
        return await _workflow_dependencies(self).get_transaction_ledger(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=False,
            skip=0,
            limit=1,
        )
