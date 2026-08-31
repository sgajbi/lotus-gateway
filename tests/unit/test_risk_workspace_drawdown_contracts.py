from app.contracts import risk_workspace
from app.contracts.risk_workspace_drawdown import (
    WorkbenchRiskDrawdownAnalysisContext,
    WorkbenchRiskDrawdownEpisode,
    WorkbenchRiskDrawdownPayload,
    WorkbenchRiskDrawdownPeriodResult,
    WorkbenchRiskDrawdownSummary,
    WorkbenchRiskRelativeDrawdownContext,
    WorkbenchRiskRelativeDrawdownSummary,
    WorkbenchRiskUnderwaterPoint,
)


def test_risk_drawdown_contracts_remain_compatibility_reexports() -> None:
    assert (
        risk_workspace.WorkbenchRiskDrawdownAnalysisContext is WorkbenchRiskDrawdownAnalysisContext
    )
    assert risk_workspace.WorkbenchRiskDrawdownEpisode is WorkbenchRiskDrawdownEpisode
    assert risk_workspace.WorkbenchRiskDrawdownPayload is WorkbenchRiskDrawdownPayload
    assert risk_workspace.WorkbenchRiskDrawdownPeriodResult is WorkbenchRiskDrawdownPeriodResult
    assert risk_workspace.WorkbenchRiskDrawdownSummary is WorkbenchRiskDrawdownSummary
    assert (
        risk_workspace.WorkbenchRiskRelativeDrawdownContext is WorkbenchRiskRelativeDrawdownContext
    )
    assert (
        risk_workspace.WorkbenchRiskRelativeDrawdownSummary is WorkbenchRiskRelativeDrawdownSummary
    )
    assert risk_workspace.WorkbenchRiskUnderwaterPoint is WorkbenchRiskUnderwaterPoint


def test_risk_drawdown_response_accepts_extracted_payload_models() -> None:
    payload = WorkbenchRiskDrawdownPayload(
        periods=[
            WorkbenchRiskDrawdownPeriodResult(
                key="YTD",
                label="YTD",
                start_date="2026-01-01",
                end_date="2026-04-04",
                portfolio_observation_count=65,
                benchmark_observation_count=65,
                summary=WorkbenchRiskDrawdownSummary(
                    max_drawdown=-0.124533,
                    max_drawdown_peak_date="2026-01-12",
                    max_drawdown_trough_date="2026-02-03",
                    max_drawdown_recovery_date=None,
                    is_recovered=False,
                    days_to_trough=16,
                    days_to_recovery=None,
                    time_under_water_days=34,
                    average_drawdown=-0.041208,
                    ulcer_index=0.053901,
                    drawdown_at_risk_95=-0.101552,
                    conditional_drawdown_at_risk_95=-0.117884,
                ),
                episodes=[
                    WorkbenchRiskDrawdownEpisode(
                        episode_id="dd_0001",
                        peak_date="2026-01-12",
                        trough_date="2026-02-03",
                        recovery_date=None,
                        depth=-0.124533,
                        days_to_trough=16,
                        days_to_recovery=None,
                        total_days=34,
                        is_recovered=False,
                    )
                ],
                relative_to_benchmark=WorkbenchRiskRelativeDrawdownSummary(
                    max_drawdown=-0.0821,
                    max_drawdown_peak_date="2026-01-11",
                    max_drawdown_trough_date="2026-02-01",
                    max_drawdown_recovery_date=None,
                    is_recovered=False,
                    days_to_trough=15,
                    days_to_recovery=None,
                    time_under_water_days=31,
                ),
                relative_to_benchmark_context=WorkbenchRiskRelativeDrawdownContext(
                    requested=True,
                    applied=True,
                    reason="APPLIED",
                    aligned_observation_count=63,
                ),
                underwater_series=[
                    WorkbenchRiskUnderwaterPoint(
                        date="2026-01-20",
                        drawdown=-0.0521,
                    )
                ],
            )
        ],
        analysis_context=WorkbenchRiskDrawdownAnalysisContext(
            include_underwater_series=True,
            include_episode_list=True,
            top_n_episodes=5,
            cdar_alpha=0.95,
            minimum_episode_depth_bps=0.0,
            duration_unit="BUSINESS_DAYS",
            include_benchmark=True,
            missing_benchmark_policy="IGNORE",
        ),
    )

    response = risk_workspace.WorkbenchRiskDrawdownResponse(
        correlation_id="corr-risk-drawdown",
        portfolio_id="PF_RISK_DRAWDOWN",
        period="YTD",
        detail_basis="NET",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        state="partial",
        payload=payload,
        metadata=risk_workspace.WorkbenchRiskMetadata(
            generated_at="2026-04-04T08:15:00Z",
            input_mode="stateful",
            methodology_version="drawdown.v1",
            cache_status="miss",
        ),
    )

    assert response.payload is payload
    assert response.payload.periods[0].summary is not None
    assert response.payload.periods[0].summary.max_drawdown == -0.124533
