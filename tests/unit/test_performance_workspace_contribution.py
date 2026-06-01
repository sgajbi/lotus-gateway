from app.services.performance_workspace_contribution import (
    build_detail_contribution_summary,
    build_workspace_contribution_summary,
    merge_contribution_summary_views,
    parse_contribution_smoothing_evidence,
    parse_contribution_source_economics_evidence,
)


def test_build_workspace_contribution_summary_maps_period_payload():
    summary = build_workspace_contribution_summary(
        {
            "total_portfolio_return": 3.25,
            "smoothing_evidence": {
                "status": "smoothed",
                "reason_codes": ["LINKING_RESIDUAL"],
                "raw_contribution": 3.24999,
                "final_contribution": 3.25,
                "linked_return": 3.25,
                "smoothing_residual": 0.00001,
            },
            "contribution": {
                "metric_basis": "GROSS",
                "summary": {
                    "weighting_scheme": "beginning_market_value",
                    "portfolio_contribution": 3.25,
                    "coverage_mv_pct": 98.5,
                    "local_contribution": 3.0,
                    "fx_contribution": 0.25,
                },
                "levels": [
                    {
                        "level": 1,
                        "name": "Asset Class",
                        "total_portfolio_return": 3.25,
                        "rows": [
                            {
                                "key": {"asset_class": "Equity"},
                                "contribution": 2.5,
                                "weight_avg": 0.6,
                                "return": 4.1,
                                "local_contribution": 2.4,
                                "fx_contribution": 0.1,
                            }
                        ],
                    }
                ],
                "position_contributions": [
                    {
                        "position_id": "POS_1",
                        "total_contribution": 1.2,
                        "average_weight": 0.2,
                        "total_return": 6.0,
                    }
                ],
                "source_economics_evidence": {
                    "status": "complete",
                    "source_contracts": ["lotus-performance.contribution.v1"],
                    "available_economics": ["local_contribution"],
                    "source_snapshot_count": 2,
                },
            },
        }
    )

    assert summary is not None
    assert summary.metric_basis == "GROSS"
    assert summary.portfolio_contribution_pct == 3.25
    assert summary.total_portfolio_return_pct == 3.25
    assert summary.coverage_mv_pct == 98.5
    assert summary.levels[0].name == "Asset Class"
    assert summary.levels[0].rows[0].key_label == "Equity"
    assert summary.levels[0].rows[0].weight_avg_pct == 60.0
    assert summary.position_rows[0].position_id == "POS_1"
    assert summary.smoothing_evidence is not None
    assert summary.smoothing_evidence.status == "smoothed"
    assert summary.source_economics_evidence is not None
    assert summary.source_economics_evidence.source_snapshot_count == 2


def test_build_detail_contribution_summary_maps_independent_payload():
    summary = build_detail_contribution_summary(
        metric_basis="NET",
        source_economics_payload={
            "status": "partial",
            "reason_codes": ["MISSING_FX"],
            "unsupported_economics": ["fx_contribution"],
        },
        period_payload={
            "total_contribution": 1.23456,
            "total_portfolio_return": 2.34567,
            "summary": {"portfolio_contribution": 1.23456},
            "levels": [
                {
                    "level": 2,
                    "name": "Sector",
                    "rows": [{"key": {"sector": "Technology"}, "contribution": 1.23456}],
                }
            ],
            "position_contributions": [{"position_id": "POS_2", "total_contribution": 0.22222}],
        },
    )

    assert summary is not None
    assert summary.metric_basis == "NET"
    assert summary.portfolio_contribution_pct == 1.23456
    assert summary.levels[0].total_contribution_pct == 1.23456
    assert summary.levels[0].rows[0].contribution_pct == 1.23456
    assert summary.position_rows[0].contribution_pct == 0.22222
    assert summary.source_economics_evidence is not None
    assert summary.source_economics_evidence.reason_codes == ["MISSING_FX"]


def test_merge_contribution_summary_views_prefers_detail_when_present():
    summary = build_workspace_contribution_summary(
        {
            "total_portfolio_return": 3.0,
            "contribution": {
                "metric_basis": "NET",
                "summary": {"portfolio_contribution": 3.0, "coverage_mv_pct": 90.0},
                "levels": [
                    {
                        "name": "Summary",
                        "rows": [{"key": {"asset_class": "Cash"}, "contribution": 3.0}],
                    }
                ],
            },
        }
    )
    detail = build_detail_contribution_summary(
        metric_basis="NET",
        source_economics_payload={},
        period_payload={
            "summary": {"portfolio_contribution": 3.1},
            "levels": [
                {"name": "Detail", "rows": [{"key": {"asset_class": "Cash"}, "contribution": 3.1}]}
            ],
        },
    )

    merged = merge_contribution_summary_views(
        summary_contribution=summary,
        detail_contribution=detail,
    )

    assert merged is not None
    assert merged.portfolio_contribution_pct == 3.1
    assert merged.coverage_mv_pct == 90.0
    assert merged.levels[0].name == "Detail"


def test_contribution_evidence_parsers_fail_closed_for_invalid_payloads():
    assert parse_contribution_smoothing_evidence([]) is None
    assert parse_contribution_source_economics_evidence([]) is None
    assert build_workspace_contribution_summary({"contribution": []}) is None
