from app.contracts.portfolio import (
    PortfolioIdentity,
    PortfolioPartialFailure,
    PortfolioProfile,
    PortfolioReportingReadiness,
    PortfolioSummary,
    PortfolioWorkflowLaunchCue,
)
from app.services.portfolio_workspace_controls import build_workspace_control_capabilities
from app.services.portfolio_workspace_response import (
    PortfolioWorkspaceComponents,
    PortfolioWorkspaceResponseParts,
    assemble_portfolio_workspace_response,
)


def test_assemble_portfolio_workspace_response_preserves_contract_parts() -> None:
    portfolio = PortfolioIdentity(
        portfolio_id="PF_1001",
        display_name="Global Balanced",
        client_id="CIF_1",
        base_currency="USD",
        booking_center_code="SGPB",
    )
    profile = PortfolioProfile(status="ACTIVE", portfolio_type="ADVISORY")
    summary = PortfolioSummary(
        assets_under_management_base=1_000_000.0,
        invested_market_value_base=900_000.0,
        cash_market_value_base=100_000.0,
        cash_weight_pct=10.0,
        position_count=12,
        cash_balance_count=2,
    )
    partial_failure = PortfolioPartialFailure(
        source_service="lotus-core",
        error_code="PORTFOLIO_CASHFLOW_UNAVAILABLE",
        detail="cashflow temporarily unavailable",
    )
    components = PortfolioWorkspaceComponents(
        portfolio=portfolio,
        profile=profile,
        summary=summary,
        cashflow_outlook=None,
        performance=None,
        rebalance=None,
        operations=None,
        warnings=["PORTFOLIO_CASHFLOW_UNAVAILABLE"],
        partial_failures=[partial_failure],
    )
    workflow_cue = PortfolioWorkflowLaunchCue(
        key="performance",
        label="Performance",
        href="/performance?portfolioId=PF_1001",
    )
    response_parts = PortfolioWorkspaceResponseParts(
        reporting=PortfolioReportingReadiness(status="READY", row_count=3),
        control_capabilities=build_workspace_control_capabilities(
            portfolio=portfolio,
            profile=profile,
            requested_as_of_date="2026-03-27",
            effective_as_of_date="2026-03-27",
            requested_reporting_currency="SGD",
        ),
        workflow_cues=[workflow_cue],
        warnings=components.warnings,
        partial_failures=components.partial_failures,
    )

    response = assemble_portfolio_workspace_response(
        correlation_id="corr-portfolio-workspace",
        contract_version="v-test",
        as_of_date="2026-03-27",
        components=components,
        response_parts=response_parts,
    )

    assert response.correlation_id == "corr-portfolio-workspace"
    assert response.contract_version == "v-test"
    assert response.as_of_date == "2026-03-27"
    assert response.portfolio == portfolio
    assert response.profile == profile
    assert response.summary == summary
    assert response.reporting == response_parts.reporting
    assert response.control_capabilities == response_parts.control_capabilities
    assert response.workflow_cues == [workflow_cue]
    assert response.warnings == ["PORTFOLIO_CASHFLOW_UNAVAILABLE"]
    assert response.partial_failures == [partial_failure]
