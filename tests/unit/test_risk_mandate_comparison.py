from datetime import date

from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskMetric,
    WorkbenchRiskPeriodResult,
    WorkbenchRiskSummaryPayload,
    WorkbenchRiskSummaryResponse,
)
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
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_mandate_comparison import (
    compose_concentration_mandate_comparison,
    compose_summary_mandate_comparison,
)
from app.services.risk_mandate_sources import (
    ManageMandateHealthSource,
    ManageMandateSource,
    RiskMandateSources,
    WorkbenchCashMeasureSource,
)


def _mandate(**constraint_overrides: float | None) -> ManageMandateSource:
    constraints = {
        "cash_band_min_weight": 0.02,
        "cash_band_max_weight": 0.10,
        "single_position_max_weight": None,
        "issuer_max_weight": None,
        "sector_max_weight": None,
        "region_max_weight": None,
        "currency_max_weight": None,
        "turnover_budget": 0.15,
        "max_tracking_error": None,
        **constraint_overrides,
    }
    return ManageMandateSource.model_validate(
        {
            "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "mandate_version": "3",
            "as_of_date": "2026-05-03",
            "risk_profile": "BALANCED",
            "constraints": constraints,
            "review_policy": {
                "review_frequency": "QUARTERLY",
                "last_review_date": "2026-03-31",
                "next_review_due_date": "2026-06-30",
            },
            "source_lineage": [
                {
                    "product_name": "DiscretionaryMandateBinding",
                    "product_version": "v1",
                    "source_system": "lotus-core",
                    "data_quality_status": "COMPLETE",
                }
            ],
        }
    )


def _health(
    *, as_of_date: str = "2026-05-03", state: str = "READY", reason: str = "CASH_LIQUIDITY_READY"
) -> ManageMandateHealthSource:
    return ManageMandateHealthSource.model_validate(
        {
            "health_snapshot_id": "mh_1",
            "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "as_of_date": as_of_date,
            "health_state": state,
            "dimension_scores": [
                {
                    "dimension": "CASH_LIQUIDITY",
                    "state": state,
                    "reason_code": reason,
                }
            ],
        }
    )


def _summary(
    *, as_of_date: str = "2026-05-03", tracking_error: float = 0.04
) -> WorkbenchRiskSummaryResponse:
    return WorkbenchRiskSummaryResponse(
        correlation_id="corr-1",
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        period="YTD",
        as_of_date=as_of_date,
        benchmark_code="BMK_1",
        state="ready",
        payload=WorkbenchRiskSummaryPayload(
            periods=[
                WorkbenchRiskPeriodResult(
                    key="YTD",
                    label="YTD",
                    start_date="2026-01-01",
                    end_date=as_of_date,
                    metrics=[
                        WorkbenchRiskMetric(
                            key="TRACKING_ERROR",
                            label="Tracking Error",
                            value=tracking_error,
                            state="ready",
                        )
                    ],
                )
            ]
        ),
        metadata=WorkbenchRiskMetadata(generated_at="2026-05-03T08:00:00Z"),
    )


def _sources(
    *,
    mandate: ManageMandateSource | None = None,
    health: ManageMandateHealthSource | None = None,
    cash_value: float = 0.0859,
    cash_as_of: str = "2026-05-03",
) -> RiskMandateSources:
    return RiskMandateSources(
        mandate=mandate or _mandate(),
        health=health or _health(),
        cash=WorkbenchCashMeasureSource(
            value=cash_value, as_of_date=date.fromisoformat(cash_as_of)
        ),
    )


def test_summary_uses_manage_cash_verdict_and_calculates_signed_headroom() -> None:
    response = compose_summary_mandate_comparison(
        response=_summary(),
        sources=_sources(),
    )

    assert response.mandate_comparison is not None
    comparison = response.mandate_comparison
    assert comparison.risk_profile == "BALANCED"
    assert comparison.date_alignment_state == "aligned"
    assert comparison.review_policy is not None
    assert comparison.review_policy.state == "scheduled"
    cash = comparison.constraints[0]
    assert cash.state == "within"
    assert cash.headroom == 0.0141
    assert cash.source_state == "READY"


def test_summary_preserves_manage_cash_breach_instead_of_reclassifying_it() -> None:
    response = compose_summary_mandate_comparison(
        response=_summary(),
        sources=_sources(
            health=_health(state="PENDING_REVIEW", reason="CASH_ABOVE_BAND"),
            cash_value=0.1066,
        ),
    )

    assert response.mandate_comparison is not None
    cash = response.mandate_comparison.constraints[0]
    assert cash.state == "breach"
    assert cash.headroom == -0.0066
    assert cash.source_reason_code == "CASH_ABOVE_BAND"


def test_summary_refuses_to_blend_mismatched_health_and_cash_dates() -> None:
    response = compose_summary_mandate_comparison(
        response=_summary(as_of_date="2026-04-10"),
        sources=_sources(
            health=_health(as_of_date="2026-05-03"),
            cash_value=0.1066,
            cash_as_of="2026-04-10",
        ),
    )

    assert response.mandate_comparison is not None
    comparison = response.mandate_comparison
    assert comparison.date_alignment_state == "mismatch"
    assert comparison.supportability.state == "partial"
    assert comparison.constraints[0].state == "measure_unavailable"
    assert comparison.constraints[0].headroom is None
    assert "not aligned" in comparison.constraints[0].reason


def test_summary_refuses_a_manage_cash_verdict_that_conflicts_with_aligned_numbers() -> None:
    response = compose_summary_mandate_comparison(
        response=_summary(),
        sources=_sources(
            health=_health(state="READY", reason="CASH_LIQUIDITY_READY"),
            cash_value=0.1066,
        ),
    )

    assert response.mandate_comparison is not None
    cash = response.mandate_comparison.constraints[0]
    assert cash.state == "measure_unavailable"
    assert cash.headroom is None
    assert "conflicts" in cash.reason
    assert cash.source_state == "READY"


def test_summary_never_classifies_a_risk_measure_without_a_source_limit() -> None:
    response = compose_summary_mandate_comparison(
        response=_summary(tracking_error=0.20),
        sources=_sources(mandate=_mandate(max_tracking_error=None)),
    )

    assert response.mandate_comparison is not None
    tracking_error = response.mandate_comparison.constraints[1]
    assert tracking_error.state == "not_defined"
    assert tracking_error.limit is None
    assert tracking_error.headroom is None


def test_summary_reports_manage_unavailability_without_hiding_risk_measures() -> None:
    response = compose_summary_mandate_comparison(
        response=_summary(),
        sources=RiskMandateSources(
            mandate=None,
            health=None,
            cash=None,
            mandate_failure_reason="Lotus Manage did not return an approved mandate.",
        ),
    )

    assert response.payload is not None
    assert response.payload.periods[0].metrics[0].value == 0.04
    assert response.mandate_comparison is not None
    assert response.mandate_comparison.supportability.state == "unavailable"
    assert response.mandate_comparison.constraints == []


def test_summary_uses_risk_dependency_reason_for_unavailable_measure() -> None:
    unavailable = _summary().model_copy(
        update={
            "state": "unavailable",
            "payload": None,
            "partial_failures": [
                WorkbenchPartialFailure(
                    source_service="lotus-risk",
                    error_code="HTTP_424",
                    detail="risk_source_dependency_unavailable",
                )
            ],
        }
    )

    response = compose_summary_mandate_comparison(
        response=unavailable,
        sources=_sources(mandate=_mandate(max_tracking_error=0.05)),
    )

    assert response.mandate_comparison is not None
    tracking_error = response.mandate_comparison.constraints[1]
    assert tracking_error.state == "measure_unavailable"
    assert tracking_error.reason == "risk_source_dependency_unavailable"
    assert "endpoint unavailable" not in tracking_error.reason.lower()


def _concentration() -> WorkbenchRiskConcentrationResponse:
    return WorkbenchRiskConcentrationResponse(
        correlation_id="corr-1",
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        period="YTD",
        as_of_date="2026-05-03",
        benchmark_code="BMK_1",
        state="ready",
        payload=WorkbenchRiskConcentrationPayload(
            portfolio_concentration=WorkbenchPortfolioConcentration(
                hhi_current=1200,
                hhi_proposed=1200,
                hhi_delta=0,
            ),
            single_position_concentration=WorkbenchSinglePositionConcentration(
                top_position_weight_current=0.1897,
                top_position_weight_proposed=0.1897,
                top_position_weight_delta=0,
                top_n_cumulative_weight_current=0.50,
                top_n_cumulative_weight_proposed=0.50,
                top_n_cumulative_weight_delta=0,
                top_n=10,
                top_position_current=WorkbenchTopPositionDriver(weight=0.1897),
                top_position_proposed=WorkbenchTopPositionDriver(weight=0.1897),
            ),
            issuer_concentration=WorkbenchIssuerConcentration(
                hhi_current=1400,
                hhi_proposed=1400,
                hhi_delta=0,
                top_issuer_weight_current=0.2107,
                top_issuer_weight_proposed=0.2107,
                top_issuer_weight_delta=0,
                coverage_status="complete",
                covered_position_count_current=10,
                covered_position_count_proposed=10,
                total_position_count_current=10,
                total_position_count_proposed=10,
                uncovered_position_count_current=0,
                uncovered_position_count_proposed=0,
                coverage_ratio_current=1,
                coverage_ratio_proposed=1,
                top_issuer_current=WorkbenchTopIssuerDriver(weight=0.2107),
                top_issuer_proposed=WorkbenchTopIssuerDriver(weight=0.2107),
            ),
            valuation_context=WorkbenchRiskConcentrationValuationContext(
                weight_basis="total_market_value_base"
            ),
            execution_context=WorkbenchRiskConcentrationExecutionContext(
                as_of_date="2026-05-03",
                issuer_grouping_level="ultimate_parent",
                enrichment_policy="merge_caller_then_core",
            ),
        ),
        metadata=WorkbenchRiskMetadata(generated_at="2026-05-03T08:00:00Z"),
    )


def test_concentration_compares_position_and_issuer_on_the_source_weight_basis() -> None:
    response = compose_concentration_mandate_comparison(
        response=_concentration(),
        sources=_sources(mandate=_mandate(single_position_max_weight=0.20, issuer_max_weight=0.20)),
    )

    assert response.mandate_comparison is not None
    position, issuer = response.mandate_comparison.constraints
    assert position.state == "within"
    assert position.headroom == 0.0103
    assert position.measure is not None
    assert position.measure.basis == "total_market_value_base"
    assert issuer.state == "breach"
    assert issuer.headroom == -0.0107


def test_concentration_refuses_classification_without_source_weight_basis() -> None:
    concentration = _concentration()
    assert concentration.payload is not None
    concentration.payload.valuation_context = None

    response = compose_concentration_mandate_comparison(
        response=concentration,
        sources=_sources(mandate=_mandate(single_position_max_weight=0.20, issuer_max_weight=0.20)),
    )

    assert response.mandate_comparison is not None
    assert {item.state for item in response.mandate_comparison.constraints} == {
        "measure_unavailable"
    }
    assert all(item.headroom is None for item in response.mandate_comparison.constraints)
    assert all("weight basis" in item.reason for item in response.mandate_comparison.constraints)
