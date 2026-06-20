import asyncio
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
)
from app.services.upstream_envelope import raise_product_safe_gateway_unavailable_error
from app.services.workbench_core_snapshot import (
    extract_current_positions,
    parse_lotus_core_snapshot,
)
from app.services.workspace_client_protocols import WorkbenchCoreClient


@dataclass(slots=True)
class WorkbenchSnapshotContext:
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    as_of_date: str
    current_positions: list[WorkbenchPositionView]


async def load_workbench_snapshot_context(
    *,
    core_client: WorkbenchCoreClient,
    portfolio_id: str,
    correlation_id: str,
) -> WorkbenchSnapshotContext:
    fallback_as_of_date = date.today().isoformat()
    (
        portfolio_result,
        snapshot_result,
    ) = await asyncio.gather(
        core_client.get_portfolio(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        ),
        core_client.get_core_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=fallback_as_of_date,
            sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
            consumer_system="lotus-gateway",
            correlation_id=correlation_id,
        ),
    )
    portfolio_status, portfolio_payload = portfolio_result
    snapshot_status, snapshot_payload = snapshot_result
    raise_for_lotus_core_snapshot_error(portfolio_status, portfolio_payload)
    raise_for_lotus_core_snapshot_error(snapshot_status, snapshot_payload)

    portfolio, overview, as_of_date = parse_lotus_core_snapshot(
        fallback_portfolio_id=portfolio_id,
        portfolio_payload=portfolio_payload,
        snapshot_payload=snapshot_payload,
        fallback_as_of_date=fallback_as_of_date,
    )
    return WorkbenchSnapshotContext(
        portfolio=portfolio,
        overview=overview,
        as_of_date=as_of_date,
        current_positions=extract_current_positions(snapshot_payload),
    )


def raise_for_lotus_core_snapshot_error(
    upstream_status: int,
    payload: dict[str, Any],
) -> None:
    raise_product_safe_gateway_unavailable_error(
        upstream_status,
        payload,
        source_service="lotus-core",
        error_code="LOTUS_CORE_SNAPSHOT_UNAVAILABLE",
        default_detail="Lotus Core snapshot is unavailable.",
    )
