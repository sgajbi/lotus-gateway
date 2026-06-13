from types import SimpleNamespace
from typing import cast

from app.contracts.portfolio import PortfolioWorkspaceResponse
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioPositionBookResponse,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.services.portfolio_readiness_response import (
    build_portfolio_readiness_response,
    build_reporting_readiness,
)


def test_build_reporting_readiness_prefers_source_payload_status() -> None:
    reporting = build_reporting_readiness(
        summary_position_count=3,
        readiness_result=(200, {"reporting": {"status": "pending"}}),
    )

    assert reporting.status == "PENDING"
    assert reporting.row_count == 3


def test_build_reporting_readiness_falls_back_to_book_coverage() -> None:
    assert build_reporting_readiness(summary_position_count=1).status == "READY"
    assert build_reporting_readiness(summary_position_count=0).status == "EMPTY"


def test_build_portfolio_readiness_response_prefers_source_indicators() -> None:
    response = build_portfolio_readiness_response(
        correlation_id="corr-readiness",
        contract_version="v1",
        portfolio_id="PF_1001",
        workspace=cast(
            PortfolioWorkspaceResponse,
            SimpleNamespace(as_of_date="2026-03-27"),
        ),
        positions=cast(PortfolioPositionBookResponse, SimpleNamespace(positions=[])),
        allocations=cast(PortfolioAllocationResponse, SimpleNamespace(views=[])),
        transactions=cast(PortfolioTransactionLedgerResponse, SimpleNamespace(total=0)),
        source_payload={
            "holdings": {"status": "READY"},
            "pricing": {
                "status": "FAILED",
                "reasons": [{"code": "NO_PRICE", "detail": "latest price unavailable"}],
            },
            "transactions": {"status": "READY"},
            "reporting": {"status": "PENDING"},
            "blocking_reasons": [
                {"code": "awaiting_pricing", "detail": "Pricing is not published."}
            ],
            "supportability": {
                "state": "degraded",
                "reason": "portfolio_supportability_pending",
                "freshness_bucket": "fresh",
                "ready_domains": 3,
                "pending_domains": 1,
                "blocked_domains": 0,
                "no_activity_domains": 0,
            },
        },
    )

    assert response.as_of_date == "2026-03-27"
    assert [indicator.status for indicator in response.indicators] == [
        "Ready",
        "Blocked",
        "Ready",
        "Pending",
    ]
    assert response.pricing is not None
    assert response.pricing.reasons[0].code == "NO_PRICE"
    assert response.blocking_reasons[0].code == "awaiting_pricing"
    assert response.supportability is not None
    assert response.supportability.pending_domains == 1


def test_build_portfolio_readiness_response_falls_back_to_loaded_views() -> None:
    workspace = SimpleNamespace(
        as_of_date="2026-03-27",
        summary=SimpleNamespace(position_count=1),
        operations=None,
        reporting=SimpleNamespace(status="READY", row_count=1),
    )
    position = SimpleNamespace(market_value_base=1000.0)

    response = build_portfolio_readiness_response(
        correlation_id="corr-readiness",
        contract_version="v1",
        portfolio_id="PF_1001",
        workspace=cast(PortfolioWorkspaceResponse, workspace),
        positions=cast(PortfolioPositionBookResponse, SimpleNamespace(positions=[position])),
        allocations=cast(PortfolioAllocationResponse, SimpleNamespace(views=[object()])),
        transactions=cast(PortfolioTransactionLedgerResponse, SimpleNamespace(total=2)),
        source_payload=None,
    )

    assert response.holdings is None
    assert response.supportability is None
    assert [indicator.status for indicator in response.indicators] == [
        "Ready",
        "Ready",
        "Ready",
        "Ready",
    ]
