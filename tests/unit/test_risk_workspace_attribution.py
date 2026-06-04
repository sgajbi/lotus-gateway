from app.services.risk_workspace_attribution import (
    blocked_attribution_response,
    map_attribution_response,
    unavailable_attribution,
)


def test_map_attribution_response_preserves_upstream_methodology_and_period_errors() -> None:
    response = map_attribution_response(
        correlation_id="corr-1",
        portfolio_id="PF_1",
        period="YTD",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        attribution_type="TOTAL_RISK",
        grouping_dimension="SECTOR",
        upstream_payload={
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-04-04",
                    "attribution_sets": [
                        {
                            "metric": "VOLATILITY",
                            "total_value": "0.12",
                            "reconciled_sum": 0.119,
                            "residual": "not-a-number",
                            "contributors": [
                                {
                                    "group_key": "SECTOR_TECH",
                                    "group_label": "Technology",
                                    "weight_average": 0.42,
                                    "marginal_contribution": 0.05,
                                    "component_contribution": 0.044,
                                    "percent_contribution": 0.36,
                                }
                            ],
                        }
                    ],
                    "error": "issuer enrichment partial",
                }
            },
            "metadata": {"methodology_version": "historical_attribution.v1"},
        },
    )

    assert response.state == "ready"
    assert response.metadata.methodology_version == "historical_attribution.v1"
    assert response.payload is not None
    attribution_set = response.payload.periods[0].attribution_sets[0]
    assert attribution_set.total_value == 0.12
    assert attribution_set.reconciled_sum == 0.119
    assert attribution_set.residual is None
    assert response.partial_failures[0].error_code == "RISK_ATTRIBUTION_PERIOD_ERROR"
    assert response.warnings == ["RISK_ATTRIBUTION_PERIOD_PARTIAL"]


def test_map_attribution_response_returns_unavailable_when_periods_are_missing() -> None:
    response = map_attribution_response(
        correlation_id="corr-1",
        portfolio_id="PF_1",
        period="YTD",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        attribution_type="TOTAL_RISK",
        grouping_dimension="SECTOR",
        upstream_payload={"results": {}, "metadata": {}},
    )

    assert response.state == "unavailable"
    assert response.payload is None
    assert response.partial_failures[0].error_code == "EMPTY_RISK_ATTRIBUTION"
    assert response.warnings == ["RISK_ATTRIBUTION_EMPTY"]


def test_blocked_attribution_response_bypasses_active_risk_without_benchmark() -> None:
    response = blocked_attribution_response(
        correlation_id="corr-1",
        portfolio_id="PF_1",
        period="YTD",
        as_of_date="2026-04-04",
        benchmark_code=None,
        attribution_type="ACTIVE_RISK",
        grouping_dimension="SECTOR",
    )

    assert response is not None
    assert response.state == "blocked"
    assert response.metadata.cache_status == "bypass"
    assert response.warnings == ["RISK_ATTRIBUTION_BLOCKED"]


def test_unavailable_attribution_preserves_product_safe_upstream_failure() -> None:
    response = unavailable_attribution(
        correlation_id="corr-1",
        portfolio_id="PF_1",
        period="YTD",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        attribution_type="TOTAL_RISK",
        grouping_dimension="SECTOR",
        upstream_status=503,
        upstream_payload={"detail": "risk attribution unavailable", "debug": "hidden"},
    )

    assert response.state == "unavailable"
    assert response.payload is not None
    assert response.partial_failures[0].error_code == "HTTP_503"
    assert response.partial_failures[0].detail == "risk attribution unavailable"
