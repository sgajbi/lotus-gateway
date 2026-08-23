import asyncio
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
)
from app.contracts.workbench_temporal import WorkbenchAsOfState
from app.services.upstream_envelope import raise_product_safe_gateway_unavailable_error
from app.services.workbench_core_snapshot import (
    extract_current_positions,
    parse_lotus_core_snapshot,
    resolve_snapshot_date_evidence,
)
from app.services.workspace_client_protocols import WorkbenchCoreClient


@dataclass(slots=True)
class WorkbenchSnapshotContext:
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    requested_as_of_date: str | None
    effective_as_of_date: str | None
    as_of_state: WorkbenchAsOfState
    enrichment_as_of_date: str | None
    current_positions: list[WorkbenchPositionView]


async def load_workbench_snapshot_context(
    *,
    core_client: WorkbenchCoreClient,
    portfolio_id: str,
    correlation_id: str,
    requested_as_of_date: str | None = None,
) -> WorkbenchSnapshotContext:
    resolved_as_of_date, portfolio_result, snapshot_result = await _load_workbench_sources(
        core_client=core_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        requested_as_of_date=requested_as_of_date,
    )
    portfolio_status, portfolio_payload = portfolio_result
    snapshot_status, snapshot_payload = snapshot_result
    raise_for_lotus_core_snapshot_error(portfolio_status, portfolio_payload)
    raise_for_lotus_core_snapshot_error(snapshot_status, snapshot_payload)

    portfolio, overview = parse_lotus_core_snapshot(
        fallback_portfolio_id=portfolio_id,
        portfolio_payload=portfolio_payload,
        snapshot_payload=snapshot_payload,
    )
    date_evidence = resolve_snapshot_date_evidence(
        snapshot_payload,
        requested_as_of_date=requested_as_of_date,
        confirmation_as_of_date=resolved_as_of_date,
    )
    enrichment_as_of_date = date_evidence.effective_as_of_date
    return WorkbenchSnapshotContext(
        portfolio=portfolio,
        overview=overview,
        requested_as_of_date=requested_as_of_date,
        effective_as_of_date=date_evidence.effective_as_of_date,
        as_of_state=date_evidence.as_of_state,
        enrichment_as_of_date=enrichment_as_of_date,
        current_positions=extract_current_positions(snapshot_payload),
    )


async def _load_workbench_sources(
    *,
    core_client: WorkbenchCoreClient,
    portfolio_id: str,
    correlation_id: str,
    requested_as_of_date: str | None,
) -> tuple[str | None, tuple[int, dict[str, Any]], tuple[int, dict[str, Any]]]:
    resolved_as_of_date = requested_as_of_date
    if requested_as_of_date is None:
        resolved_as_of_date = await _resolve_latest_business_date(
            core_client=core_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
    query_as_of_date = resolved_as_of_date or date.today().isoformat()
    portfolio_result, snapshot_result = await asyncio.gather(
        core_client.get_portfolio(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        ),
        core_client.get_core_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=query_as_of_date,
            sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
            consumer_system="lotus-gateway",
            correlation_id=correlation_id,
        ),
    )
    return resolved_as_of_date, portfolio_result, snapshot_result


async def _resolve_latest_business_date(
    *,
    core_client: WorkbenchCoreClient,
    portfolio_id: str,
    correlation_id: str,
) -> str | None:
    try:
        status_code, payload = await core_client.get_support_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
    except Exception:
        return None
    if status_code >= 400 or not isinstance(payload, dict):
        return None
    raw_business_date = payload.get("business_date")
    if not isinstance(raw_business_date, str):
        return None
    try:
        return date.fromisoformat(raw_business_date).isoformat()
    except ValueError:
        return None


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
