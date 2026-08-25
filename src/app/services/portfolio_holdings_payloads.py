import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.contracts.portfolio_holdings import (
    PortfolioAllocationBucket,
    PortfolioAllocationContributor,
    PortfolioAllocationLookThroughCapability,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioCashBalance,
)
from app.precision_policy import quantize_money, quantize_performance
from app.services.portfolio_allocation_source_contract import (
    SourceAllocationBucket,
    SourceAllocationContributor,
    SourceAllocationLookThrough,
    SourceAllocationView,
)
from app.services.portfolio_position_book import parse_position_book_summary

UpstreamResult = tuple[int, dict[str, Any]]
ALLOCATION_VIEW_DIMENSIONS = ["asset_class", "currency", "sector", "region"]
DEFAULT_CONTRIBUTOR_LIMIT_PER_BUCKET = 50


class PortfolioAllocationSourceContractError(ValueError):
    """Raised when a successful Core allocation payload is not safely consumable."""


@dataclass(frozen=True)
class PortfolioAllocationLoadRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    reporting_currency: str | None
    look_through_mode: str | None
    contributor_limit_per_bucket: int = DEFAULT_CONTRIBUTOR_LIMIT_PER_BUCKET


@dataclass(frozen=True)
class PortfolioAllocationPayloads:
    aum_result: UpstreamResult
    aum_payload: dict[str, Any]
    positions_payload: dict[str, Any]
    allocation_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioPositionBookLoadRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    include_projected: bool
    reporting_currency: str | None


@dataclass(frozen=True)
class PortfolioPositionBookPayloads:
    aum_payload: dict[str, Any]
    positions_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioAllocationPayloadLoaders:
    query_aum_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_positions_result: Callable[..., Awaitable[UpstreamResult]]
    query_asset_allocation_result: Callable[..., Awaitable[UpstreamResult]]
    require_payload: Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class PortfolioPositionBookPayloadLoaders:
    query_aum_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_positions_result: Callable[..., Awaitable[UpstreamResult]]
    require_payload: Callable[..., dict[str, Any]]


async def load_portfolio_allocation_payloads(
    request: PortfolioAllocationLoadRequest,
    loaders: PortfolioAllocationPayloadLoaders,
) -> PortfolioAllocationPayloads:
    aum_result, positions_result, allocation_result = await asyncio.gather(
        loaders.query_aum_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_positions_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=False,
            reporting_currency=request.reporting_currency,
        ),
        loaders.query_asset_allocation_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            dimensions=ALLOCATION_VIEW_DIMENSIONS,
            reporting_currency=request.reporting_currency,
            look_through_mode=request.look_through_mode,
            contributor_limit_per_bucket=request.contributor_limit_per_bucket,
        ),
    )
    return PortfolioAllocationPayloads(
        aum_result=aum_result,
        aum_payload=loaders.require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        ),
        allocation_payload=loaders.require_payload(
            result=allocation_result,
            unavailable_detail_prefix="lotus-core allocation unavailable",
        ),
        positions_payload=loaders.require_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        ),
    )


async def load_portfolio_position_book_payloads(
    request: PortfolioPositionBookLoadRequest,
    loaders: PortfolioPositionBookPayloadLoaders,
) -> PortfolioPositionBookPayloads:
    aum_result, positions_result = await asyncio.gather(
        loaders.query_aum_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_positions_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=request.include_projected,
            reporting_currency=request.reporting_currency,
        ),
    )
    return PortfolioPositionBookPayloads(
        aum_payload=loaders.require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        ),
        positions_payload=loaders.require_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        ),
    )


def build_portfolio_allocation_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    as_of_date: str | None,
    default_as_of_date: str,
    reporting_currency: str | None,
    aum_payload: dict[str, Any],
    positions_payload: dict[str, Any],
    allocation_payload: dict[str, Any],
) -> PortfolioAllocationResponse:
    _require_source_look_through_for_non_empty_views(allocation_payload)
    return PortfolioAllocationResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        as_of_date=str(aum_payload.get("resolved_as_of_date") or as_of_date or default_as_of_date),
        reporting_currency=optional_str(allocation_payload.get("reporting_currency"))
        or reporting_currency,
        look_through=parse_look_through_capability(allocation_payload.get("look_through")),
        summary=parse_position_book_summary(aum_payload, positions_payload),
        views=parse_allocation_views(allocation_payload),
    )


def _require_source_look_through_for_non_empty_views(payload: dict[str, Any]) -> None:
    views = payload.get("views")
    if isinstance(views, list) and views and not isinstance(payload.get("look_through"), dict):
        raise PortfolioAllocationSourceContractError(
            "lotus-core allocation look-through metadata missing"
        )


def parse_look_through_capability(
    payload: Any,
) -> PortfolioAllocationLookThroughCapability | None:
    if not isinstance(payload, dict):
        return None
    try:
        source = SourceAllocationLookThrough.model_validate(payload)
    except ValidationError as exc:
        raise PortfolioAllocationSourceContractError(
            "lotus-core allocation look-through contract invalid"
        ) from exc
    return PortfolioAllocationLookThroughCapability(
        requested_mode=source.requested_mode,
        effective_mode=source.applied_mode,
        applied=source.applied_mode == "prefer_look_through",
        supported=source.supported,
        decomposed_position_count=source.decomposed_position_count,
        limitation_reason=source.limitation_reason,
    )


def parse_allocation_views(payload: dict[str, Any]) -> list[PortfolioAllocationView]:
    raw_views = payload.get("views", [])
    if raw_views is None:
        return []
    if not isinstance(raw_views, list):
        raise PortfolioAllocationSourceContractError("lotus-core allocation views contract invalid")
    if not raw_views:
        return []
    try:
        source_views = [SourceAllocationView.model_validate(view) for view in raw_views]
    except ValidationError as exc:
        raise PortfolioAllocationSourceContractError(
            "lotus-core allocation contributor contract invalid"
        ) from exc
    return [
        PortfolioAllocationView(
            dimension=view.dimension,
            buckets=[_map_allocation_bucket(bucket) for bucket in view.buckets],
        )
        for view in source_views
    ]


def _map_allocation_bucket(source: SourceAllocationBucket) -> PortfolioAllocationBucket:
    return PortfolioAllocationBucket(
        bucket=source.dimension_value,
        position_count=source.position_count,
        # Pydantic coerces exact Decimal to the legacy display shape.
        market_value_base=quantize_money(source.market_value_reporting_currency),  # type: ignore[arg-type]
        market_value_reporting_currency=source.market_value_reporting_currency,
        # Pydantic coerces exact Decimal to the legacy display shape.
        weight_pct=quantize_performance(source.weight * 100),  # type: ignore[arg-type]
        contributor_count=source.contributor_count,
        contributors=[_map_allocation_contributor(item) for item in source.contributors],
        contributors_truncated=source.contributors_truncated,
        omitted_market_value_reporting_currency=source.omitted_market_value_reporting_currency,
    )


def _map_allocation_contributor(
    source: SourceAllocationContributor,
) -> PortfolioAllocationContributor:
    return PortfolioAllocationContributor(
        contributor_type=source.contributor_type,
        portfolio_id=source.portfolio_id,
        security_id=source.security_id,
        booked_security_id=source.booked_security_id,
        source_snapshot_id=source.source_snapshot_id,
        component_record_id=source.component_record_id,
        component_weight=source.component_weight,
        component_effective_from=source.component_effective_from,
        component_effective_to=source.component_effective_to,
        component_source_system=source.component_source_system,
        component_source_record_id=source.component_source_record_id,
        market_value_reporting_currency=source.market_value_reporting_currency,
        bucket_weight=source.bucket_weight,
    )


def parse_cash_balances(payload: dict[str, Any], total_aum: float) -> list[PortfolioCashBalance]:
    balances: list[PortfolioCashBalance] = []
    for item in payload.get("cash_accounts", []):
        balance = float(quantize_money(item.get("balance_reporting_currency", 0)))
        weight = float(quantize_performance((balance / total_aum) * 100)) if total_aum > 0 else 0.0
        balances.append(
            PortfolioCashBalance(
                security_id=str(item.get("security_id", "")),
                instrument_name=str(item.get("instrument_name", "")),
                currency=optional_str(item.get("account_currency")),
                quantity=float(quantize_money(item.get("balance_account_currency", 0))),
                market_value_base=balance,
                weight_pct=weight,
            )
        )
    return balances


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
