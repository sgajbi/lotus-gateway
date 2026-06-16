import pytest
from fastapi import HTTPException

from app.contracts.portfolio_common import PortfolioPartialFailure
from app.services.portfolio_workspace_components import (
    assemble_portfolio_workspace_components,
    build_portfolio_workspace_assembly_state,
    build_portfolio_workspace_response_parts,
    extract_resolved_as_of_date,
    parse_cashflow,
    parse_summary,
    parse_workspace_rebalance,
)
from app.services.portfolio_workspace_sources import (
    PortfolioWorkspaceAnalyticsResults,
    PortfolioWorkspaceSourceResults,
)


def _portfolio_result() -> tuple[int, dict[str, object]]:
    return (
        200,
        {
            "portfolio_id": "PF_1001",
            "portfolio_name": "Global Balanced",
            "client_id": "CIF_1",
            "base_currency": "USD",
            "booking_center": "SGPB",
            "status": "ACTIVE",
            "portfolio_type": "ADVISORY",
        },
    )


def _aum_result() -> tuple[int, dict[str, object]]:
    return (
        200,
        {
            "resolved_as_of_date": "2026-03-28",
            "portfolios": [
                {
                    "portfolio_id": "PF_1001",
                    "aum_reporting_currency": "1000000.129",
                    "position_count": 12,
                }
            ],
        },
    )


def _source_results(
    *,
    cash_balance_result: tuple[int, dict[str, object]] = (
        200,
        {"totals": {"total_balance_reporting_currency": "100000.125", "cash_account_count": 2}},
    ),
    cashflow_result: tuple[int, dict[str, object]] = (
        200,
        {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": "1500.129",
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        },
    ),
    support_result: tuple[int, dict[str, object]] = (
        200,
        {"business_date": "2026-03-27", "publish_allowed": True},
    ),
    readiness_result: tuple[int, dict[str, object]] = (
        200,
        {"status": "READY", "row_count": 12},
    ),
) -> PortfolioWorkspaceSourceResults:
    return PortfolioWorkspaceSourceResults(
        portfolio_result=_portfolio_result(),
        aum_result=_aum_result(),
        support_result=support_result,
        cashflow_result=cashflow_result,
        cash_balance_result=cash_balance_result,
        readiness_result=readiness_result,
    )


def test_parse_summary_records_cash_balance_partial_failure() -> None:
    warnings: list[str] = []
    partial_failures: list[PortfolioPartialFailure] = []

    summary = parse_summary(
        _aum_result(),
        (503, {"detail": "cash backend down"}),
        warnings,
        partial_failures,
    )

    assert summary.assets_under_management_base == 1000000.13
    assert summary.cash_market_value_base == 0.0
    assert warnings == ["PORTFOLIO_CASH_BALANCES_UNAVAILABLE"]
    assert partial_failures[0].source_service == "lotus-core"
    assert partial_failures[0].error_code == "PORTFOLIO_CASH_BALANCES_UNAVAILABLE"


def test_parse_cashflow_returns_none_and_records_unavailable_source() -> None:
    warnings: list[str] = []
    partial_failures: list[PortfolioPartialFailure] = []

    cashflow = parse_cashflow((503, {"detail": "cashflow unavailable"}), warnings, partial_failures)

    assert cashflow is None
    assert warnings == ["PORTFOLIO_CASHFLOW_UNAVAILABLE"]
    assert partial_failures[0].source_service == "lotus-core"


def test_parse_workspace_rebalance_uses_supportability_when_runs_absent() -> None:
    warnings: list[str] = []
    partial_failures: list[PortfolioPartialFailure] = []

    rebalance = parse_workspace_rebalance(
        result=None,
        supportability_result=(
            200,
            {
                "state": "degraded",
                "reason": "action_register_stale",
                "freshness_bucket": "stale",
                "run_count": 4,
            },
        ),
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert rebalance is not None
    assert rebalance.status == "NO_RUNS"
    assert rebalance.supportability is not None
    assert rebalance.supportability.state == "degraded"
    assert rebalance.supportability.run_count == 4
    assert warnings == []
    assert partial_failures == []


def test_workspace_assembly_rejects_source_client_errors() -> None:
    with pytest.raises(HTTPException) as exc:
        build_portfolio_workspace_assembly_state(
            source_results=_source_results(
                support_result=(404, {"detail": "missing portfolio"}),
            )
        )

    assert exc.value.status_code == 404
    assert "support overview rejected" in str(exc.value.detail)


def test_assemble_workspace_components_preserves_source_warnings_and_parts() -> None:
    source_results = _source_results(cash_balance_result=(503, {"detail": "cash backend down"}))
    assembly_state = build_portfolio_workspace_assembly_state(source_results=source_results)

    components = assemble_portfolio_workspace_components(
        source_results=source_results,
        analytics_results=PortfolioWorkspaceAnalyticsResults(
            performance_result=None,
            rebalance_result=None,
            rebalance_supportability_result=None,
        ),
        assembly_state=assembly_state,
    )
    response_parts = build_portfolio_workspace_response_parts(
        portfolio_id="PF_1001",
        components=components,
        source_results=source_results,
        effective_as_of_date="2026-03-27",
        resolved_as_of_date="2026-03-28",
        reporting_currency="CHF",
    )

    assert components.portfolio.portfolio_id == "PF_1001"
    assert components.profile.status == "ACTIVE"
    assert components.operations is not None
    assert components.operations.publish_allowed is True
    assert components.cashflow_outlook is not None
    assert components.rebalance is None
    assert components.warnings == ["PORTFOLIO_CASH_BALANCES_UNAVAILABLE"]
    assert response_parts.reporting.status == "READY"
    assert response_parts.reporting.row_count == 12
    assert (
        response_parts.control_capabilities.historical_snapshots.effective_as_of_date
        == "2026-03-28"
    )
    assert response_parts.workflow_cues
    assert response_parts.partial_failures == components.partial_failures


def test_extract_resolved_as_of_date_uses_source_payload_only_when_available() -> None:
    assert extract_resolved_as_of_date(_aum_result()) == "2026-03-28"
    assert extract_resolved_as_of_date((503, {"resolved_as_of_date": "2026-03-28"})) is None
