from app.contracts import risk_workspace
from app.contracts.risk_workspace_concentration import (
    WorkbenchIssuerConcentration,
    WorkbenchPortfolioConcentration,
    WorkbenchRiskConcentrationExecutionContext,
    WorkbenchRiskConcentrationPayload,
    WorkbenchRiskConcentrationValuationContext,
    WorkbenchSinglePositionConcentration,
    WorkbenchTopIssuerDriver,
    WorkbenchTopPositionDriver,
)


def test_risk_concentration_contracts_remain_compatibility_reexports() -> None:
    assert risk_workspace.WorkbenchPortfolioConcentration is WorkbenchPortfolioConcentration
    assert risk_workspace.WorkbenchTopPositionDriver is WorkbenchTopPositionDriver
    assert (
        risk_workspace.WorkbenchSinglePositionConcentration is WorkbenchSinglePositionConcentration
    )
    assert risk_workspace.WorkbenchTopIssuerDriver is WorkbenchTopIssuerDriver
    assert risk_workspace.WorkbenchIssuerConcentration is WorkbenchIssuerConcentration
    assert (
        risk_workspace.WorkbenchRiskConcentrationValuationContext
        is WorkbenchRiskConcentrationValuationContext
    )
    assert (
        risk_workspace.WorkbenchRiskConcentrationExecutionContext
        is WorkbenchRiskConcentrationExecutionContext
    )
    assert risk_workspace.WorkbenchRiskConcentrationPayload is WorkbenchRiskConcentrationPayload


def test_risk_concentration_response_accepts_extracted_payload_models() -> None:
    payload = WorkbenchRiskConcentrationPayload(
        portfolio_concentration=WorkbenchPortfolioConcentration(
            hhi_current=1200.0,
            hhi_proposed=1225.0,
            hhi_delta=25.0,
        ),
        single_position_concentration=WorkbenchSinglePositionConcentration(
            top_position_weight_current=0.2,
            top_position_weight_proposed=0.21,
            top_position_weight_delta=0.01,
            top_n_cumulative_weight_current=0.5,
            top_n_cumulative_weight_proposed=0.52,
            top_n_cumulative_weight_delta=0.02,
            top_n=10,
            top_position_current=WorkbenchTopPositionDriver(
                security_id="FO_FUND_PIMCO_INC",
                security_name="PIMCO GIS Income Fund",
                weight=0.2,
            ),
            top_position_proposed=WorkbenchTopPositionDriver(
                security_id="FO_FUND_PIMCO_INC",
                security_name="PIMCO GIS Income Fund",
                weight=0.21,
            ),
        ),
        issuer_concentration=WorkbenchIssuerConcentration(
            hhi_current=1500.0,
            hhi_proposed=1600.0,
            hhi_delta=100.0,
            top_issuer_weight_current=0.25,
            top_issuer_weight_proposed=0.27,
            top_issuer_weight_delta=0.02,
            coverage_status="complete",
            covered_position_count_current=10,
            covered_position_count_proposed=10,
            total_position_count_current=10,
            total_position_count_proposed=10,
            uncovered_position_count_current=0,
            uncovered_position_count_proposed=0,
            coverage_ratio_current=1.0,
            coverage_ratio_proposed=1.0,
            top_issuer_current=WorkbenchTopIssuerDriver(
                issuer_id="ULTIMATE_PIMCO",
                issuer_name="Pacific Investment Management Company LLC",
                weight=0.25,
            ),
            top_issuer_proposed=WorkbenchTopIssuerDriver(
                issuer_id="ULTIMATE_PIMCO",
                issuer_name="Pacific Investment Management Company LLC",
                weight=0.27,
            ),
        ),
        valuation_context=WorkbenchRiskConcentrationValuationContext(
            portfolio_currency="USD",
            reporting_currency="USD",
            position_basis="market_value_base",
            weight_basis="total_market_value_base",
        ),
        execution_context=WorkbenchRiskConcentrationExecutionContext(
            as_of_date="2026-04-04",
            portfolio_id="PF_RISK_CONC",
            issuer_grouping_level="ultimate_parent",
            enrichment_policy="merge_caller_then_core",
            include_cash_positions=True,
            include_zero_quantity_positions=False,
        ),
    )

    response = risk_workspace.WorkbenchRiskConcentrationResponse(
        correlation_id="corr-risk-concentration",
        portfolio_id="PF_RISK_CONC",
        period="YTD",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        state="ready",
        payload=payload,
        metadata=risk_workspace.WorkbenchRiskMetadata(
            generated_at="2026-04-04T08:15:00Z",
            input_mode="stateful",
            methodology_version="concentration.v1",
            cache_status="miss",
        ),
    )

    assert response.payload is payload
    assert response.payload.issuer_concentration.coverage_status == "complete"
