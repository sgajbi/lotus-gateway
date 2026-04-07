import pytest

from app.services.risk_workspace_service import RiskWorkspaceService


class _StubRiskClient:
    def __init__(self) -> None:
        self.calculate_calls: list[dict] = []
        self.concentration_calls: list[dict] = []
        self.calculate_status = 200
        self.concentration_status = 200
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
                "note": "Two positions have no issuer enrichment.",
            },
            "valuation_context": {"reporting_currency": "USD"},
            "metadata": {"as_of_date": "2026-04-04", "portfolio_id": "PF_1"},
        }

    async def post_risk_calculate(self, payload: dict, correlation_id: str):
        self.calculate_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.calculate_status, self.calculate_payload

    async def post_risk_concentration(self, payload: dict, correlation_id: str):
        self.concentration_calls.append({"payload": payload, "correlation_id": correlation_id})
        return self.concentration_status, self.concentration_payload


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
        metric
        for metric in response.payload.periods[0].metrics
        if metric.key == "TRACKING_ERROR"
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
    assert response.payload.risk_proxy.hhi_current == 1200.0
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_positions": "ready",
        "issuer_enrichment": "partial",
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
