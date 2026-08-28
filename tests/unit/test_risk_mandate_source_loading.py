from typing import Any

import pytest
from fastapi import HTTPException

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
)
from app.services.risk_mandate_source_loading import load_risk_mandate_sources


def _mandate_payload() -> dict[str, Any]:
    return {
        "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "mandate_version": "3",
        "as_of_date": "2026-05-03",
        "risk_profile": "BALANCED",
        "constraints": {
            "cash_band_min_weight": "0.02",
            "cash_band_max_weight": "0.10",
            "turnover_budget": "0.15",
        },
        "review_policy": {
            "review_frequency": "QUARTERLY",
            "next_review_due_date": "2026-06-30",
        },
        "source_lineage": [],
    }


def _health_payload() -> dict[str, Any]:
    return {
        "health_snapshot_id": "mh_1",
        "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
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


class _ManageClient:
    def __init__(self) -> None:
        self.mandate_status = 200
        self.mandate_payload = _mandate_payload()
        self.health_status = 200
        self.health_payload = _health_payload()
        self.calls: list[dict[str, Any]] = []

    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {
                "method": "mandate",
                "portfolio_id": portfolio_id,
                "correlation_id": correlation_id,
                "as_of_date": as_of_date,
            }
        )
        return self.mandate_status, self.mandate_payload

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {
                "method": "health",
                "mandate_id": mandate_id,
                "correlation_id": correlation_id,
                "as_of_date": as_of_date,
            }
        )
        return self.health_status, self.health_payload


class _CashSource:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.failure: HTTPException | None = None
        self.response = WorkbenchOverviewResponse(
            correlation_id="corr-1",
            as_of_date="2026-05-03",
            requested_as_of_date="2026-05-03",
            effective_as_of_date="2026-05-03",
            as_of_state="confirmed",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id="PB_SG_GLOBAL_BAL_001",
                base_currency="SGD",
            ),
            overview=WorkbenchOverviewSummary(
                market_value_base=1_000_000,
                cash_weight_pct=8.59,
                position_count=12,
            ),
        )

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,
        include_rebalance_snapshot: bool = True,
        requested_as_of_date: str | None = None,
    ) -> WorkbenchOverviewResponse:
        self.calls.append(
            {
                "portfolio_id": portfolio_id,
                "correlation_id": correlation_id,
                "include_performance_snapshot": include_performance_snapshot,
                "include_rebalance_snapshot": include_rebalance_snapshot,
                "requested_as_of_date": requested_as_of_date,
            }
        )
        if self.failure is not None:
            raise self.failure
        return self.response


@pytest.mark.asyncio
async def test_source_loader_forwards_review_date_and_normalizes_cash_percentage_points() -> None:
    manage = _ManageClient()
    cash = _CashSource()

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=cash,
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert [call["as_of_date"] for call in manage.calls] == ["2026-05-03", "2026-05-03"]
    assert cash.calls == [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "correlation_id": "corr-1",
            "include_performance_snapshot": False,
            "include_rebalance_snapshot": False,
            "requested_as_of_date": "2026-05-03",
        }
    ]
    assert sources.mandate is not None
    assert sources.health is not None
    assert sources.cash is not None
    assert sources.cash.value == pytest.approx(0.0859)


@pytest.mark.asyncio
async def test_source_loader_does_not_default_an_absent_review_frequency() -> None:
    manage = _ManageClient()
    del manage.mandate_payload["review_policy"]["review_frequency"]

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=_CashSource(),
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.mandate is not None
    assert sources.mandate.review_policy.review_frequency is None


@pytest.mark.asyncio
async def test_source_loader_does_not_request_health_when_mandate_is_unavailable() -> None:
    manage = _ManageClient()
    manage.mandate_status = 503

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=_CashSource(),
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert [call["method"] for call in manage.calls] == ["mandate"]
    assert sources.mandate is None
    assert sources.health is None
    assert "unavailable" in (sources.mandate_failure_reason or "").lower()


@pytest.mark.asyncio
async def test_source_loader_degrades_malformed_health_without_losing_mandate_or_cash() -> None:
    manage = _ManageClient()
    manage.health_payload = {"mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001"}

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=_CashSource(),
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.mandate is not None
    assert sources.cash is not None
    assert sources.health is None
    assert sources.health_failure_reason == (
        "Lotus Manage returned incomplete mandate-health evidence."
    )


@pytest.mark.asyncio
async def test_source_loader_rejects_cross_portfolio_health_evidence() -> None:
    manage = _ManageClient()
    manage.health_payload["portfolio_id"] = "PB_OTHER"

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=_CashSource(),
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.mandate is not None
    assert sources.health is None
    assert sources.health_failure_reason == (
        "Lotus Manage returned health evidence for a different mandate or portfolio."
    )


@pytest.mark.asyncio
async def test_source_loader_rejects_invalid_mandate_ratio_bounds() -> None:
    manage = _ManageClient()
    manage.mandate_payload["constraints"]["cash_band_max_weight"] = 1.5

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=_CashSource(),
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.mandate is None
    assert sources.health is None
    assert sources.mandate_failure_reason == "Lotus Manage returned incomplete mandate evidence."


@pytest.mark.asyncio
async def test_source_loader_preserves_absent_cash_limits_without_defaulting_a_band() -> None:
    manage = _ManageClient()
    del manage.mandate_payload["constraints"]["cash_band_min_weight"]
    del manage.mandate_payload["constraints"]["cash_band_max_weight"]

    sources = await load_risk_mandate_sources(
        manage_client=manage,
        cash_source=_CashSource(),
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.mandate is not None
    assert sources.mandate.constraints.cash_band_min_weight is None
    assert sources.mandate.constraints.cash_band_max_weight is None


@pytest.mark.asyncio
async def test_source_loader_keeps_manage_evidence_when_cash_snapshot_fails() -> None:
    cash = _CashSource()
    cash.failure = HTTPException(status_code=502, detail="Core unavailable")

    sources = await load_risk_mandate_sources(
        manage_client=_ManageClient(),
        cash_source=cash,
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.mandate is not None
    assert sources.health is not None
    assert sources.cash is None
    assert sources.cash_failure_reason == (
        "Cash allocation is unavailable for the selected review date."
    )


@pytest.mark.asyncio
async def test_source_loader_rejects_invalid_cash_business_date() -> None:
    cash = _CashSource()
    cash.response.effective_as_of_date = "not-a-date"

    sources = await load_risk_mandate_sources(
        manage_client=_ManageClient(),
        cash_source=cash,
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-1",
        as_of_date="2026-05-03",
    )

    assert sources.cash is None
    assert sources.cash_failure_reason == "Cash allocation has invalid business-date evidence."
