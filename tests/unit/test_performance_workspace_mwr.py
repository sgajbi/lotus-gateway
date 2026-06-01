from app.services.performance_workspace_mwr import build_workspace_mwr_summary


def test_build_workspace_mwr_summary_maps_economics_and_notes():
    summary = build_workspace_mwr_summary(
        {
            "money_weighted_return": {
                "period_return": 14.05,
                "annualized_return": 16.1,
                "holding_period_return": 3.05,
                "input_mode": "stateful",
                "method": "XIRR",
                "status": "CALCULATED",
                "reason_codes": ["STATEFUL_CASH_FLOWS"],
                "warnings": ["FLOW_TIMING_APPROXIMATED"],
                "is_annualized_primary": True,
                "fallback_from": "DAILY_MWR",
                "fallback_reason": "INSUFFICIENT_DAILY_POINTS",
                "is_approximation": False,
                "start_date": "2026-01-01",
                "end_date": "2026-03-27",
                "economics": {
                    "begin_market_value": 450000.0,
                    "end_market_value": 508870.0,
                    "beginning_cash_flow": 30000.0,
                    "ending_cash_flow": -7500.0,
                    "flow_adjusted_end_market_value": 486370.0,
                    "net_cash_flow": 22500.0,
                    "fees": 0.0,
                },
                "notes": ["client contribution included"],
            }
        }
    )

    assert summary is not None
    assert summary.money_weighted_return_pct == 14.05
    assert summary.annualized_return_pct == 16.1
    assert summary.holding_period_return_pct == 3.05
    assert summary.input_mode == "stateful"
    assert summary.method == "XIRR"
    assert summary.reason_codes == ["STATEFUL_CASH_FLOWS"]
    assert summary.warnings == ["FLOW_TIMING_APPROXIMATED"]
    assert summary.is_annualized_primary is True
    assert summary.is_approximation is False
    assert summary.begin_market_value == 450000.0
    assert summary.end_market_value == 508870.0
    assert summary.beginning_cash_flow == 30000.0
    assert summary.ending_cash_flow == -7500.0
    assert summary.flow_adjusted_end_market_value == 486370.0
    assert summary.net_cash_flow == 22500.0
    assert summary.fees == 0.0
    assert summary.notes == ["client contribution included"]


def test_mwr_summary_builders_fail_closed_for_invalid_nested_payloads():
    assert build_workspace_mwr_summary({"money_weighted_return": []}) is None

    summary = build_workspace_mwr_summary(
        {"money_weighted_return": {"economics": [], "notes": "not-a-list"}}
    )

    assert summary is not None
    assert summary.begin_market_value is None
    assert summary.notes == []
