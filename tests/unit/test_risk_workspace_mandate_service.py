from typing import Any

import pytest

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
)
from app.services.risk_workspace_service import RiskWorkspaceService


class _RiskClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def post_risk_calculate(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append({"payload": payload, "correlation_id": correlation_id})
        return 200, {
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-05-03",
                    "metrics": {
                        "VOLATILITY": {"value": 0.12},
                        "SHARPE": {"value": 1.4},
                        "SORTINO": {"value": 1.7},
                        "BETA": {"value": 0.92},
                        "TRACKING_ERROR": {"value": 0.04},
                        "INFORMATION_RATIO": {"value": 0.3},
                        "VAR": {"value": -0.02},
                    },
                }
            }
        }


class _ManageClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {"method": "mandate", "correlation_id": correlation_id, "as_of_date": as_of_date}
        )
        return 200, {
            "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
            "portfolio_id": portfolio_id,
            "mandate_version": "3",
            "as_of_date": "2026-05-03",
            "risk_profile": "BALANCED",
            "constraints": {
                "cash_band_min_weight": 0.02,
                "cash_band_max_weight": 0.10,
                "turnover_budget": 0.15,
                "max_tracking_error": 0.05,
            },
            "review_policy": {
                "review_frequency": "QUARTERLY",
                "next_review_due_date": "2026-06-30",
            },
        }

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {"method": "health", "correlation_id": correlation_id, "as_of_date": as_of_date}
        )
        return 200, {
            "health_snapshot_id": "mh_1",
            "mandate_id": mandate_id,
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "as_of_date": "2026-05-03",
            "health_state": "READY",
            "dimension_scores": [
                {
                    "dimension": "CASH_LIQUIDITY",
                    "state": "READY",
                    "reason_code": "CASH_LIQUIDITY_READY",
                }
            ],
        }


class _CashSource:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,
        include_rebalance_snapshot: bool = True,
        requested_as_of_date: str | None = None,
    ) -> WorkbenchOverviewResponse:
        self.calls.append({"correlation_id": correlation_id, "as_of_date": requested_as_of_date})
        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            as_of_date="2026-05-03",
            requested_as_of_date=requested_as_of_date,
            effective_as_of_date="2026-05-03",
            as_of_state="confirmed",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id=portfolio_id,
                base_currency="SGD",
            ),
            overview=WorkbenchOverviewSummary(
                market_value_base=1_000_000,
                cash_weight_pct=8.59,
                position_count=12,
            ),
        )


@pytest.mark.asyncio
async def test_summary_composes_and_caches_risk_manage_and_cash_sources_together() -> None:
    risk = _RiskClient()
    manage = _ManageClient()
    cash = _CashSource()
    service = RiskWorkspaceService(
        risk,
        manage_client=manage,
        cash_source=cash,
        cache_ttl_seconds=60,
    )

    first = await service.get_summary(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-first",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-05-03",
        reporting_currency="SGD",
    )
    second = await service.get_summary(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-second",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-05-03",
        reporting_currency="SGD",
    )

    assert len(risk.calls) == 1
    assert [call["method"] for call in manage.calls] == ["mandate", "health"]
    assert len(cash.calls) == 1
    assert first.mandate_comparison is not None
    assert first.mandate_comparison.supportability.state == "ready"
    assert first.mandate_comparison.constraints[0].headroom == 0.0141
    assert first.mandate_comparison.constraints[1].state == "within"
    assert second.correlation_id == "corr-second"
    assert second.metadata.cache_status == "hit"


@pytest.mark.asyncio
async def test_summary_without_configured_sources_is_explicitly_unavailable() -> None:
    service = RiskWorkspaceService(_RiskClient(), cache_ttl_seconds=60)

    response = await service.get_summary(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-unconfigured",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-05-03",
        reporting_currency="SGD",
    )

    assert response.payload is not None
    assert response.mandate_comparison is not None
    assert response.mandate_comparison.supportability.state == "unavailable"
    assert response.mandate_comparison.supportability.reason == (
        "Mandate comparison sources are not configured for this runtime."
    )
