from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status


@dataclass(frozen=True)
class CoreSnapshotSections:
    baseline_rows: list[Any]
    totals_payload: dict[str, Any]
    enrichment_rows: list[Any]


def validate_core_snapshot_payloads(
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


def read_core_snapshot_sections(payload: dict[str, Any]) -> CoreSnapshotSections:
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
