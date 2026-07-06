import pytest
from fastapi import HTTPException

from app.services.workbench_snapshot_context import load_workbench_snapshot_context


class _StubWorkbenchCoreClient:
    def __init__(self) -> None:
        self.portfolio_status = 200
        self.portfolio_payload = {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "client_id": "CLIENT_001",
            "base_currency": "SGD",
            "booking_center_code": "SG",
        }
        self.snapshot_status = 200
        self.snapshot_payload = {
            "as_of_date": "2026-02-24",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": "10",
                        "market_value_base": "1200",
                        "weight": "0.60",
                    },
                    {
                        "security_id": "CASH_SGD",
                        "quantity": "1",
                        "market_value_base": "800",
                        "weight": "0.40",
                    },
                ],
                "portfolio_totals": {"baseline_total_market_value_base": "2000"},
                "instrument_enrichment": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Global Equity Fund",
                        "asset_class": "Equity",
                    },
                    {
                        "security_id": "CASH_SGD",
                        "instrument_name": "Singapore Dollar Cash",
                        "asset_class": "Cash",
                    },
                ],
            },
        }
        self.portfolio_calls: list[dict[str, str]] = []
        self.snapshot_calls: list[dict[str, object]] = []

    async def get_portfolio(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ):
        self.portfolio_calls.append(
            {
                "portfolio_id": portfolio_id,
                "correlation_id": correlation_id,
            }
        )
        return self.portfolio_status, self.portfolio_payload

    async def get_core_snapshot(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        self.snapshot_calls.append(
            {
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date,
                "sections": sections,
                "consumer_system": consumer_system,
                "correlation_id": correlation_id,
            }
        )
        return self.snapshot_status, self.snapshot_payload


@pytest.mark.asyncio
async def test_load_workbench_snapshot_context_preserves_core_snapshot_shape() -> None:
    client = _StubWorkbenchCoreClient()

    context = await load_workbench_snapshot_context(
        core_client=client,
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-workbench-context",
    )

    assert client.portfolio_calls == [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "correlation_id": "corr-workbench-context",
        }
    ]
    assert client.snapshot_calls == [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "as_of_date": client.snapshot_calls[0]["as_of_date"],
            "sections": ["positions_baseline", "portfolio_totals", "instrument_enrichment"],
            "consumer_system": "lotus-gateway",
            "correlation_id": "corr-workbench-context",
        }
    ]
    assert context.as_of_date == "2026-02-24"
    assert context.portfolio.portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert context.portfolio.base_currency == "SGD"
    assert context.overview.market_value_base == 2000.0
    assert context.overview.position_count == 2
    assert [position.security_id for position in context.current_positions] == [
        "CASH_SGD",
        "EQ_1",
    ]


@pytest.mark.asyncio
async def test_load_workbench_snapshot_context_maps_core_error_safely() -> None:
    client = _StubWorkbenchCoreClient()
    client.snapshot_status = 503
    client.snapshot_payload = {
        "detail": "database connection failed at internal-host:5432",
    }

    with pytest.raises(HTTPException) as exc_info:
        await load_workbench_snapshot_context(
            core_client=client,
            portfolio_id="PB_SG_GLOBAL_BAL_001",
            correlation_id="corr-workbench-context",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": 503,
        "error_code": "LOTUS_CORE_SNAPSHOT_UNAVAILABLE",
        "detail": "Lotus Core snapshot is unavailable.",
    }
