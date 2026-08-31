from app.contracts import risk_workspace
from app.contracts.risk_workspace_rolling import (
    WorkbenchRiskRollingDependencyContext,
    WorkbenchRiskRollingMetricSeriesContext,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingPayload,
    WorkbenchRiskRollingPeriodResult,
    WorkbenchRiskRollingRequestContext,
    WorkbenchRiskRollingRequestDependencyContext,
    WorkbenchRiskRollingWindowResult,
)


def test_risk_rolling_contracts_remain_compatibility_reexports() -> None:
    assert (
        risk_workspace.WorkbenchRiskRollingDependencyContext
        is WorkbenchRiskRollingDependencyContext
    )
    assert (
        risk_workspace.WorkbenchRiskRollingMetricSeriesContext
        is WorkbenchRiskRollingMetricSeriesContext
    )
    assert (
        risk_workspace.WorkbenchRiskRollingMetricSeriesPoint
        is WorkbenchRiskRollingMetricSeriesPoint
    )
    assert risk_workspace.WorkbenchRiskRollingMetricSummary is WorkbenchRiskRollingMetricSummary
    assert risk_workspace.WorkbenchRiskRollingPayload is WorkbenchRiskRollingPayload
    assert risk_workspace.WorkbenchRiskRollingPeriodResult is WorkbenchRiskRollingPeriodResult
    assert risk_workspace.WorkbenchRiskRollingRequestContext is WorkbenchRiskRollingRequestContext
    assert (
        risk_workspace.WorkbenchRiskRollingRequestDependencyContext
        is WorkbenchRiskRollingRequestDependencyContext
    )
    assert risk_workspace.WorkbenchRiskRollingWindowResult is WorkbenchRiskRollingWindowResult


def test_risk_rolling_response_accepts_extracted_payload_models() -> None:
    payload = WorkbenchRiskRollingPayload(
        periods=[
            WorkbenchRiskRollingPeriodResult(
                key="YTD",
                label="YTD",
                start_date="2026-01-01",
                end_date="2026-04-04",
                series_count=66,
                benchmark_series_count=66,
                aligned_benchmark_series_count=64,
                risk_free_series_count=65,
                aligned_risk_free_series_count=0,
                window_lengths_requested=[21, 63],
                window_count_requested=2,
                window_lengths_emitted=[21],
                window_count_emitted=1,
                benchmark_context=WorkbenchRiskRollingDependencyContext(
                    requested=True,
                    available=True,
                    aligned=True,
                    reason="APPLIED",
                ),
                risk_free_context=WorkbenchRiskRollingDependencyContext(
                    requested=True,
                    available=False,
                    aligned=False,
                    reason="Risk-free series could not be aligned for rolling Sharpe.",
                ),
                window_results=[
                    WorkbenchRiskRollingWindowResult(
                        window_length=21,
                        metric_summaries={
                            "ROLLING_VOLATILITY": WorkbenchRiskRollingMetricSummary(
                                total_point_count=66,
                                computed_point_count=46,
                                coverage_ratio=0.697,
                                min_observations_required=21,
                                warmup_point_count=20,
                                non_computed_point_count=20,
                                post_warmup_gap_point_count=0,
                                latest_observation_date="2026-04-04",
                                latest=0.1374,
                            )
                        },
                        metric_series=[
                            WorkbenchRiskRollingMetricSeriesPoint(
                                date="2026-04-01",
                                metric_values={"ROLLING_VOLATILITY": 0.131},
                            )
                        ],
                        metric_series_context=WorkbenchRiskRollingMetricSeriesContext(
                            requested=True,
                            included=True,
                            emitted_point_count=1,
                            reason="Included for drill-down request.",
                        ),
                    )
                ],
                quality_flags=["metric:ROLLING_BETA:benchmark_variance_zero"],
            )
        ],
        request_context=WorkbenchRiskRollingRequestContext(
            annualization_basis=252,
            requested_metrics=["ROLLING_VOLATILITY", "ROLLING_SHARPE"],
            window_lengths_requested=[21, 63],
            window_count_requested=2,
            alignment_policy="INNER_JOIN",
            min_observations_policy="STRICT",
            include_time_series=True,
            risk_free_context=WorkbenchRiskRollingRequestDependencyContext(
                requested=True,
                requested_metrics=["ROLLING_SHARPE"],
            ),
        ),
    )

    response = risk_workspace.WorkbenchRiskRollingResponse(
        correlation_id="corr-risk-rolling",
        portfolio_id="PF_RISK_ROLLING",
        period="YTD",
        detail_basis="NET",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        state="partial",
        payload=payload,
        metadata=risk_workspace.WorkbenchRiskMetadata(
            generated_at="2026-04-04T08:15:00Z",
            input_mode="stateful",
            methodology_version="rolling.v1",
            cache_status="miss",
        ),
    )

    assert response.payload is payload
    assert response.payload.periods[0].window_results[0].window_length == 21
    assert response.payload.request_context is not None
    assert response.payload.request_context.include_time_series is True
