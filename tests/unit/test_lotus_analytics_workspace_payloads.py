from app.clients.lotus_analytics_workspace_payloads import build_workspace_summary_payload


def test_build_workspace_summary_payload_uses_explicit_period_and_dedupes_frequency() -> None:
    payload = build_workspace_summary_payload(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        report_end_date="2026-03-27",
        report_start_date="2026-01-01",
        period="QTD",
        chart_frequency="monthly",
        benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        periods=None,
    )

    assert payload["input_mode"] == "stateful"
    assert payload["portfolio_id"] == "PB_SG_GLOBAL_BAL_001"
    assert payload["report_start_date"] == "2026-01-01"
    assert payload["report_ccy"] == "USD"
    assert payload["periods"] == [
        {"period": "EXPLICIT", "frequencies": ["monthly", "quarterly", "yearly"]}
    ]
    assert payload["benchmark"] == {
        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
        "input_mode": "stateful",
        "return_source": "calculated",
        "stateful_input": {},
    }


def test_build_workspace_summary_payload_preserves_caller_periods() -> None:
    periods = [{"period": "YTD", "frequencies": ["daily"]}]

    payload = build_workspace_summary_payload(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        chart_frequency="monthly",
        benchmark_id=None,
        reporting_currency=None,
        periods=periods,
    )

    assert payload["periods"] is periods
    assert payload["include_benchmark"] is False
    assert "benchmark" not in payload
    assert "report_ccy" not in payload
    assert "report_start_date" not in payload
