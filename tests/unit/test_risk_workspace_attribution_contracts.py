from app.contracts import risk_workspace
from app.contracts.risk_workspace_attribution import (
    WorkbenchRiskAttributionContributor,
    WorkbenchRiskAttributionControls,
    WorkbenchRiskAttributionGroupingOption,
    WorkbenchRiskAttributionMethodologyContext,
    WorkbenchRiskAttributionPayload,
    WorkbenchRiskAttributionPeriodResult,
    WorkbenchRiskAttributionSet,
    WorkbenchRiskAttributionTypeOption,
)


def test_risk_attribution_contracts_remain_compatibility_reexports() -> None:
    assert risk_workspace.WorkbenchRiskAttributionContributor is WorkbenchRiskAttributionContributor
    assert risk_workspace.WorkbenchRiskAttributionControls is WorkbenchRiskAttributionControls
    assert (
        risk_workspace.WorkbenchRiskAttributionGroupingOption
        is WorkbenchRiskAttributionGroupingOption
    )
    assert (
        risk_workspace.WorkbenchRiskAttributionMethodologyContext
        is WorkbenchRiskAttributionMethodologyContext
    )
    assert risk_workspace.WorkbenchRiskAttributionPayload is WorkbenchRiskAttributionPayload
    assert (
        risk_workspace.WorkbenchRiskAttributionPeriodResult is WorkbenchRiskAttributionPeriodResult
    )
    assert risk_workspace.WorkbenchRiskAttributionSet is WorkbenchRiskAttributionSet
    assert risk_workspace.WorkbenchRiskAttributionTypeOption is WorkbenchRiskAttributionTypeOption


def test_risk_attribution_response_accepts_extracted_payload_models() -> None:
    payload = WorkbenchRiskAttributionPayload(
        controls=WorkbenchRiskAttributionControls(
            attribution_types=[
                WorkbenchRiskAttributionTypeOption(
                    key="TOTAL_RISK",
                    label="Total Risk",
                    state="ready",
                ),
                WorkbenchRiskAttributionTypeOption(
                    key="ACTIVE_RISK",
                    label="Active Risk",
                    state="ready",
                ),
            ],
            grouping_dimensions=[
                WorkbenchRiskAttributionGroupingOption(
                    key="ASSET_CLASS",
                    label="Asset Class",
                    state="ready",
                    supported_attribution_types=["TOTAL_RISK", "ACTIVE_RISK"],
                )
            ],
            selected_attribution_type="ACTIVE_RISK",
            selected_grouping_dimension="ASSET_CLASS",
        ),
        periods=[
            WorkbenchRiskAttributionPeriodResult(
                key="YTD",
                label="YTD",
                start_date="2026-01-01",
                end_date="2026-04-04",
                attribution_sets=[
                    WorkbenchRiskAttributionSet(
                        attribution_type="ACTIVE_RISK",
                        metric="TRACKING_ERROR",
                        grouping_dimension="ASSET_CLASS",
                        total_value=0.034,
                        reconciled_sum=0.033,
                        residual=0.001,
                        contributors=[
                            WorkbenchRiskAttributionContributor(
                                group_key="EQUITY",
                                group_label="Equity",
                                weight_average=0.62,
                                marginal_contribution=0.018,
                                component_contribution=0.016,
                                percent_contribution=0.47,
                            )
                        ],
                        quality_flags=["covariance:benchmark_overlap_warning"],
                    )
                ],
            )
        ],
        methodology_context=WorkbenchRiskAttributionMethodologyContext(
            covariance_method="EMPIRICAL",
            annualization_basis=252,
            requested_attribution_types=["ACTIVE_RISK"],
            requested_metrics=["TRACKING_ERROR"],
            requested_grouping_dimensions=["ASSET_CLASS"],
            min_observations_policy="STRICT",
            stateful_active_risk_supported_grouping_dimensions=[
                "POSITION",
                "SECTOR",
                "ASSET_CLASS",
            ],
            stateful_active_risk_gated_grouping_dimensions=["ISSUER"],
            stateful_active_risk_gate_reason=(
                "Benchmark issuer exposure semantics are not yet approved for active risk."
            ),
        ),
    )

    response = risk_workspace.WorkbenchRiskAttributionResponse(
        correlation_id="corr-risk-attribution",
        portfolio_id="PF_RISK_ATTR",
        period="YTD",
        detail_basis="NET",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        state="ready",
        payload=payload,
        metadata=risk_workspace.WorkbenchRiskMetadata(
            generated_at="2026-04-04T08:15:00Z",
            input_mode="stateful",
            methodology_version="attribution.v1",
            cache_status="miss",
        ),
    )

    assert response.payload is payload
    assert response.payload.periods[0].attribution_sets[0].contributors[0].group_key == "EQUITY"
