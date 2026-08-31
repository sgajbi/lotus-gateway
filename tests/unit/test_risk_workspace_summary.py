from app.services.risk_workspace_summary import map_summary_response, unavailable_summary


def test_map_summary_response_maps_metrics_and_source_supportability() -> None:
    response = map_summary_response(
        correlation_id="corr-summary",
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="NET",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        upstream_payload=_summary_payload(),
    )

    assert response.state == "ready"
    assert response.detail_basis == "NET"
    assert response.payload is not None
    period = response.payload.periods[0]
    assert period.key == "YTD"
    assert period.metrics[0].label == "Volatility"
    assert period.metrics[0].value == 0.12
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "ready",
        "benchmark_returns": "ready",
        "risk_free_series": "ready",
        "source_calculation": "ready",
    }
    source_support = {item.key: item for item in response.supportability}["source_calculation"]
    assert source_support.reason == "Source calculation supportability was confirmed upstream."


def test_map_summary_response_reports_partial_metric_dependencies() -> None:
    payload = _summary_payload()
    payload["results"]["YTD"]["metrics"]["TRACKING_ERROR"] = {
        "value": None,
        "details": {"error": "benchmark returns unavailable"},
    }

    response = map_summary_response(
        correlation_id="corr-summary",
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="GROSS",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        upstream_payload=payload,
    )

    assert response.state == "partial"
    assert response.detail_basis == "GROSS"
    assert response.payload is not None
    tracking_error = [
        metric for metric in response.payload.periods[0].metrics if metric.key == "TRACKING_ERROR"
    ][0]
    assert tracking_error.state == "partial"
    assert tracking_error.reason == "benchmark returns unavailable"
    benchmark_support = {item.key: item for item in response.supportability}["benchmark_returns"]
    assert benchmark_support.state == "partial"


def test_map_summary_response_returns_empty_envelope_for_missing_periods() -> None:
    response = map_summary_response(
        correlation_id="corr-summary",
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="NET",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        upstream_payload={"results": {}},
    )

    assert response.state == "unavailable"
    assert response.payload is None
    assert response.warnings == ["RISK_SUMMARY_EMPTY"]
    assert response.partial_failures[0].error_code == "EMPTY_RISK_SUMMARY"
    assert {item.key: item.state for item in response.supportability} == {
        "portfolio_returns": "unavailable",
        "benchmark_returns": "partial",
        "risk_free_series": "partial",
    }


def test_unavailable_summary_preserves_product_safe_failure_detail() -> None:
    response = unavailable_summary(
        correlation_id="corr-summary",
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="GROSS",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        upstream_status=503,
        upstream_payload={"detail": "risk unavailable"},
    )

    assert response.state == "unavailable"
    assert response.detail_basis == "GROSS"
    assert response.payload is None
    assert response.warnings == ["RISK_SUMMARY_UNAVAILABLE"]
    assert response.supportability[0].key == "risk_service"
    assert response.partial_failures[0].error_code == "HTTP_503"
    assert response.partial_failures[0].source_service == "lotus-risk"
    assert response.partial_failures[0].detail == "risk request failed"


def _summary_payload() -> dict:
    return {
        "results": {
            "YTD": {
                "start_date": "2026-01-01",
                "end_date": "2026-04-04",
                "portfolio_observation_count": 66,
                "benchmark_observation_count": 66,
                "aligned_benchmark_observation_count": 64,
                "benchmark_context": {"reason": "APPLIED"},
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
        "metadata": {
            "calculation_supportability": {
                "state": "ready",
                "reason": "Source calculation supportability was confirmed upstream.",
                "freshness_bucket": "fresh",
                "source_service": "lotus-risk",
            }
        },
    }
