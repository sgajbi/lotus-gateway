from typing import Any

from app.contracts.portfolio import (
    PortfolioReportingReadiness,
    PortfolioWorkspaceResponse,
)
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioPositionBookResponse,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.contracts.portfolio_workflow import PortfolioReadinessResponse
from app.services.portfolio_source_readiness import (
    build_source_readiness_indicators,
    parse_portfolio_supportability,
    parse_readiness_bucket,
    parse_readiness_reasons,
)
from app.services.portfolio_upstream_payloads import optional_payload
from app.services.portfolio_workflow import build_readiness_indicators


def build_portfolio_readiness_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    workspace: PortfolioWorkspaceResponse,
    positions: PortfolioPositionBookResponse,
    allocations: PortfolioAllocationResponse,
    transactions: PortfolioTransactionLedgerResponse,
    source_payload: dict[str, Any] | None,
) -> PortfolioReadinessResponse:
    indicators = build_source_readiness_indicators(
        payload=source_payload,
        detailed_view=False,
    ) or build_readiness_indicators(
        workspace=workspace,
        positions=positions.positions,
        allocation_views=allocations.views,
        transaction_total=transactions.total,
        detailed_view=False,
    )
    return PortfolioReadinessResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        as_of_date=workspace.as_of_date,
        holdings=parse_readiness_bucket((source_payload or {}).get("holdings")),
        pricing=parse_readiness_bucket((source_payload or {}).get("pricing")),
        transactions=parse_readiness_bucket((source_payload or {}).get("transactions")),
        reporting=parse_readiness_bucket((source_payload or {}).get("reporting")),
        blocking_reasons=parse_readiness_reasons((source_payload or {}).get("blocking_reasons")),
        supportability=parse_portfolio_supportability((source_payload or {}).get("supportability")),
        indicators=indicators,
    )


def build_reporting_readiness(
    *,
    summary_position_count: int,
    readiness_result: tuple[int, dict[str, Any]] | None = None,
) -> PortfolioReportingReadiness:
    if readiness_result is not None:
        payload = optional_payload(
            readiness_result,
            "lotus-core",
            "PORTFOLIO_SOURCE_READINESS_UNAVAILABLE",
            [],
            [],
        )
        if payload is not None:
            reporting_bucket = payload.get("reporting")
            if isinstance(reporting_bucket, dict):
                return PortfolioReportingReadiness(
                    status=str(reporting_bucket.get("status", "UNKNOWN")).strip().upper(),
                    row_count=summary_position_count,
                )
    return PortfolioReportingReadiness(
        status="READY" if summary_position_count > 0 else "EMPTY",
        row_count=summary_position_count,
    )
