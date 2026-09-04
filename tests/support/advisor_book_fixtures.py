"""Shared advisor-book test doubles: trusted callers, Core membership and bulk value stubs."""

import asyncio
from decimal import Decimal
from typing import Any

from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext


class MembershipClient:
    def __init__(self, payload: dict[str, Any] | None = None, delay_seconds: float = 0.0) -> None:
        self.payload = payload or {}
        self.delay_seconds = delay_seconds
        self.calls: list[dict[str, Any]] = []

    async def get_portfolio_manager_book_memberships(self, **kwargs: Any):
        self.calls.append(kwargs)
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        return 200, self.payload


class ValueClient:
    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: dict[str, Any] | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        self.status_code = status_code
        self.payload = payload or {}
        self.delay_seconds = delay_seconds
        self.calls: list[dict[str, Any]] = []

    async def query_bulk_portfolio_summary(self, **kwargs: Any):
        self.calls.append(kwargs)
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        return self.status_code, self.payload


def book_caller() -> AdvisorBookCallerContext:
    return AdvisorBookCallerContext(
        portfolio_manager_id="PM_SG_001",
        tenant_id="tenant-sg",
        region="APAC",
        booking_center_code="Singapore",
        role="ADVISOR",
        caller_application="lotus-workbench",
    )


def cockpit_caller() -> AdvisorCockpitCallerContext:
    return AdvisorCockpitCallerContext(
        actor_id="advisor_sg_001",
        caller_application="lotus-workbench",
        tenant_id="tenant-sg",
        region="APAC",
        booking_center_code="Singapore",
        legal_entity_code="SG01",
        role="ADVISOR",
        capabilities=frozenset({"advisory.advisor_cockpit.read"}),
        principal_status="ACTIVE",
        authorized_advisor_id="advisor_sg_001",
        authorized_portfolio_id=None,
    )


def membership_member(portfolio_id: str) -> dict[str, object]:
    return {
        "portfolio_id": portfolio_id,
        "client_id": f"CIF_{portfolio_id}",
        "booking_center_code": "Singapore",
        "portfolio_type": "ADVISORY",
        "status": "ACTIVE",
        "open_date": "2025-03-31",
        "close_date": None,
        "base_currency": "USD",
        "source_record_id": f"portfolio:{portfolio_id}",
        "membership_source": "party_role_assignment",
        "role_type": "ADVISOR",
    }


def membership_payload(*portfolio_ids: str) -> dict[str, object]:
    members = [membership_member(portfolio_id) for portfolio_id in portfolio_ids]
    return {
        "product_name": "PortfolioManagerBookMembership",
        "product_version": "v1",
        "portfolio_manager_id": "PM_SG_001",
        "tenant_id": "tenant-sg",
        "generated_at": "2026-04-10T02:00:00Z",
        "as_of_date": "2026-04-10",
        "latest_evidence_timestamp": "2026-04-10T01:59:00Z",
        "snapshot_id": "pm_book_membership:2e7dfe0c",
        "content_hash": "sha256:0123456789abcdef",
        "data_quality_status": "ACCEPTED",
        "source_evidence_current": True,
        "freshness_status": "CURRENT",
        "booking_center_code": "Singapore",
        "members": members,
        "supportability": {
            "state": "READY",
            "reason": "PM_BOOK_MEMBERSHIP_READY",
            "returned_portfolio_count": len(members),
            "filters_applied": ["portfolio_manager_id", "as_of_date"],
        },
        "lineage": {"source_system": "lotus-core"},
    }


def covered_member(portfolio_id: str, total: str, cash: str) -> dict[str, object]:
    invested = str(Decimal(total) - Decimal(cash))
    return {
        "portfolio_id": portfolio_id,
        "booking_center_code": "Singapore",
        "client_id": f"CIF_{portfolio_id}",
        "portfolio_currency": "USD",
        "reporting_currency": "USD",
        "resolved_as_of_date": "2026-04-10",
        "coverage_state": "COMPLETE",
        "coverage_reason": "snapshot_rows_complete",
        "snapshot_date": "2026-04-10",
        "snapshot_row_count": 12,
        "expected_open_position_count": 12,
        "totals": {
            "total_market_value_portfolio_currency": total,
            "total_market_value_reporting_currency": total,
            "cash_balance_portfolio_currency": cash,
            "cash_balance_reporting_currency": cash,
            "invested_market_value_portfolio_currency": invested,
            "invested_market_value_reporting_currency": invested,
        },
    }


def uncovered_member(portfolio_id: str, coverage_state: str) -> dict[str, object]:
    return {
        "portfolio_id": portfolio_id,
        "booking_center_code": None,
        "client_id": None,
        "portfolio_currency": None,
        "reporting_currency": "USD",
        "resolved_as_of_date": "2026-04-10",
        "coverage_state": coverage_state,
        "coverage_reason": "no_snapshot_rows_for_as_of_date",
        "snapshot_date": None,
        "snapshot_row_count": 0,
        "expected_open_position_count": 3,
        "totals": None,
    }


def bulk_payload(
    requested_ids: list[str],
    members: list[dict[str, object]],
    *,
    aggregate_state: str = "COMPLETE",
) -> dict[str, object]:
    covered = [member for member in members if member.get("totals") is not None]
    aggregate_totals = None
    if aggregate_state == "COMPLETE":
        aggregate_totals = {
            "total_market_value_portfolio_currency": None,
            "total_market_value_reporting_currency": str(
                sum(
                    Decimal(str(m["totals"]["total_market_value_reporting_currency"]))
                    for m in covered
                )  # type: ignore[index]
            ),
            "cash_balance_portfolio_currency": None,
            "cash_balance_reporting_currency": str(
                sum(Decimal(str(m["totals"]["cash_balance_reporting_currency"])) for m in covered)  # type: ignore[index]
            ),
            "invested_market_value_portfolio_currency": None,
            "invested_market_value_reporting_currency": str(
                sum(
                    Decimal(str(m["totals"]["invested_market_value_reporting_currency"]))  # type: ignore[index]
                    for m in covered
                )
            ),
        }
    return {
        "contract_version": "portfolio-summary-bulk-v1",
        "requested_portfolio_ids": requested_ids,
        "resolved_as_of_date": "2026-04-10",
        "reporting_currency": "USD",
        "portfolios": members,
        "aggregate": {
            "portfolio_count": len(requested_ids),
            "coverage_state": aggregate_state,
            "coverage_reason": (
                "all_members_covered"
                if aggregate_state == "COMPLETE"
                else "member_coverage_incomplete"
            ),
            "totals": aggregate_totals,
        },
    }
