from typing import Any

from pydantic import ValidationError

from app.contracts.portfolio_allocation import (
    PortfolioAllocationCalculationLineage,
    PortfolioAllocationContributor,
    PortfolioAllocationLookThroughCapability,
    PortfolioAllocationNumericOutputPolicy,
    PortfolioAllocationValuationCoverage,
)
from app.contracts.portfolio_allocation_response import (
    PortfolioAllocationBucket,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
)
from app.precision_policy import quantize_money, quantize_performance
from app.services.portfolio_allocation_source_contract import (
    SourceAllocationBucket,
    SourceAllocationContributor,
    SourceAllocationEvidence,
    SourceAllocationLookThrough,
    SourceAllocationPayload,
    SourceAllocationValuationCoverage,
    SourceAllocationView,
    SourceCalculationLineage,
)
from app.services.portfolio_holdings_payloads import ALLOCATION_VIEW_DIMENSIONS, optional_str
from app.services.portfolio_position_book import parse_position_book_summary


class PortfolioAllocationSourceContractError(ValueError):
    """Raised when a successful Core allocation payload is not safely consumable."""


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
    look_through_mode: str | None = "direct_only",
) -> PortfolioAllocationResponse:
    _require_source_look_through_for_non_empty_views(allocation_payload)
    source = parse_allocation_payload(allocation_payload)
    effective_as_of_date = str(
        as_of_date or aum_payload.get("resolved_as_of_date") or default_as_of_date
    )
    _validate_source_request_identity(
        source=source,
        portfolio_id=portfolio_id,
        as_of_date=effective_as_of_date,
        reporting_currency=reporting_currency,
        look_through_mode=look_through_mode,
    )
    aum_as_of_date = optional_str(aum_payload.get("resolved_as_of_date"))
    if aum_as_of_date and aum_as_of_date != source.resolved_as_of_date.isoformat():
        raise PortfolioAllocationSourceContractError("lotus-core AUM as-of date mismatch")
    return PortfolioAllocationResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        as_of_date=source.resolved_as_of_date.isoformat(),
        reporting_currency=source.reporting_currency,
        total_market_value_reporting_currency=(source.total_market_value_reporting_currency),
        valuation_coverage=_map_valuation_coverage(source.valuation_coverage),
        calculation_lineage=_map_calculation_lineage(source.calculation_lineage),
        look_through=parse_look_through_capability(allocation_payload.get("look_through")),
        summary=parse_position_book_summary(aum_payload, positions_payload),
        views=_map_allocation_views(source.views or []),
    )


def parse_allocation_payload(payload: dict[str, Any]) -> SourceAllocationPayload:
    try:
        return SourceAllocationPayload.model_validate(payload)
    except ValidationError as exc:
        raise PortfolioAllocationSourceContractError(
            "lotus-core allocation payload contract invalid"
        ) from exc


def _validate_source_request_identity(
    *,
    source: SourceAllocationPayload,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str | None,
    look_through_mode: str | None,
) -> None:
    expected_currency = optional_str(reporting_currency)
    source_dimensions = [view.dimension for view in source.views or []]
    if source.scope.portfolio_id != portfolio_id:
        raise PortfolioAllocationSourceContractError("lotus-core allocation scope mismatch")
    if source.resolved_as_of_date.isoformat() != as_of_date:
        raise PortfolioAllocationSourceContractError("lotus-core allocation as-of date mismatch")
    if expected_currency and source.reporting_currency != expected_currency.upper():
        raise PortfolioAllocationSourceContractError("lotus-core allocation currency mismatch")
    if source.look_through is None or source.look_through.requested_mode != look_through_mode:
        raise PortfolioAllocationSourceContractError(
            "lotus-core allocation look-through mode mismatch"
        )
    if len(source_dimensions) != len(set(source_dimensions)) or set(source_dimensions) != set(
        ALLOCATION_VIEW_DIMENSIONS
    ):
        raise PortfolioAllocationSourceContractError("lotus-core allocation dimensions mismatch")


def parse_allocation_evidence(payload: dict[str, Any]) -> SourceAllocationEvidence:
    try:
        return SourceAllocationEvidence.model_validate(payload)
    except ValidationError as exc:
        raise PortfolioAllocationSourceContractError(
            "lotus-core allocation evidence contract invalid"
        ) from exc


def _map_valuation_coverage(
    source: SourceAllocationValuationCoverage,
) -> PortfolioAllocationValuationCoverage:
    return PortfolioAllocationValuationCoverage(**source.model_dump())


def _map_calculation_lineage(
    source: SourceCalculationLineage,
) -> PortfolioAllocationCalculationLineage:
    numeric_output_policy = None
    if source.numeric_output_policy is not None:
        numeric_output_policy = PortfolioAllocationNumericOutputPolicy(
            **source.numeric_output_policy.model_dump()
        )
    return PortfolioAllocationCalculationLineage(
        algorithm_id=source.algorithm_id,
        algorithm_version=source.algorithm_version,
        intermediate_precision=source.intermediate_precision,
        input_content_hash=source.input_content_hash,
        calculation_content_hash=source.calculation_content_hash,
        output_content_hash=source.output_content_hash,
        numeric_output_policy=numeric_output_policy,
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
    return _map_allocation_views(source_views)


def _map_allocation_views(
    source_views: list[SourceAllocationView],
) -> list[PortfolioAllocationView]:
    return [
        PortfolioAllocationView(
            dimension=view.dimension,
            total_market_value_reporting_currency=(view.total_market_value_reporting_currency),
            buckets=[_map_allocation_bucket(bucket) for bucket in view.buckets],
        )
        for view in source_views
    ]


def _map_allocation_bucket(source: SourceAllocationBucket) -> PortfolioAllocationBucket:
    return PortfolioAllocationBucket(
        bucket=source.dimension_value,
        position_count=source.position_count,
        # Pydantic coerces exact Decimal to the legacy display shape.
        market_value_base=(
            quantize_money(source.market_value_reporting_currency)  # type: ignore[arg-type]
            if source.market_value_reporting_currency is not None
            else None
        ),
        market_value_reporting_currency=source.market_value_reporting_currency,
        # Pydantic coerces exact Decimal to the legacy display shape.
        weight_pct=(
            quantize_performance(source.weight * 100)  # type: ignore[arg-type]
            if source.weight is not None
            else None
        ),
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
