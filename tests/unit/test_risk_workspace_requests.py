from app.services.risk_workspace_requests import (
    build_attribution_request,
    build_risk_periods,
    build_rolling_request,
    build_summary_request,
    normalize_detail_basis,
    normalize_period,
    resolve_reporting_currency,
)


def test_normalize_period_accepts_canonical_values_and_legacy_aliases() -> None:
    assert normalize_period("YTD") == "YTD"
    assert normalize_period("one_year") == "1Y"
    assert normalize_period("THREE_YEAR") == "3Y"
    assert normalize_period("five_year") == "5Y"
    assert normalize_period("ITD") == "SI"
    assert normalize_period("unsupported") == "YTD"


def test_build_risk_periods_preserves_explicit_window_when_complete() -> None:
    assert build_risk_periods(
        period="EXPLICIT",
        report_start_date="2026-01-01",
        report_end_date="2026-04-10",
    ) == [
        {
            "type": "EXPLICIT",
            "name": "EXPLICIT",
            "from_date": "2026-01-01",
            "to_date": "2026-04-10",
        }
    ]


def test_resolve_reporting_currency_defaults_and_normalizes() -> None:
    assert resolve_reporting_currency(None) == "USD"
    assert resolve_reporting_currency("   ") == "USD"
    assert resolve_reporting_currency("sgd") == "SGD"


def test_normalize_detail_basis_fails_closed_to_net() -> None:
    assert normalize_detail_basis("GROSS") == "GROSS"
    assert normalize_detail_basis("net") == "NET"
    assert normalize_detail_basis("unsupported") == "NET"


def test_build_summary_request_uses_stateful_lotus_risk_contract() -> None:
    request = build_summary_request(
        portfolio_id="PF_1",
        period="ONE_YEAR",
        detail_basis="GROSS",
        as_of_date="2026-04-10",
        report_start_date=None,
        report_end_date=None,
        reporting_currency="eur",
    )

    stateful_input = request["stateful_input"]
    assert request["input_mode"] == "stateful"
    assert stateful_input["portfolio_id"] == "PF_1"
    assert stateful_input["reporting_currency"] == "EUR"
    assert stateful_input["net_or_gross"] == "GROSS"
    assert stateful_input["periods"] == [{"type": "1Y", "name": "1Y"}]
    assert stateful_input["metrics"] == [
        "VOLATILITY",
        "SHARPE",
        "SORTINO",
        "BETA",
        "TRACKING_ERROR",
        "INFORMATION_RATIO",
        "VAR",
    ]


def test_build_rolling_request_selects_metrics_by_dependency_context() -> None:
    request = build_rolling_request(
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-10",
        report_start_date=None,
        report_end_date=None,
        reporting_currency="USD",
        include_time_series=True,
        include_sharpe=True,
    )

    rolling_options = request["stateful_input"]["rolling_options"]
    assert rolling_options["window_lengths"] == [21, 63, 126, 252]
    assert rolling_options["metrics"] == [
        "ROLLING_VOLATILITY",
        "ROLLING_MAX_DRAWDOWN",
        "ROLLING_SHARPE",
        "ROLLING_BETA",
        "ROLLING_TRACKING_ERROR",
        "ROLLING_INFORMATION_RATIO",
    ]
    assert rolling_options["include_time_series"] is True


def test_build_attribution_request_includes_benchmark_only_for_active_risk() -> None:
    total_risk_request = build_attribution_request(
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-10",
        report_start_date=None,
        report_end_date=None,
        reporting_currency="USD",
        attribution_type="TOTAL_RISK",
        grouping_dimension="SECTOR",
    )
    active_risk_request = build_attribution_request(
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-10",
        report_start_date=None,
        report_end_date=None,
        reporting_currency="USD",
        attribution_type="ACTIVE_RISK",
        grouping_dimension="SECTOR",
    )

    assert "benchmark_id" not in total_risk_request["stateful_input"]
    assert active_risk_request["stateful_input"]["benchmark_id"] == "BMK_1"
    assert total_risk_request["stateful_input"]["attribution_options"]["metrics"] == [
        "VOLATILITY"
    ]
    assert active_risk_request["stateful_input"]["attribution_options"]["metrics"] == [
        "TRACKING_ERROR"
    ]
