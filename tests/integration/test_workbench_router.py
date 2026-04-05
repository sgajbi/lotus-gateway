from fastapi.testclient import TestClient

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefResponse,
    AdvisorBriefSourceMetric,
    AdvisorBriefStatus,
    AdvisorBriefSupportabilityItem,
    AdvisorBriefTone,
)
from app.contracts.workbench import WorkbenchPortfolioSummary
from app.main import app
from app.middleware.server_timing import append_server_timing_metric

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


async def _analytics_reference(*args, **kwargs):
    return 200, {"performance_end_date": "2026-02-23"}


def test_workbench_router_success(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
            "client_id": "CIF_1001",
        }

    async def _pas(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 10,
                        "market_value_base": 750.0,
                        "weight": 0.75,
                    },
                    {
                        "security_id": "CASH_USD",
                        "quantity": 250.0,
                        "market_value_base": 250.0,
                        "weight": 0.25,
                    },
                ],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                    },
                    {
                        "security_id": "CASH_USD",
                        "instrument_name": "US Dollar Cash",
                        "asset_class": "Cash",
                    },
                ],
            },
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 2.5}}}}
            }
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "items": [
                {
                    "rebalance_run_id": "rr_100",
                    "status": "PENDING_REVIEW",
                    "created_at": "2026-02-23T01:00:00Z",
                }
            ]
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _pas)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_analytics_reference", _analytics_reference
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_twr_analytics", _pa
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert body["overview"]["position_count"] == 2
    assert body["performance_snapshot"]["period"] == "YTD"
    assert body["rebalance_snapshot"]["status"] == "PENDING_REVIEW"


def test_workbench_router_partial_failure(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD"}

    async def _pas(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 9,
                        "market_value_base": 900.0,
                        "weight": 0.9,
                    },
                    {
                        "security_id": "CASH_USD",
                        "quantity": 100.0,
                        "market_value_base": 100.0,
                        "weight": 0.1,
                    },
                ],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                    },
                    {
                        "security_id": "CASH_USD",
                        "instrument_name": "US Dollar Cash",
                        "asset_class": "Cash",
                    },
                ],
            },
        }

    async def _pa(*args, **kwargs):
        return 503, {"detail": "paused"}

    async def _dpm(*args, **kwargs):
        return 503, {"detail": "paused"}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _pas)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_analytics_reference", _analytics_reference
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_twr_analytics", _pa
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["performance_snapshot"] is None
    assert body["rebalance_snapshot"] is None
    assert len(body["partial_failures"]) == 2


def test_workbench_portfolio_360_router(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD"}

    async def _pas_core(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 10,
                        "market_value_base": 500.0,
                        "weight": 0.5,
                    }
                ],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [
                    {"security_id": "EQ_1", "instrument_name": "Equity 1", "asset_class": "Equity"}
                ],
            },
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.5}}}}
            }
        }

    async def _dpm_runs(*args, **kwargs):
        return 200, {"items": []}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _pas_core)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_analytics_reference", _analytics_reference
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_twr_analytics", _pa
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/portfolio-360")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert len(body["current_positions"]) == 1
    assert body["current_positions"][0]["market_value_base"] == 500.0


def test_workbench_analytics_router(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD"}

    async def _pas_core(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 10,
                        "market_value_base": 1000.0,
                        "weight": 1.0,
                    }
                ],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [
                    {"security_id": "EQ_1", "instrument_name": "Equity 1", "asset_class": "Equity"}
                ],
            },
        }

    async def _pas_positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "baseline_quantity": 10,
                    "proposed_quantity": 12,
                    "delta_quantity": 2,
                }
            ]
        }

    async def _pas_summary(*args, **kwargs):
        return 200, {
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 2.0,
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.5}}}}
            }
        }

    async def _pa_workbench(*args, **kwargs):
        return 200, {
            "portfolioId": "PF_1001",
            "period": "YTD",
            "groupBy": "ASSET_CLASS",
            "benchmarkCode": "MODEL_60_40",
            "portfolioReturnPct": 1.5,
            "benchmarkReturnPct": 3.1,
            "activeReturnPct": -1.6,
            "allocationBuckets": [
                {
                    "bucketKey": "EQUITY",
                    "bucketLabel": "EQUITY",
                    "currentQuantity": 10.0,
                    "proposedQuantity": 12.0,
                    "deltaQuantity": 2.0,
                    "currentWeightPct": 100.0,
                    "proposedWeightPct": 100.0,
                }
            ],
            "topChanges": [
                {
                    "securityId": "EQ_1",
                    "instrumentName": "Equity 1",
                    "deltaQuantity": 2.0,
                    "direction": "INCREASE",
                }
            ],
            "riskProxy": {"hhiCurrent": 10000.0, "hhiProposed": 10000.0, "hhiDelta": 0.0},
        }

    async def _dpm_runs(*args, **kwargs):
        return 200, {"items": []}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _pas_core)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_projected_positions", _pas_positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_projected_summary", _pas_summary)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_analytics_reference", _analytics_reference
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_twr_analytics", _pa
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_workbench_analytics",
        _pa_workbench,
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/analytics?group_by=ASSET_CLASS&benchmark_code=MODEL_60_40&session_id=sess_1"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert body["group_by"] == "ASSET_CLASS"
    assert len(body["allocation_buckets"]) >= 1
    assert "risk_proxy" in body


def test_workbench_performance_router(monkeypatch):
    async def _performance_workspace(*args, **kwargs):  # noqa: ARG001
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-02-24",
            "period": "YTD",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-02-24",
            "chart_frequency": "monthly",
            "contribution_dimension": "asset_class",
            "attribution_dimension": "asset_class",
            "detail_basis": "NET",
            "segment": "asset_class",
            "benchmark_code": "MODEL_60_40",
            "benchmark_options": [
                {
                    "benchmark_code": "MODEL_60_40",
                    "benchmark_name": "Model 60/40",
                    "benchmark_currency": "USD",
                    "benchmark_type": "composite",
                    "benchmark_family": "Balanced",
                    "benchmark_provider": "Lotus",
                    "is_assigned": True,
                }
            ],
            "capabilities": {
                "summary_kpis": {"state": "supported"},
                "return_path": {"state": "supported"},
                "benchmark_comparison": {"state": "supported"},
                "multi_horizon_returns": {"state": "supported"},
                "contribution_ranking": {"state": "supported"},
                "attribution_detail": {"state": "supported"},
                "contribution_detail": {"state": "supported"},
                "evidence": {"state": "unavailable"},
            },
            "portfolio": {
                "portfolio_id": "PF_1001",
                "client_id": "CIF_1001",
                "base_currency": "USD",
                "booking_center_code": "SG",
            },
            "overview": {
                "market_value_base": 1250000.0,
                "cash_weight_pct": 6.8,
                "position_count": 18,
            },
            "net_performance": {
                "metric_basis": "NET",
                "portfolio_return_pct": 5.42,
                "benchmark_return_pct": 4.9,
                "active_return_pct": 0.52,
                "annualized_return_pct": 5.42,
                "benchmark_id": "MODEL_60_40",
                "benchmark_return_source": "calculated",
            },
            "gross_performance": {
                "metric_basis": "GROSS",
                "portfolio_return_pct": 5.88,
                "benchmark_return_pct": 4.9,
                "active_return_pct": 0.98,
                "annualized_return_pct": 5.88,
                "benchmark_id": "MODEL_60_40",
                "benchmark_return_source": "calculated",
            },
            "money_weighted_return": {
                "money_weighted_return_pct": 5.12,
                "annualized_return_pct": 5.12,
                "method": "XIRR",
                "start_date": "2026-01-01",
                "end_date": "2026-02-24",
                "notes": ["cash-flow aware"],
            },
            "net_chart": [
                {
                    "label": "2026-01",
                    "frequency": "monthly",
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "portfolio_return_pct": 2.2,
                    "benchmark_return_pct": 1.9,
                    "active_return_pct": 0.3,
                    "cumulative_portfolio_return_pct": 2.2,
                    "cumulative_benchmark_return_pct": 1.9,
                    "cumulative_active_return_pct": 0.3,
                }
            ],
            "gross_chart": [],
            "contribution": {
                "metric_basis": "NET",
                "weighting_scheme": "average_weight",
                "portfolio_contribution_pct": 5.42,
                "total_portfolio_return_pct": 5.42,
                "coverage_mv_pct": 98.7,
                "levels": [],
            },
            "attribution": {
                "metric_basis": "NET",
                "model": "BF",
                "linking": "carino",
                "benchmark_id": "MODEL_60_40",
                "active_return_pct": 0.52,
                "sum_of_effects_pct": 0.5,
                "residual_pct": 0.02,
                "levels": [],
            },
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_workspace",
        _performance_workspace,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance"
        "?period=YTD&chart_frequency=monthly&contribution_dimension=asset_class"
        "&attribution_dimension=asset_class&detail_basis=NET&benchmark_code=MODEL_60_40"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert body["net_performance"]["portfolio_return_pct"] == 5.42
    assert body["gross_performance"]["portfolio_return_pct"] == 5.88
    assert body["money_weighted_return"]["method"] == "XIRR"
    assert body["contribution"]["coverage_mv_pct"] == 98.7
    assert body["attribution"]["model"] == "BF"


def test_workbench_performance_summary_router(monkeypatch):
    async def _performance_summary(*args, **kwargs):  # noqa: ARG001
        append_server_timing_metric("perf-reference", 1.0)
        append_server_timing_metric("perf-benchmark", 2.0)
        append_server_timing_metric("perf-summary", 3.0)
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-02-24",
            "period": "YTD",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-02-24",
            "chart_frequency": "monthly",
            "detail_basis": "NET",
            "benchmark_code": "MODEL_60_40",
            "benchmark_options": [
                {
                    "benchmark_code": "MODEL_60_40",
                    "benchmark_name": "Model 60/40",
                    "is_assigned": True,
                }
            ],
            "capabilities": {
                "summary_kpis": {"state": "supported"},
                "return_path": {"state": "supported"},
                "benchmark_comparison": {"state": "supported"},
                "multi_horizon_returns": {"state": "supported"},
                "contribution_ranking": {"state": "supported"},
                "attribution_detail": {"state": "supported"},
                "contribution_detail": {"state": "supported"},
                "evidence": {"state": "unavailable"},
            },
            "portfolio": {
                "portfolio_id": "PF_1001",
                "client_id": "CIF_1001",
                "base_currency": "USD",
                "booking_center_code": "SG",
            },
            "overview": {
                "market_value_base": 1250000.0,
                "cash_weight_pct": 6.8,
                "position_count": 18,
            },
            "net_performance": {
                "metric_basis": "NET",
                "portfolio_return_pct": 5.42,
                "benchmark_return_pct": 4.9,
                "active_return_pct": 0.52,
                "annualized_return_pct": 5.42,
                "benchmark_input_mode": "stateful",
            },
            "gross_performance": {
                "metric_basis": "GROSS",
                "portfolio_return_pct": 5.88,
                "benchmark_return_pct": 4.9,
                "active_return_pct": 0.98,
                "annualized_return_pct": 5.88,
                "benchmark_input_mode": "stateful",
            },
            "money_weighted_return": {
                "money_weighted_return_pct": 5.12,
                "annualized_return_pct": 5.12,
                "input_mode": "stateful",
                "method": "XIRR",
                "start_date": "2026-01-01",
                "end_date": "2026-02-24",
                "begin_market_value": 1200000.0,
                "end_market_value": 1250000.0,
                "beginning_cash_flow": 50000.0,
                "ending_cash_flow": -8000.0,
                "flow_adjusted_end_market_value": 1208000.0,
                "net_cash_flow": 42000.0,
                "fees": 0.0,
                "notes": [],
            },
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_workspace_summary",
        _performance_summary,
    )

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/performance/summary?period=YTD")

    assert response.status_code == 200
    assert response.headers["Server-Timing"].startswith("app;dur=")
    assert "perf-summary;dur=" in response.headers["Server-Timing"]
    assert "perf-benchmark;dur=" in response.headers["Server-Timing"]
    assert "perf-reference;dur=" in response.headers["Server-Timing"]
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert body["net_performance"]["portfolio_return_pct"] == 5.42
    assert body["net_performance"]["benchmark_input_mode"] == "stateful"
    assert body["money_weighted_return"]["input_mode"] == "stateful"
    assert body["money_weighted_return"]["begin_market_value"] == 1200000.0
    assert body["money_weighted_return"]["flow_adjusted_end_market_value"] == 1208000.0
    assert body["money_weighted_return"]["net_cash_flow"] == 42000.0
    assert "net_chart" not in body
    assert "contribution" not in body


def test_workbench_performance_details_router(monkeypatch):
    async def _performance_details(*args, **kwargs):  # noqa: ARG001
        append_server_timing_metric("perf-reference", 1.0)
        append_server_timing_metric("perf-benchmark", 2.0)
        append_server_timing_metric("perf-summary", 3.0)
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-02-24",
            "period": "YTD",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-02-24",
            "chart_frequency": "monthly",
            "contribution_dimension": "asset_class",
            "attribution_dimension": "asset_class",
            "detail_basis": "NET",
            "segment": "asset_class",
            "benchmark_code": "MODEL_60_40",
            "capabilities": {
                "summary_kpis": {"state": "supported"},
                "return_path": {"state": "supported"},
                "benchmark_comparison": {"state": "supported"},
                "multi_horizon_returns": {"state": "supported"},
                "contribution_ranking": {"state": "supported"},
                "attribution_detail": {"state": "supported"},
                "contribution_detail": {"state": "supported"},
                "evidence": {"state": "unavailable"},
            },
            "net_chart": [
                {
                    "label": "2026-01",
                    "frequency": "monthly",
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "portfolio_return_pct": 2.2,
                    "benchmark_return_pct": 1.9,
                    "active_return_pct": 0.3,
                    "cumulative_portfolio_return_pct": 2.2,
                    "cumulative_benchmark_return_pct": 1.9,
                    "cumulative_active_return_pct": 0.3,
                }
            ],
            "gross_chart": [],
            "contribution": {
                "metric_basis": "NET",
                "weighting_scheme": "average_weight",
                "portfolio_contribution_pct": 5.42,
                "total_portfolio_return_pct": 5.42,
                "coverage_mv_pct": 98.7,
                "levels": [],
            },
            "attribution": {
                "metric_basis": "NET",
                "model": "BF",
                "linking": "carino",
                "benchmark_id": "MODEL_60_40",
                "active_return_pct": 0.52,
                "sum_of_effects_pct": 0.5,
                "residual_pct": 0.02,
                "levels": [],
            },
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_workspace_details",
        _performance_details,
    )

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/performance/details?period=YTD")

    assert response.status_code == 200
    assert response.headers["Server-Timing"].startswith("app;dur=")
    assert "perf-summary;dur=" in response.headers["Server-Timing"]
    assert "perf-benchmark;dur=" in response.headers["Server-Timing"]
    assert "perf-reference;dur=" in response.headers["Server-Timing"]
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert body["net_chart"][0]["label"] == "2026-01"
    assert body["contribution"]["coverage_mv_pct"] == 98.7
    assert "overview" not in body
    assert "net_performance" not in body


def test_workbench_performance_horizon_comparison_router(monkeypatch):
    async def _performance_horizon_comparison(*args, **kwargs):  # noqa: ARG001
        assert kwargs["period"] == "EXPLICIT"
        assert kwargs["explicit_start_date"] == "2026-01-01"
        assert kwargs["explicit_end_date"] == "2026-02-24"
        append_server_timing_metric("perf-reference", 1.0)
        append_server_timing_metric("perf-benchmark", 2.0)
        append_server_timing_metric("perf-horizon", 3.0)
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-02-24",
            "period": "EXPLICIT",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-02-24",
            "detail_basis": "NET",
            "chart_frequency": "monthly",
            "requested_chart_frequency_supported": True,
            "benchmark_code": "MODEL_60_40",
            "benchmark_options": [
                {
                    "benchmark_code": "MODEL_60_40",
                    "benchmark_name": "Model 60/40",
                    "is_assigned": True,
                }
            ],
            "rows": [
                {
                    "period": "MTD",
                    "portfolio_return_pct": 1.2,
                    "benchmark_return_pct": 1.0,
                    "active_return_pct": 0.2,
                    "annualized_return_pct": 1.2,
                },
                {
                    "period": "YTD",
                    "portfolio_return_pct": 5.4,
                    "benchmark_return_pct": 4.9,
                    "active_return_pct": 0.5,
                    "annualized_return_pct": 5.4,
                },
            ],
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_horizon_comparison",
        _performance_horizon_comparison,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/horizon-comparison"
        "?period=EXPLICIT&detail_basis=NET&benchmark_code=MODEL_60_40"
        "&report_start_date=2026-01-01&report_end_date=2026-02-24"
    )

    assert response.status_code == 200
    assert "perf-horizon;dur=" in response.headers["Server-Timing"]
    assert "perf-benchmark;dur=" in response.headers["Server-Timing"]
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert body["period"] == "EXPLICIT"
    assert body["report_start_date"] == "2026-01-01"
    assert body["report_end_date"] == "2026-02-24"
    assert body["chart_frequency"] == "monthly"
    assert body["requested_chart_frequency_supported"] is True
    assert body["rows"][0]["period"] == "MTD"
    assert body["rows"][1]["benchmark_return_pct"] == 4.9


def test_workbench_performance_attribution_trend_router(monkeypatch):
    async def _performance_attribution_trend(*args, **kwargs):  # noqa: ARG001
        append_server_timing_metric("perf-reference", 1.0)
        append_server_timing_metric("perf-benchmark", 2.0)
        append_server_timing_metric("perf-attribution", 3.0)
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-02-24",
            "period": "YTD",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-02-24",
            "chart_frequency": "monthly",
            "detail_basis": "NET",
            "attribution_dimension": "asset_class",
            "requested_chart_frequency_supported": True,
            "requested_attribution_dimension_supported": True,
            "benchmark_code": "MODEL_60_40",
            "rows": [
                {
                    "period_label": "2026-01",
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "frequency": "monthly",
                    "allocation_pct": 0.12,
                    "selection_pct": 0.08,
                    "interaction_pct": 0.02,
                    "total_effect_pct": 0.22,
                    "cumulative_total_effect_pct": 0.22,
                    "active_return_pct": 0.22,
                    "residual_pct": 0.0,
                }
            ],
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_attribution_trend",
        _performance_attribution_trend,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/attribution-trend"
        "?period=YTD&chart_frequency=monthly&attribution_dimension=asset_class"
        "&detail_basis=NET&benchmark_code=MODEL_60_40"
    )

    assert response.status_code == 200
    assert "perf-attribution;dur=" in response.headers["Server-Timing"]
    assert "perf-benchmark;dur=" in response.headers["Server-Timing"]
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert body["chart_frequency"] == "monthly"
    assert body["requested_chart_frequency_supported"] is True
    assert body["requested_attribution_dimension_supported"] is True
    assert body["rows"][0]["period_label"] == "2026-01"
    assert body["rows"][0]["cumulative_total_effect_pct"] == 0.22


def test_workbench_performance_monolithic_route_is_marked_deprecated_in_openapi():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    performance_get = schema["paths"]["/api/v1/workbench/{portfolio_id}/performance"]["get"]
    assert performance_get["deprecated"] is True
    assert (
        "Compatibility endpoint for the legacy monolithic performance workspace contract"
        in (performance_get["description"])
    )


def test_workbench_performance_advisor_brief_router(monkeypatch):
    captured_call = {}

    async def _brief(*args, **kwargs):
        captured_call.update(kwargs)
        append_server_timing_metric("perf-advisor-brief-source", 4.0)
        append_server_timing_metric("perf-advisor-brief-ai", 5.0)
        return AdvisorBriefResponse(
            correlation_id=kwargs["correlation_id"],
            contract_version="v1",
            portfolio_id="PF_1001",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id="PF_1001",
                client_id="CIF_1001",
                base_currency="USD",
                booking_center_code="SG",
            ),
            as_of_date="2026-04-04",
            period="YTD",
            report_start_date="2026-01-01",
            report_end_date="2026-04-04",
            detail_basis="NET",
            chart_frequency="monthly",
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            benchmark_code="BMK_GLOBAL_BALANCED_60_40",
            status=AdvisorBriefStatus.READY,
            summary="Advisor summary.",
            talking_points=[
                AdvisorBriefNarrativeItem(
                    headline="Portfolio return is 1.25% versus benchmark 7.93%.",
                    detail="Active return is -6.68% for the selected YTD period.",
                    tone=AdvisorBriefTone.WARNING,
                    evidence_refs=[
                        AdvisorBriefEvidenceRef(
                            metric_label="Active Return",
                            metric_value="-6.68%",
                            source_surface="performance.return_path",
                            target_mode="summary",
                            route=(
                                "/performance?portfolioId=PF_1001&period=YTD"
                                "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                            ),
                        )
                    ],
                )
            ],
            recommended_actions=[
                AdvisorBriefActionItem(
                    label="Open Return Path",
                    target_mode="summary",
                    route=(
                        "/performance?portfolioId=PF_1001&period=YTD"
                        "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                    ),
                )
            ],
            risks_and_exceptions=[],
            source_metrics=[
                AdvisorBriefSourceMetric(
                    label="Active Return",
                    value="-6.68%",
                    support_label="YTD NET",
                    target_mode="summary",
                    route=(
                        "/performance?portfolioId=PF_1001&period=YTD"
                        "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                    ),
                )
            ],
            supportability=[
                AdvisorBriefSupportabilityItem(
                    label="Advisor Brief",
                    value="Ready",
                    tone="success",
                )
            ],
            ai_audit={
                "request_id": "req-1",
                "provider_mode": "local_openai_compatible",
                "provider_id": "text.local",
                "adapter_kind": "OPENAI_COMPATIBLE_LOCAL",
                "model_id": "qwen3:8b",
                "stubbed": False,
            },
            ai_evidence={"descriptors": []},
        )

    monkeypatch.setattr(
        "app.services.advisor_brief_service.AdvisorBriefService.get_performance_advisor_brief",
        _brief,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/advisor-brief"
        "?period=YTD&chart_frequency=monthly&detail_basis=NET"
        "&contribution_dimension=asset_class&attribution_dimension=asset_class"
        "&benchmark_code=BMK_GLOBAL_BALANCED_60_40&report_start_date=2026-01-01"
        "&report_end_date=2026-04-04"
    )

    assert response.status_code == 200
    assert response.headers["Server-Timing"].startswith("app;dur=")
    assert "perf-advisor-brief-source;dur=" in response.headers["Server-Timing"]
    assert "perf-advisor-brief-ai;dur=" in response.headers["Server-Timing"]
    body = response.json()
    assert body["status"] == "ready"
    assert body["summary"] == "Advisor summary."
    assert body["talking_points"][0]["evidence_refs"][0]["target_mode"] == "summary"
    assert body["source_metrics"][0]["label"] == "Active Return"
    assert body["supportability"][0]["value"] == "Ready"
    assert body["ai_audit"]["request_id"] == "req-1"
    assert body["ai_audit"]["provider_mode"] == "local_openai_compatible"
    assert body["ai_audit"]["provider_id"] == "text.local"
    assert body["ai_audit"]["adapter_kind"] == "OPENAI_COMPATIBLE_LOCAL"
    assert body["ai_audit"]["model_id"] == "qwen3:8b"
    assert body["ai_audit"]["stubbed"] is False
    assert body["ai_evidence"] == {"descriptors": []}
    assert captured_call["portfolio_id"] == "PF_1001"
    assert captured_call["period"] == "YTD"
    assert captured_call["detail_basis"] == "NET"
    assert captured_call["benchmark_code"] == "BMK_GLOBAL_BALANCED_60_40"
    assert captured_call["explicit_start_date"] == "2026-01-01"
    assert captured_call["explicit_end_date"] == "2026-04-04"


def test_workbench_sandbox_changes_router(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD"}

    async def _pas_core(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [],
            },
        }

    async def _pas_create(*args, **kwargs):
        return 201, {"session": {"session_id": "sess_1", "version": 1}}

    async def _pas_add(*args, **kwargs):
        return 200, {"session_id": "sess_1", "version": 2}

    async def _pas_positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "baseline_quantity": 10,
                    "proposed_quantity": 12,
                    "delta_quantity": 2,
                }
            ]
        }

    async def _pas_summary(*args, **kwargs):
        return 200, {
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 2.0,
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.5}}}}
            }
        }

    async def _dpm_runs(*args, **kwargs):
        return 200, {"items": []}

    async def _dpm_simulate(*args, **kwargs):
        return 200, {"status": "COMPLETED", "gate_decision": {"status": "PASS"}}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _pas_core)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.create_simulation_session", _pas_create)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.add_simulation_changes", _pas_add)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_projected_positions", _pas_positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_projected_summary", _pas_summary)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_analytics_reference", _analytics_reference
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_twr_analytics", _pa
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.simulate_proposal", _dpm_simulate)

    client = TestClient(app)
    created = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions", json={"created_by": "advisor_1"}
    )
    assert created.status_code == 200
    assert created.json()["session_id"] == "sess_1"

    updated = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions/sess_1/changes",
        json={
            "changes": [{"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 2}],
            "evaluate_policy": True,
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["session_id"] == "sess_1"
    assert body["session_version"] == 2
    assert body["policy_feedback"]["status"] == "PASS"
