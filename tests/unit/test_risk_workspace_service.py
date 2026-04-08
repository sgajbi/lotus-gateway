import pytest

from app.services.risk_workspace_service import RiskWorkspaceService


class _StubRiskClient:
    def __init__(self) -> None:
        self.calculate_calls: list[dict] = []
        self.concentration_calls: list[dict] = []
        self.drawdown_calls: list[dict] = []
        self.rolling_calls: list[dict] = []
        self.attribution_calls: list[dict] = []
        self.calculate_status = 200
        self.concentration_status = 200
        self.drawdown_status = 200
        self.rolling_status = 200
        self.attribution_status = 200
        self.calculate_payload: dict = {
            "scope": {
                "as_of_date": "2026-04-04",
                "reporting_currency": "USD",
                "net_or_gross": "NET",
            },
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-04-04",
                    "metrics": {
                        "VOLATILITY": {"value": 0.12},
                        "SHARPE": {"value": 1.4},
                        "SORTINO": {"value": 1.7},
                        "BETA": {"value": 0.92},
                        "TRACKING_ERROR": {"value": 0.04},
                        "INFORMATION_RATIO": {"value": 0.3},
                        "VAR": {"value": -0.02, "details": {"expected_shortfall": -0.03}},
                    },
                }
            },
        }
        self.concentration_payload: dict = {
            "source_service": "lotus-risk",
            "input_mode": "stateful",
            "risk_proxy": {"hhi_current": 1200.0, "hhi_proposed": 1200.0, "hhi_delta": 0.0},
            "single_position_concentration": {
                "top_position_weight_current": 0.18,
                "top_position_weight_proposed": 0.18,
                "top_position_weight_delta": 0.0,
                "top_n_cumulative_weight_current": 0.42,
                "top_n_cumulative_weight_proposed": 0.42,
                "top_n_cumulative_weight_delta": 0.0,
                "top_n": 10,
                "top_position_current": {
                    "security_id": "FO_FUND_PIMCO_INC",
                    "security_name": "PIMCO GIS Income Fund",
                    "weight": 0.18,
                },
                "top_position_proposed": {
                    "security_id": "FO_FUND_PIMCO_INC",
                    "security_name": "PIMCO GIS Income Fund",
                    "weight": 0.18,
                },
            },
            "issuer_concentration": {
                "hhi_current": 1400.0,
                "hhi_proposed": 1450.0,
                "hhi_delta": 50.0,
                "top_issuer_weight_current": 0.2,
                "top_issuer_weight_proposed": 0.21,
                "top_issuer_weight_delta": 0.01,
                "coverage_status": "partial",
                "covered_position_count_current": 8,
                "covered_position_count_proposed": 8,
                "total_position_count_current": 10,
                "total_position_count_proposed": 10,
                "uncovered_position_count_current": 2,
                "uncovered_position_count_proposed": 2,
                "coverage_ratio_current": 0.8,
                "coverage_ratio_proposed": 0.8,
                "note": "Two positions have no issuer enrichment.",
                "top_issuer_current": {
                    "issuer_id": "ULTIMATE_PIMCO",
                    "issuer_name": "Pacific Investment Management Company LLC",
                    "weight": 0.2,
                },
                "top_issuer_proposed": {
                    "issuer_id": "ULTIMATE_PIMCO",
                    "issuer_name": "Pacific Investment Management Company LLC",
                    "weight": 0.21,
                },
            },
            "valuation_context": {
                "portfolio_currency": "USD",
                "reporting_currency": "USD",
                "position_basis": "market_value_base",
                "weight_basis": "total_market_value_base",
            },
            "metadata": {
                "as_of_date": "2026-04-04",
                "portfolio_id": "PF_1",
                "issuer_grouping_level": "ultimate_parent",
                "enrichment_policy": "merge_caller_then_core",
                "include_cash_positions": True,
                "include_zero_quantity_positions": False,
            },
        }
        self.drawdown_payload: dict = {
            "source_service": "lotus-risk",
            "input_mode": "stateful",
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-04-04",
                    "summary": {
                        "max_drawdown": -0.124533,
                        "max_drawdown_peak_date": "2026-01-12",
                        "max_drawdown_trough_date": "2026-02-03",
                        "max_drawdown_recovery_date": None,
                        "is_recovered": False,
                        "days_to_trough": 16,
                        "days_to_recovery": None,
                        "time_under_water_days": 34,
                        "average_drawdown": -0.041208,
                        "ulcer_index": 0.053901,
                        "drawdown_at_risk_95": -0.101552,
                        "conditional_drawdown_at_risk_95": -0.117884,
                    },
                    "episodes": [
                        {
                            "episode_id": "dd_0002",
                            "peak_date": "2026-02-12",
                            "trough_date": "2026-02-13",
                            "recovery_date": None,
                            "depth": -0.055,
                            "days_to_trough": 1,
                            "days_to_recovery": None,
                            "total_days": 7,
                            "is_recovered": False,
                        },
                        {
                            "episode_id": "dd_0001",
                            "peak_date": "2026-01-12",
                            "trough_date": "2026-02-03",
                            "recovery_date": None,
                            "depth": -0.124533,
                            "days_to_trough": 16,
                            "days_to_recovery": None,
                            "total_days": 34,
                            "is_recovered": False,
                        },
                    ],
                    "relative_to_benchmark": {
                        "max_drawdown": -0.0821,
                        "max_drawdown_peak_date": "2026-01-11",
                        "max_drawdown_trough_date": "2026-02-01",
                    },
                    "underwater_series": None,
                    "error": None,
                }
            },
            "metadata": {"contract_version": "v1", "methodology_version": "drawdown.v1"},
        }
        self.rolling_payload: dict = {
            "source_service": "lotus-risk",
            "input_mode": "stateful",
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-04-04",
                    "series_count": 66,
                    "window_results": [
                        {
                            "window_length": 21,
                            "metric_summaries": {
                                "ROLLING_VOLATILITY": {
                                    "latest": 0.1374,
                                    "average": 0.1221,
                                    "minimum": 0.0913,
                                    "maximum": 0.1662,
                                    "p05": 0.0975,
                                    "p50": 0.1218,
                                    "p95": 0.1611,
                                },
                                "ROLLING_MAX_DRAWDOWN": {
                                    "latest": -0.034,
                                    "average": -0.028,
                                    "minimum": -0.051,
                                    "maximum": -0.012,
                                    "p05": -0.048,
                                    "p50": -0.029,
                                    "p95": -0.015,
                                },
                            },
                            "metric_series": None,
                        },
                        {
                            "window_length": 63,
                            "metric_summaries": {
                                "ROLLING_VOLATILITY": {
                                    "latest": 0.142,
                                    "average": 0.128,
                                    "minimum": 0.104,
                                    "maximum": 0.171,
                                    "p05": 0.108,
                                    "p50": 0.129,
                                    "p95": 0.168,
                                }
                            },
                            "metric_series": None,
                        },
                    ],
                    "quality_flags": ["metric:ROLLING_BETA:benchmark_variance_zero"],
                    "error": None,
                }
            },
            "metadata": {"contract_version": "v1", "methodology_version": "rolling_metrics.v1"},
        }
        self.attribution_payload: dict = {
            "source_service": "lotus-risk",
            "input_mode": "stateful",
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-04-04",
                    "attribution_sets": [
                        {
                            "attribution_type": "TOTAL_RISK",
                            "metric": "VOLATILITY",
                            "grouping_dimension": "SECTOR",
                            "total_value": 0.124,
                            "reconciled_sum": 0.123,
                            "residual": 0.001,
                            "contributors": [
                                {
                                    "group_key": "SECTOR_TECH",
                                    "group_label": "Technology",
                                    "weight_average": 0.42,
                                    "marginal_contribution": 0.051,
                                    "component_contribution": 0.044,
                                    "percent_contribution": 0.355,
                                },
                                {
                                    "group_key": "SECTOR_HEALTH",
                                    "group_label": "Healthcare",
                                    "weight_average": 0.18,
                                    "marginal_contribution": 0.022,
                                    "component_contribution": 0.019,
                                    "percent_contribution": 0.153,
                                },
                            ],
                            "quality_flags": [],
                        }
                    ],
                    "error": None,
                }
            },
            "metadata": {
                "contract_version": "v1",
                "methodology_version": "historical_attribution.v1",
            },
        }

    async def post_risk_calculate(self, payload: dict, correlation_id: str):
        self.calculate_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.calculate_status, self.calculate_payload

    async def post_risk_concentration(self, payload: dict, correlation_id: str):
        self.concentration_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.concentration_status, self.concentration_payload

    async def post_risk_drawdown(self, payload: dict, correlation_id: str):
        self.drawdown_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.drawdown_status, self.drawdown_payload

    async def post_risk_rolling_metrics(self, payload: dict, correlation_id: str):
        self.rolling_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.rolling_status, self.rolling_payload

    async def post_risk_historical_attribution(self, payload: dict, correlation_id: str):
        self.attribution_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.attribution_status, self.attribution_payload


@pytest.mark.asyncio
async def test_risk_summary_uses_stateful_request_and_maps_supportability() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_summary(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
    )

    request = client.calculate_calls[0]["payload"]
    assert request["input_mode"] == "stateful"
    assert "stateless_input" not in request
    assert request["stateful_input"]["portfolio_id"] == "PF_1"
    assert request["stateful_input"]["metrics"] == [
        "VOLATILITY",
        "SHARPE",
        "SORTINO",
        "BETA",
        "TRACKING_ERROR",
        "INFORMATION_RATIO",
        "VAR",
    ]
    assert response.state == "ready"
    assert response.payload is not None
    assert response.payload.periods[0].metrics[0].label == "Volatility"
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "ready",
        "benchmark_returns": "ready",
        "risk_free_series": "ready",
    }


@pytest.mark.asyncio
async def test_risk_summary_reports_partial_when_benchmark_metrics_have_errors() -> None:
    client = _StubRiskClient()
    client.calculate_payload["results"]["YTD"]["metrics"]["TRACKING_ERROR"] = {
        "value": None,
        "details": {"error": "benchmark returns unavailable"},
    }
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_summary(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
    )

    assert response.state == "partial"
    assert response.payload is not None
    tracking_error = [
        metric for metric in response.payload.periods[0].metrics if metric.key == "TRACKING_ERROR"
    ][0]
    assert tracking_error.state == "partial"
    assert tracking_error.reason == "benchmark returns unavailable"


@pytest.mark.asyncio
async def test_risk_concentration_uses_stateful_request_and_maps_issuer_supportability() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_concentration(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        benchmark_code="BMK_1",
    )

    request = client.concentration_calls[0]["payload"]
    assert request["input_mode"] == "stateful"
    assert request["stateful_input"]["portfolio_id"] == "PF_1"
    assert request["issuer_grouping_level"] == "ultimate_parent"
    assert request["enrichment_policy"] == "merge_caller_then_core"
    assert response.state == "partial"
    assert response.payload is not None
    assert response.payload.portfolio_concentration.hhi_current == 1200.0
    assert response.payload.single_position_concentration.top_position_current.security_name == (
        "PIMCO GIS Income Fund"
    )
    assert response.payload.issuer_concentration.coverage_ratio_current == 0.8
    assert response.payload.execution_context is not None
    assert response.payload.execution_context.issuer_grouping_level == "ultimate_parent"
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_positions": "ready",
        "issuer_enrichment": "partial",
        "issuer_grouping": "ready",
        "valuation_basis": "ready",
    }


@pytest.mark.asyncio
async def test_risk_workspace_cache_reuses_identical_summary_requests() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    first = await service.get_summary(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
    )
    second = await service.get_summary(
        portfolio_id="PF_1",
        correlation_id="corr-2",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
    )

    assert len(client.calculate_calls) == 1
    assert first.metadata.cache_status == "miss"
    assert second.metadata.cache_status == "hit"
    assert second.correlation_id == "corr-2"


@pytest.mark.asyncio
async def test_risk_summary_returns_unavailable_envelope_on_upstream_failure() -> None:
    client = _StubRiskClient()
    client.calculate_status = 503
    client.calculate_payload = {"detail": "risk unavailable"}
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_summary(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
    )

    assert response.state == "unavailable"
    assert response.payload is None
    assert response.partial_failures[0].error_code == "HTTP_503"
    assert response.partial_failures[0].detail == "risk unavailable"


@pytest.mark.asyncio
async def test_risk_concentration_returns_unavailable_envelope_on_malformed_success() -> None:
    client = _StubRiskClient()
    client.concentration_payload = {
        "risk_proxy": {"hhi_current": 1200.0, "hhi_proposed": 1200.0, "hhi_delta": 0.0}
    }
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_concentration(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        benchmark_code="BMK_1",
    )

    assert response.state == "unavailable"
    assert response.payload is None
    assert response.partial_failures[0].error_code == "MALFORMED_RISK_CONCENTRATION"
    assert "single_position_concentration" in response.partial_failures[0].detail
    assert "issuer_concentration" in response.partial_failures[0].detail


@pytest.mark.asyncio
async def test_risk_drawdown_uses_stateful_request_and_keeps_underwater_out_of_first_paint() -> (
    None
):
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_drawdown(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_underwater_series=False,
    )

    request = client.drawdown_calls[0]["payload"]
    assert request["input_mode"] == "stateful"
    assert request["stateful_input"]["portfolio_id"] == "PF_1"
    assert request["stateful_input"]["benchmark_policy"] == {
        "include_benchmark": True,
        "missing_benchmark_policy": "IGNORE",
    }
    assert request["analysis_options"]["include_underwater_series"] is False
    assert response.state == "partial"
    assert response.payload is not None
    assert response.payload.periods[0].summary is not None
    assert response.payload.periods[0].underwater_series is None
    assert response.payload.periods[0].episodes[0].episode_id == "dd_0001"
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "ready",
        "benchmark_relative_drawdown": "ready",
        "underwater_series": "partial",
    }


@pytest.mark.asyncio
async def test_risk_drawdown_requests_underwater_detail_on_demand_with_distinct_cache_key() -> None:
    client = _StubRiskClient()
    client.drawdown_payload["results"]["YTD"]["underwater_series"] = [
        {"date": "2026-01-20", "drawdown": -0.0521},
        {"date": "2026-01-21", "drawdown": -0.061},
    ]
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    first = await service.get_drawdown(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_underwater_series=False,
    )
    second = await service.get_drawdown(
        portfolio_id="PF_1",
        correlation_id="corr-2",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_underwater_series=True,
    )
    third = await service.get_drawdown(
        portfolio_id="PF_1",
        correlation_id="corr-3",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_underwater_series=True,
    )

    assert len(client.drawdown_calls) == 2
    assert (
        client.drawdown_calls[0]["payload"]["analysis_options"]["include_underwater_series"]
        is False
    )
    assert (
        client.drawdown_calls[1]["payload"]["analysis_options"]["include_underwater_series"] is True
    )
    assert first.metadata.cache_status == "miss"
    assert second.metadata.cache_status == "miss"
    assert third.metadata.cache_status == "hit"
    assert second.payload is not None
    assert second.payload.periods[0].underwater_series is not None


@pytest.mark.asyncio
async def test_risk_drawdown_reports_partial_when_benchmark_relative_summary_is_missing() -> None:
    client = _StubRiskClient()
    client.drawdown_payload["results"]["YTD"]["relative_to_benchmark"] = None
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_drawdown(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_underwater_series=False,
    )

    assert response.state == "partial"
    benchmark_support = {item.key: item for item in response.supportability}[
        "benchmark_relative_drawdown"
    ]
    assert benchmark_support.state == "partial"
    assert benchmark_support.reason == "Benchmark-relative drawdown was not returned by lotus-risk."


@pytest.mark.asyncio
async def test_risk_drawdown_returns_unavailable_envelope_on_upstream_failure() -> None:
    client = _StubRiskClient()
    client.drawdown_status = 503
    client.drawdown_payload = {"detail": "drawdown unavailable"}
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_drawdown(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_underwater_series=False,
    )

    assert response.state == "unavailable"
    assert response.payload is None
    assert response.partial_failures[0].error_code == "HTTP_503"
    assert response.partial_failures[0].detail == "drawdown unavailable"


@pytest.mark.asyncio
async def test_risk_rolling_uses_stateful_request_and_maps_quality_flags() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_rolling(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_time_series=False,
    )

    request = client.rolling_calls[0]["payload"]
    assert request["input_mode"] == "stateful"
    assert request["stateful_input"]["portfolio_id"] == "PF_1"
    assert request["stateful_input"]["rolling_options"]["window_lengths"] == [21, 63, 126, 252]
    assert request["stateful_input"]["rolling_options"]["include_time_series"] is False
    assert request["stateful_input"]["rolling_options"]["metrics"] == [
        "ROLLING_VOLATILITY",
        "ROLLING_MAX_DRAWDOWN",
        "ROLLING_SHARPE",
        "ROLLING_BETA",
        "ROLLING_TRACKING_ERROR",
        "ROLLING_INFORMATION_RATIO",
    ]
    assert response.state == "partial"
    assert response.payload is not None
    assert response.payload.periods[0].window_results[0].window_length == 21
    assert response.payload.periods[0].quality_flags == [
        "metric:ROLLING_BETA:benchmark_variance_zero"
    ]
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "ready",
        "benchmark_returns": "ready",
        "risk_free_series": "ready",
        "rolling_time_series": "partial",
    }


@pytest.mark.asyncio
async def test_risk_rolling_retries_without_sharpe_when_risk_free_dependency_fails() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    async def _rolling(payload: dict, correlation_id: str):
        client.rolling_calls.append({"payload": payload, "correlation_id": correlation_id})
        if len(client.rolling_calls) == 1:
            return 424, {
                "detail": {
                    "message": "lotus-core returned no usable risk-free returns for rolling Sharpe",
                }
            }
        return client.rolling_status, client.rolling_payload

    client.post_risk_rolling_metrics = _rolling  # type: ignore[method-assign]

    response = await service.get_rolling(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_time_series=False,
    )

    assert len(client.rolling_calls) == 2
    assert (
        "ROLLING_SHARPE"
        in client.rolling_calls[0]["payload"]["stateful_input"]["rolling_options"]["metrics"]
    )
    assert (
        "ROLLING_SHARPE"
        not in client.rolling_calls[1]["payload"]["stateful_input"]["rolling_options"]["metrics"]
    )
    risk_free_support = {item.key: item for item in response.supportability}["risk_free_series"]
    assert risk_free_support.state == "partial"
    assert "risk-free returns" in (risk_free_support.reason or "")
    assert response.partial_failures[-1].error_code == "ROLLING_SHARPE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_risk_rolling_time_series_uses_distinct_cache_key() -> None:
    client = _StubRiskClient()
    client.rolling_payload["results"]["YTD"]["window_results"][0]["metric_series"] = [
        {
            "date": "2026-04-01",
            "metric_values": {
                "ROLLING_VOLATILITY": 0.131,
                "ROLLING_MAX_DRAWDOWN": -0.03,
            },
        }
    ]
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    first = await service.get_rolling(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code=None,
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_time_series=False,
    )
    second = await service.get_rolling(
        portfolio_id="PF_1",
        correlation_id="corr-2",
        period="YTD",
        detail_basis="NET",
        benchmark_code=None,
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_time_series=True,
    )
    third = await service.get_rolling(
        portfolio_id="PF_1",
        correlation_id="corr-3",
        period="YTD",
        detail_basis="NET",
        benchmark_code=None,
        as_of_date="2026-04-04",
        reporting_currency="USD",
        include_time_series=True,
    )

    assert len(client.rolling_calls) == 2
    assert first.metadata.cache_status == "miss"
    assert second.metadata.cache_status == "miss"
    assert third.metadata.cache_status == "hit"
    assert second.payload is not None
    assert second.payload.periods[0].window_results[0].metric_series is not None


@pytest.mark.asyncio
async def test_risk_attribution_uses_stateful_total_risk_request_and_maps_controls() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_attribution(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        attribution_type="TOTAL_RISK",
        grouping_dimension="SECTOR",
    )

    request = client.attribution_calls[0]["payload"]
    assert request["input_mode"] == "stateful"
    assert request["stateful_input"]["portfolio_id"] == "PF_1"
    assert request["stateful_input"]["attribution_options"] == {
        "attribution_types": ["TOTAL_RISK"],
        "metrics": ["VOLATILITY"],
        "grouping_dimensions": ["SECTOR"],
        "annualization_basis": 252,
    }
    assert response.state == "ready"
    assert response.payload is not None
    assert response.payload.controls.selected_attribution_type == "TOTAL_RISK"
    assert response.payload.controls.selected_grouping_dimension == "SECTOR"
    assert (
        response.payload.periods[0].attribution_sets[0].contributors[0].group_label == "Technology"
    )
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "ready",
        "exposure_history": "ready",
        "benchmark_exposure_context": "ready",
    }


@pytest.mark.asyncio
async def test_risk_attribution_uses_stateful_active_risk_request_for_supported_grouping() -> None:
    client = _StubRiskClient()
    client.attribution_payload["results"]["YTD"]["attribution_sets"][0]["attribution_type"] = (
        "ACTIVE_RISK"
    )
    client.attribution_payload["results"]["YTD"]["attribution_sets"][0]["metric"] = "TRACKING_ERROR"
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_attribution(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        attribution_type="ACTIVE_RISK",
        grouping_dimension="ASSET_CLASS",
    )

    request = client.attribution_calls[0]["payload"]
    assert request["stateful_input"]["attribution_options"] == {
        "attribution_types": ["ACTIVE_RISK"],
        "metrics": ["TRACKING_ERROR"],
        "grouping_dimensions": ["ASSET_CLASS"],
        "annualization_basis": 252,
    }
    assert response.state == "ready"
    assert response.payload is not None
    assert response.payload.controls.attribution_types[1].state == "ready"
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "ready",
        "exposure_history": "ready",
        "benchmark_returns": "ready",
        "benchmark_exposure_context": "ready",
    }


@pytest.mark.asyncio
async def test_risk_attribution_blocks_active_risk_issuer_until_supported() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_attribution(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        reporting_currency="USD",
        attribution_type="ACTIVE_RISK",
        grouping_dimension="ISSUER",
    )

    assert client.attribution_calls == []
    assert response.state == "blocked"
    assert response.payload is not None
    assert response.payload.controls.selected_grouping_dimension == "ISSUER"
    issuer_grouping = {
        option.key: option for option in response.payload.controls.grouping_dimensions
    }["ISSUER"]
    assert issuer_grouping.state == "blocked"
    assert "benchmark issuer exposure semantics" in (issuer_grouping.reason or "")


@pytest.mark.asyncio
async def test_risk_attribution_blocks_active_risk_without_benchmark_context() -> None:
    client = _StubRiskClient()
    service = RiskWorkspaceService(client, cache_ttl_seconds=60)

    response = await service.get_attribution(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code=None,
        as_of_date="2026-04-04",
        reporting_currency="USD",
        attribution_type="ACTIVE_RISK",
        grouping_dimension="SECTOR",
    )

    assert client.attribution_calls == []
    assert response.state == "blocked"
    assert response.payload is not None
    active_risk = {option.key: option for option in response.payload.controls.attribution_types}[
        "ACTIVE_RISK"
    ]
    assert active_risk.state == "blocked"
    assert active_risk.reason == "Active risk requires benchmark context."
