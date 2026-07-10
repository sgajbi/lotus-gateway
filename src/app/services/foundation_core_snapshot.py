from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.contracts.foundation import (
    FoundationAllocationBucket,
    FoundationPortfolioIdentity,
    FoundationPortfolioSummary,
    FoundationTopPosition,
)
from app.precision_policy import quantize_money, quantize_performance
from app.services.foundation_core_market_value import extract_core_market_value

Number = int | float


@dataclass(frozen=True)
class CoreSnapshotSections:
    baseline_rows: list[Any]
    totals_payload: dict[str, Any]
    enrichment_rows: list[Any]


@dataclass(frozen=True)
class CoreSnapshotPositionViews:
    position_count: int
    allocations: list[FoundationAllocationBucket]
    top_positions: list[FoundationTopPosition]


class FoundationCoreSnapshotMapper:
    def parse_core_snapshot(
        self,
        fallback_portfolio_id: str,
        portfolio_payload: dict[str, Any],
        payload: dict[str, Any],
        fallback_as_of_date: str,
    ) -> tuple[
        FoundationPortfolioIdentity,
        FoundationPortfolioSummary,
        list[FoundationAllocationBucket],
        list[FoundationTopPosition],
        str,
    ]:
        self._validate_core_snapshot_payloads(
            payload=payload,
            portfolio_payload=portfolio_payload,
        )

        sections = self._read_core_snapshot_sections(payload)
        market_value_base, total_cash_base, cash_weight_pct = self._read_core_totals(
            sections.totals_payload
        )
        position_views = self._build_core_position_views(
            baseline_rows=sections.baseline_rows,
            enrichment_rows=sections.enrichment_rows,
            market_value_base=market_value_base,
        )
        portfolio = self._build_core_portfolio_identity(
            payload=payload,
            portfolio_payload=portfolio_payload,
            fallback_portfolio_id=fallback_portfolio_id,
        )
        summary = FoundationPortfolioSummary(
            market_value_base=market_value_base,
            total_cash_base=total_cash_base,
            cash_weight_pct=cash_weight_pct,
            position_count=position_views.position_count,
        )
        as_of_date = str(payload.get("as_of_date") or fallback_as_of_date)
        return (
            portfolio,
            summary,
            position_views.allocations,
            position_views.top_positions[:5],
            as_of_date,
        )

    def extract_market_value(self, item: dict[str, Any]) -> float | None:
        market_value = extract_core_market_value(item)
        return self._to_number(market_value) if market_value is not None else None

    def _validate_core_snapshot_payloads(
        self,
        *,
        payload: dict[str, Any],
        portfolio_payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core foundation snapshot payload structure.",
            )
        if not isinstance(portfolio_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core portfolio identity payload structure.",
            )

    def _read_core_snapshot_sections(self, payload: dict[str, Any]) -> CoreSnapshotSections:
        sections_payload = payload.get("sections", {})
        if not isinstance(sections_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core foundation snapshot payload structure.",
            )

        baseline_rows = sections_payload.get("positions_baseline", [])
        totals_payload = sections_payload.get("portfolio_totals", {})
        enrichment_rows = sections_payload.get("instrument_enrichment", [])
        return CoreSnapshotSections(
            baseline_rows=baseline_rows if isinstance(baseline_rows, list) else [],
            totals_payload=totals_payload if isinstance(totals_payload, dict) else {},
            enrichment_rows=enrichment_rows if isinstance(enrichment_rows, list) else [],
        )

    def _read_core_totals(self, totals_payload: dict[str, Any]) -> tuple[float, float, float]:
        market_value_base = float(
            quantize_money(totals_payload.get("baseline_total_market_value_base", 0.0))
        )
        total_cash_base = float(quantize_money(totals_payload.get("baseline_total_cash_base", 0.0)))
        cash_weight_pct = 0.0
        if market_value_base > 0:
            cash_weight_pct = float(
                quantize_performance((total_cash_base / market_value_base) * 100.0)
            )
        return market_value_base, total_cash_base, cash_weight_pct

    def _build_core_position_views(
        self,
        *,
        baseline_rows: list[Any],
        enrichment_rows: list[Any],
        market_value_base: Number,
    ) -> CoreSnapshotPositionViews:
        enrichment_by_security_id = self._index_core_enrichment_rows(enrichment_rows)
        allocations_by_asset_class: dict[str, FoundationAllocationBucket] = {}
        top_positions: list[FoundationTopPosition] = []
        position_count = 0

        for row in baseline_rows:
            if not isinstance(row, dict):
                continue
            position_count += 1
            self._append_core_position_views(
                row=row,
                enrichment_by_security_id=enrichment_by_security_id,
                allocations_by_asset_class=allocations_by_asset_class,
                top_positions=top_positions,
                market_value_base=market_value_base,
            )

        allocations = self._sorted_core_allocations(
            allocations_by_asset_class=allocations_by_asset_class,
            market_value_base=market_value_base,
        )
        top_positions.sort(
            key=lambda item: (item.market_value_base is not None, item.market_value_base or 0.0),
            reverse=True,
        )
        return CoreSnapshotPositionViews(
            position_count=position_count,
            allocations=allocations,
            top_positions=top_positions,
        )

    def _index_core_enrichment_rows(self, enrichment_rows: list[Any]) -> dict[str, dict[str, Any]]:
        enrichment_by_security_id: dict[str, dict[str, Any]] = {}
        for row in enrichment_rows:
            if not isinstance(row, dict):
                continue
            security_id = self._optional_str(row.get("security_id"))
            if security_id is not None:
                enrichment_by_security_id[security_id] = row
        return enrichment_by_security_id

    def _append_core_position_views(
        self,
        *,
        row: dict[str, Any],
        enrichment_by_security_id: dict[str, dict[str, Any]],
        allocations_by_asset_class: dict[str, FoundationAllocationBucket],
        top_positions: list[FoundationTopPosition],
        market_value_base: Number,
    ) -> None:
        security_id = self._optional_str(row.get("security_id"))
        enrichment = enrichment_by_security_id.get(security_id or "", {})
        asset_class = self._resolve_core_asset_class(row=row, enrichment=enrichment)
        market_value = self.extract_market_value(row)

        bucket = self._get_or_create_allocation_bucket(
            allocations_by_asset_class=allocations_by_asset_class,
            asset_class=asset_class,
        )
        bucket.position_count += 1
        if market_value is not None:
            current_market_value = bucket.market_value_base or 0.0
            bucket.market_value_base = self._to_number(
                quantize_money(current_market_value + market_value)
            )

        top_positions.append(
            self._build_core_top_position(
                security_id=security_id,
                enrichment=enrichment,
                asset_class=asset_class,
                market_value=market_value,
                market_value_base=market_value_base,
            )
        )

    def _resolve_core_asset_class(
        self,
        *,
        row: dict[str, Any],
        enrichment: dict[str, Any],
    ) -> str:
        return str(
            enrichment.get("asset_class")
            or enrichment.get("asset_class_name")
            or row.get("asset_class")
            or "Unclassified"
        )

    def _get_or_create_allocation_bucket(
        self,
        *,
        allocations_by_asset_class: dict[str, FoundationAllocationBucket],
        asset_class: str,
    ) -> FoundationAllocationBucket:
        bucket = allocations_by_asset_class.get(asset_class)
        if bucket is None:
            bucket = FoundationAllocationBucket(
                asset_class=asset_class,
                position_count=0,
                market_value_base=0.0,
                weight_pct=None,
            )
            allocations_by_asset_class[asset_class] = bucket
        return bucket

    def _build_core_top_position(
        self,
        *,
        security_id: str | None,
        enrichment: dict[str, Any],
        asset_class: str,
        market_value: Number | None,
        market_value_base: Number,
    ) -> FoundationTopPosition:
        return FoundationTopPosition(
            security_id=security_id or "UNKNOWN_SECURITY",
            display_name=str(
                enrichment.get("instrument_name")
                or enrichment.get("security_name")
                or enrichment.get("name")
                or security_id
                or "Unknown Security"
            ),
            asset_class=self._optional_str(asset_class),
            market_value_base=self._to_number(quantize_money(market_value))
            if market_value is not None
            else None,
            weight_pct=self._to_number(
                quantize_performance((market_value / market_value_base) * 100.0)
            )
            if market_value is not None and market_value_base > 0
            else None,
        )

    def _sorted_core_allocations(
        self,
        *,
        allocations_by_asset_class: dict[str, FoundationAllocationBucket],
        market_value_base: Number,
    ) -> list[FoundationAllocationBucket]:
        allocations = sorted(allocations_by_asset_class.values(), key=lambda item: item.asset_class)
        for bucket in allocations:
            if bucket.market_value_base is not None and market_value_base > 0:
                bucket.weight_pct = float(
                    quantize_performance((bucket.market_value_base / market_value_base) * 100.0)
                )
        return allocations

    def _build_core_portfolio_identity(
        self,
        *,
        payload: dict[str, Any],
        portfolio_payload: dict[str, Any],
        fallback_portfolio_id: str,
    ) -> FoundationPortfolioIdentity:
        portfolio_id = str(payload.get("portfolio_id") or fallback_portfolio_id)
        display_name = str(
            portfolio_payload.get("portfolio_name") or portfolio_payload.get("name") or portfolio_id
        )
        return FoundationPortfolioIdentity(
            portfolio_id=portfolio_id,
            display_name=display_name,
            client_id=self._optional_str(
                portfolio_payload.get("cif_id", portfolio_payload.get("client_id"))
            ),
            base_currency=str(
                portfolio_payload.get("base_currency")
                or self._read_valuation_context_currency(payload, "portfolio_currency")
                or "USD"
            ),
            booking_center_code=self._optional_str(
                portfolio_payload.get(
                    "booking_center",
                    portfolio_payload.get("booking_center_code"),
                )
            ),
        )

    def _read_valuation_context_currency(
        self,
        payload: dict[str, Any],
        currency_key: str,
    ) -> str | None:
        valuation_context = payload.get("valuation_context")
        if not isinstance(valuation_context, dict):
            return None
        return self._optional_str(valuation_context.get(currency_key))

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _to_number(self, raw: Any) -> float:
        converted = float(raw)
        return converted
