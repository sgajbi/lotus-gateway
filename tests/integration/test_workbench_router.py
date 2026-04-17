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
    assert body["portfolio"]["client_id"] == "CIF_1001"
    assert body["portfolio"]["booking_center_code"] == "SG"
    assert body["overview"]["market_value_base"] == 1000.0
    assert body["overview"]["cash_weight_pct"] == 25.0
    assert body["overview"]["position_count"] == 2
    assert body["performance_snapshot"]["period"] == "YTD"
    assert body["performance_snapshot"]["return_pct"] == 2.5
    assert body["rebalance_snapshot"]["status"] == "PENDING_REVIEW"
    assert body["rebalance_snapshot"]["last_rebalance_run_id"] == "rr_100"
    assert body["rebalance_snapshot"]["last_run_at_utc"] == "2026-02-23T01:00:00Z"
    assert body["warnings"] == []
    assert body["partial_failures"] == []


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
    assert body["warnings"] == [
        "PERFORMANCE_SNAPSHOT_UNAVAILABLE",
        "MANAGE_REBALANCE_UNAVAILABLE",
    ]
    assert body["partial_failures"][0]["source_service"] == "lotus-performance"
    assert body["partial_failures"][1]["source_service"] == "lotus-manage"


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
    assert body["as_of_date"] == "2026-02-23"
    assert body["overview"]["market_value_base"] == 1000.0
    assert body["performance_snapshot"]["return_pct"] == 1.5
    assert body["rebalance_snapshot"]["status"] == "NOT_AVAILABLE"
    assert len(body["current_positions"]) == 1
    assert body["current_positions"][0]["security_id"] == "EQ_1"
    assert body["current_positions"][0]["instrument_name"] == "Equity 1"
    assert body["current_positions"][0]["asset_class"] == "Equity"
    assert body["current_positions"][0]["market_value_base"] == 500.0
    assert body["current_positions"][0]["weight_pct"] == 50.0
    assert body["projected_positions"] == []
    assert body["projected_summary"] is None
    assert body["warnings"] == []
    assert body["partial_failures"] == []


def test_workbench_portfolio_360_router_preserves_session_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(self, portfolio_id: str, correlation_id: str, session_id: str | None):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["session_id"] = session_id
        return {
            "correlation_id": correlation_id,
            "contract_version": "v1",
            "as_of_date": "2026-02-23",
            "portfolio": {
                "portfolio_id": portfolio_id,
                "client_id": "CIF_1001",
                "base_currency": "USD",
                "booking_center_code": "SG",
            },
            "overview": {
                "market_value_base": 1000.0,
                "cash_weight_pct": 25.0,
                "position_count": 1,
            },
            "current_positions": [],
            "projected_positions": [],
            "projected_summary": None,
            "active_session_id": session_id,
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.workbench_service.WorkbenchService.get_portfolio_360",
        _service,
    )

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/portfolio-360?session_id=sess_1")

    assert response.status_code == 200
    body = response.json()
    assert captured["portfolio_id"] == "PF_1001"
    assert captured["session_id"] == "sess_1"
    assert captured["correlation_id"]
    assert body["active_session_id"] == "sess_1"


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
    assert body["session_id"] == "sess_1"
    assert body["period"] == "YTD"
    assert body["group_by"] == "ASSET_CLASS"
    assert body["benchmark_code"] == "MODEL_60_40"
    assert body["portfolio_return_pct"] == 1.5
    assert body["benchmark_return_pct"] == 3.1
    assert body["active_return_pct"] == -1.6
    assert len(body["allocation_buckets"]) >= 1
    assert body["allocation_buckets"][0]["bucket_key"] == "EQUITY"
    assert body["allocation_buckets"][0]["delta_quantity"] == 2.0
    assert body["top_changes"][0]["security_id"] == "EQ_1"
    assert body["top_changes"][0]["direction"] == "INCREASE"
    assert "RISK_BFF_PENDING" in body["warnings"]
    assert any(
        failure["error_code"] == "RISK_BFF_NOT_IMPLEMENTED" for failure in body["partial_failures"]
    )
    assert "risk_proxy" not in body


def test_workbench_analytics_router_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        group_by: str,
        benchmark_code: str,
        session_id: str | None,
    ):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["period"] = period
        captured["group_by"] = group_by
        captured["benchmark_code"] = benchmark_code
        captured["session_id"] = session_id
        return {
            "correlation_id": correlation_id,
            "contract_version": "v1",
            "portfolio_id": portfolio_id,
            "session_id": session_id,
            "period": period,
            "group_by": group_by,
            "benchmark_code": benchmark_code,
            "portfolio_return_pct": 1.5,
            "benchmark_return_pct": 3.1,
            "active_return_pct": -1.6,
            "allocation_buckets": [],
            "top_changes": [],
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.workbench_service.WorkbenchService.get_workbench_analytics",
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/analytics?period=QTD&group_by=SECTOR"
        "&benchmark_code=MODEL_70_30&session_id=sess_2"
    )

    assert response.status_code == 200
    body = response.json()
    assert captured == {
        "portfolio_id": "PF_1001",
        "correlation_id": body["correlation_id"],
        "period": "QTD",
        "group_by": "SECTOR",
        "benchmark_code": "MODEL_70_30",
        "session_id": "sess_2",
    }
    assert body["period"] == "QTD"
    assert body["group_by"] == "SECTOR"
    assert body["benchmark_code"] == "MODEL_70_30"


def test_workbench_risk_summary_router_uses_stateful_gateway_contract(monkeypatch):
    async def _risk_calculate(self, payload, correlation_id):  # noqa: ARG001
        assert payload["input_mode"] == "stateful"
        assert "stateless_input" not in payload
        assert payload["stateful_input"]["portfolio_id"] == "PF_RISK_SUMMARY"
        return 200, {
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
                        "SHARPE": {"value": 1.2},
                        "SORTINO": {"value": 1.4},
                        "BETA": {"value": 0.9},
                        "TRACKING_ERROR": {"value": 0.03},
                        "INFORMATION_RATIO": {"value": 0.4},
                        "VAR": {"value": -0.02},
                    },
                }
            },
        }

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_risk_calculate",
        _risk_calculate,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_RISK_SUMMARY/risk/summary"
        "?period=YTD&detail_basis=NET&benchmark_code=BMK_1"
        "&as_of_date=2026-04-04&reporting_currency=USD",
        headers={"X-Correlation-Id": "corr-risk-summary"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "risk-workspace.v1"
    assert body["correlation_id"] == "corr-risk-summary"
    assert body["source_service"] == "lotus-risk"
    assert body["state"] == "ready"
    assert body["metadata"]["input_mode"] == "stateful"
    assert body["payload"]["periods"][0]["metrics"][0]["label"] == "Volatility"


def test_workbench_risk_concentration_router_maps_stateful_concentration(monkeypatch):
    async def _risk_concentration(self, payload, correlation_id):  # noqa: ARG001
        assert payload["input_mode"] == "stateful"
        assert payload["stateful_input"]["portfolio_id"] == "PF_RISK_CONC"
        assert payload["issuer_grouping_level"] == "ultimate_parent"
        return 200, {
            "source_service": "lotus-risk",
            "input_mode": "stateful",
            "risk_proxy": {"hhi_current": 1200.0, "hhi_proposed": 1225.0, "hhi_delta": 25.0},
            "single_position_concentration": {
                "top_position_weight_current": 0.2,
                "top_position_weight_proposed": 0.21,
                "top_position_weight_delta": 0.01,
                "top_n_cumulative_weight_current": 0.5,
                "top_n_cumulative_weight_proposed": 0.52,
                "top_n_cumulative_weight_delta": 0.02,
                "top_n": 10,
                "top_position_current": {
                    "security_id": "FO_FUND_PIMCO_INC",
                    "security_name": "PIMCO GIS Income Fund",
                    "weight": 0.2,
                },
                "top_position_proposed": {
                    "security_id": "FO_FUND_PIMCO_INC",
                    "security_name": "PIMCO GIS Income Fund",
                    "weight": 0.21,
                },
            },
            "issuer_concentration": {
                "hhi_current": 1500.0,
                "hhi_proposed": 1600.0,
                "hhi_delta": 100.0,
                "top_issuer_weight_current": 0.25,
                "top_issuer_weight_proposed": 0.27,
                "top_issuer_weight_delta": 0.02,
                "coverage_status": "complete",
                "covered_position_count_current": 10,
                "covered_position_count_proposed": 10,
                "total_position_count_current": 10,
                "total_position_count_proposed": 10,
                "uncovered_position_count_current": 0,
                "uncovered_position_count_proposed": 0,
                "coverage_ratio_current": 1.0,
                "coverage_ratio_proposed": 1.0,
                "note": None,
                "top_issuer_current": {
                    "issuer_id": "ULTIMATE_PIMCO",
                    "issuer_name": "Pacific Investment Management Company LLC",
                    "weight": 0.25,
                },
                "top_issuer_proposed": {
                    "issuer_id": "ULTIMATE_PIMCO",
                    "issuer_name": "Pacific Investment Management Company LLC",
                    "weight": 0.27,
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
                "portfolio_id": "PF_RISK_CONC",
                "issuer_grouping_level": "ultimate_parent",
                "enrichment_policy": "merge_caller_then_core",
                "include_cash_positions": True,
                "include_zero_quantity_positions": False,
            },
        }

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_risk_concentration",
        _risk_concentration,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_RISK_CONC/risk/concentration"
        "?period=YTD&benchmark_code=BMK_1&as_of_date=2026-04-04&reporting_currency=USD",
        headers={"X-Correlation-Id": "corr-risk-concentration"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "risk-workspace.v1"
    assert body["state"] == "ready"
    assert body["payload"]["portfolio_concentration"]["hhi_current"] == 1200.0
    assert (
        body["payload"]["single_position_concentration"]["top_position_current"]["security_name"]
        == "PIMCO GIS Income Fund"
    )
    assert body["payload"]["execution_context"]["issuer_grouping_level"] == "ultimate_parent"
    assert {item["key"]: item["state"] for item in body["supportability"]} == {
        "portfolio_positions": "ready",
        "issuer_enrichment": "ready",
        "issuer_grouping": "ready",
        "valuation_basis": "ready",
    }


def test_workbench_risk_drawdown_router_maps_stateful_drawdown_and_detail_flag(monkeypatch):
    async def _risk_drawdown(self, payload, correlation_id):  # noqa: ARG001
        assert payload["input_mode"] == "stateful"
        assert payload["stateful_input"]["portfolio_id"] == "PF_RISK_DRAWDOWN"
        assert payload["stateful_input"]["benchmark_policy"] == {
            "include_benchmark": True,
            "missing_benchmark_policy": "IGNORE",
        }
        assert payload["analysis_options"]["include_underwater_series"] is True
        return 200, {
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
                            "episode_id": "dd_0001",
                            "peak_date": "2026-01-12",
                            "trough_date": "2026-02-03",
                            "recovery_date": None,
                            "depth": -0.124533,
                            "days_to_trough": 16,
                            "days_to_recovery": None,
                            "total_days": 34,
                            "is_recovered": False,
                        }
                    ],
                    "relative_to_benchmark": {
                        "max_drawdown": -0.0821,
                        "max_drawdown_peak_date": "2026-01-11",
                        "max_drawdown_trough_date": "2026-02-01",
                    },
                    "underwater_series": [
                        {"date": "2026-01-20", "drawdown": -0.0521},
                        {"date": "2026-01-21", "drawdown": -0.061},
                    ],
                    "error": None,
                }
            },
            "metadata": {"contract_version": "v1", "methodology_version": "drawdown.v1"},
        }

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_risk_drawdown",
        _risk_drawdown,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_RISK_DRAWDOWN/risk/drawdown"
        "?period=YTD&detail_basis=NET&benchmark_code=BMK_1"
        "&as_of_date=2026-04-04&reporting_currency=USD&include_underwater_series=true",
        headers={"X-Correlation-Id": "corr-risk-drawdown"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "risk-workspace.v1"
    assert body["correlation_id"] == "corr-risk-drawdown"
    assert body["state"] == "ready"
    assert body["metadata"]["methodology_version"] == "drawdown.v1"
    assert body["payload"]["periods"][0]["summary"]["max_drawdown"] == -0.124533
    assert body["payload"]["periods"][0]["episodes"][0]["episode_id"] == "dd_0001"
    assert len(body["payload"]["periods"][0]["underwater_series"]) == 2
    assert {item["key"]: item["state"] for item in body["supportability"]} == {
        "portfolio_returns": "ready",
        "benchmark_relative_drawdown": "ready",
        "underwater_series": "ready",
    }


def test_workbench_risk_rolling_router_maps_stateful_rolling_and_detail_flag(monkeypatch):
    async def _risk_rolling(self, payload, correlation_id):  # noqa: ARG001
        assert payload["input_mode"] == "stateful"
        assert payload["stateful_input"]["portfolio_id"] == "PF_RISK_ROLLING"
        assert payload["stateful_input"]["rolling_options"]["include_time_series"] is True
        assert payload["stateful_input"]["rolling_options"]["window_lengths"] == [21, 63, 126, 252]
        return 200, {
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
                            },
                            "metric_series": [
                                {
                                    "date": "2026-04-01",
                                    "metric_values": {
                                        "ROLLING_VOLATILITY": 0.131,
                                    },
                                }
                            ],
                        }
                    ],
                    "quality_flags": ["metric:ROLLING_BETA:benchmark_variance_zero"],
                    "error": None,
                }
            },
            "metadata": {"contract_version": "v1", "methodology_version": "rolling_metrics.v1"},
        }

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_risk_rolling_metrics",
        _risk_rolling,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_RISK_ROLLING/risk/rolling"
        "?period=YTD&detail_basis=NET&benchmark_code=BMK_1"
        "&as_of_date=2026-04-04&reporting_currency=USD&include_time_series=true",
        headers={"X-Correlation-Id": "corr-risk-rolling"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "risk-workspace.v1"
    assert body["correlation_id"] == "corr-risk-rolling"
    assert body["state"] == "ready"
    assert body["metadata"]["methodology_version"] == "rolling_metrics.v1"
    assert body["payload"]["periods"][0]["window_results"][0]["window_length"] == 21
    assert len(body["payload"]["periods"][0]["window_results"][0]["metric_series"]) == 1
    assert body["payload"]["periods"][0]["quality_flags"] == [
        "metric:ROLLING_BETA:benchmark_variance_zero"
    ]
    assert {item["key"]: item["state"] for item in body["supportability"]} == {
        "portfolio_returns": "ready",
        "benchmark_returns": "ready",
        "risk_free_series": "ready",
        "rolling_time_series": "ready",
    }


def test_workbench_risk_attribution_router_maps_stateful_attribution(monkeypatch):
    async def _risk_attribution(self, payload, correlation_id):  # noqa: ARG001
        assert payload["input_mode"] == "stateful"
        assert payload["stateful_input"]["portfolio_id"] == "PF_RISK_ATTRIBUTION"
        assert payload["stateful_input"]["benchmark_id"] == "BMK_1"
        assert payload["stateful_input"]["attribution_options"] == {
            "attribution_types": ["ACTIVE_RISK"],
            "metrics": ["TRACKING_ERROR"],
            "grouping_dimensions": ["ASSET_CLASS"],
            "annualization_basis": 252,
        }
        return 200, {
            "source_service": "lotus-risk",
            "input_mode": "stateful",
            "results": {
                "YTD": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-04-04",
                    "attribution_sets": [
                        {
                            "attribution_type": "ACTIVE_RISK",
                            "metric": "TRACKING_ERROR",
                            "grouping_dimension": "ASSET_CLASS",
                            "total_value": 0.034,
                            "reconciled_sum": 0.033,
                            "residual": 0.001,
                            "contributors": [
                                {
                                    "group_key": "EQUITY",
                                    "group_label": "Equity",
                                    "weight_average": 0.62,
                                    "marginal_contribution": 0.018,
                                    "component_contribution": 0.016,
                                    "percent_contribution": 0.47,
                                }
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

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_risk_historical_attribution",
        _risk_attribution,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_RISK_ATTRIBUTION/risk/attribution"
        "?period=YTD&detail_basis=NET&benchmark_code=BMK_1"
        "&as_of_date=2026-04-04&reporting_currency=USD"
        "&attribution_type=ACTIVE_RISK&grouping_dimension=ASSET_CLASS",
        headers={"X-Correlation-Id": "corr-risk-attribution"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "risk-workspace.v1"
    assert body["correlation_id"] == "corr-risk-attribution"
    assert body["state"] == "ready"
    assert body["metadata"]["methodology_version"] == "historical_attribution.v1"
    assert body["payload"]["controls"]["selected_attribution_type"] == "ACTIVE_RISK"
    assert body["payload"]["controls"]["selected_grouping_dimension"] == "ASSET_CLASS"
    assert body["payload"]["periods"][0]["attribution_sets"][0]["metric"] == "TRACKING_ERROR"
    assert (
        body["payload"]["periods"][0]["attribution_sets"][0]["contributors"][0]["group_label"]
        == "Equity"
    )


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
                "evidence": {"state": "supported"},
            },
            "evidence_view": {
                "state": "supported",
                "reason": "Execution and lineage evidence are exposed.",
                "calculations": [
                    {
                        "calculation_role": "workspace_summary",
                        "calculation_id": "calc-workspace-summary",
                        "analytics_type": "WORKSPACE_SUMMARY",
                        "execution_status": "complete",
                        "execution_mode": "sync",
                        "lineage_status": "complete",
                        "stage_statuses": [],
                        "upstream_snapshots": [],
                        "artifacts": [
                            {
                                "artifact_name": "request.json",
                                "url": (
                                    "/api/v1/workbench/PF_1001/performance/evidence/artifacts/"
                                    "calc-workspace-summary/request.json"
                                ),
                            }
                        ],
                    }
                ],
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
    assert body["requested_chart_frequency_supported"] is True
    assert body["requested_contribution_dimension_supported"] is True
    assert body["requested_attribution_dimension_supported"] is True
    assert body["benchmark_options"][0]["benchmark_code"] == "MODEL_60_40"
    assert body["overview"]["market_value_base"] == 1250000.0
    assert body["gross_performance"]["portfolio_return_pct"] == 5.88
    assert body["net_performance"]["portfolio_return_pct"] == 5.42
    assert body["net_performance"]["benchmark_input_mode"] == "stateful"
    assert body["money_weighted_return"]["input_mode"] == "stateful"
    assert body["money_weighted_return"]["begin_market_value"] == 1200000.0
    assert body["money_weighted_return"]["flow_adjusted_end_market_value"] == 1208000.0
    assert body["money_weighted_return"]["net_cash_flow"] == 42000.0
    assert body["capabilities"]["evidence"]["state"] == "supported"
    assert body["evidence_view"]["calculations"][0]["calculation_role"] == "workspace_summary"
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
                "evidence": {"state": "partial"},
            },
            "evidence_view": {
                "state": "partial",
                "reason": "Lineage is still pending for one or more calculations.",
                "calculations": [
                    {
                        "calculation_role": "workspace_summary",
                        "calculation_id": "calc-workspace-summary",
                        "analytics_type": "WORKSPACE_SUMMARY",
                        "execution_status": "complete",
                        "execution_mode": "sync",
                        "lineage_status": "pending",
                        "stage_statuses": [],
                        "upstream_snapshots": [],
                        "artifacts": [],
                    }
                ],
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
    assert body["requested_chart_frequency_supported"] is True
    assert body["requested_contribution_dimension_supported"] is True
    assert body["requested_attribution_dimension_supported"] is True
    assert body["segment"] == "asset_class"
    assert body["net_chart"][0]["label"] == "2026-01"
    assert body["gross_chart"] == []
    assert body["contribution"]["coverage_mv_pct"] == 98.7
    assert body["attribution"]["benchmark_id"] == "MODEL_60_40"
    assert body["capabilities"]["evidence"]["state"] == "partial"
    assert body["evidence_view"]["state"] == "partial"
    assert "overview" not in body
    assert "net_performance" not in body


def test_workbench_performance_summary_router_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["period"] = period
        captured["chart_frequency"] = chart_frequency
        captured["contribution_dimension"] = contribution_dimension
        captured["attribution_dimension"] = attribution_dimension
        captured["detail_basis"] = detail_basis
        captured["benchmark_code"] = benchmark_code
        captured["explicit_start_date"] = explicit_start_date
        captured["explicit_end_date"] = explicit_end_date
        return {
            "correlation_id": correlation_id,
            "contract_version": "v1",
            "portfolio_id": portfolio_id,
            "as_of_date": "2026-02-24",
            "period": period,
            "report_start_date": explicit_start_date,
            "report_end_date": explicit_end_date,
            "chart_frequency": chart_frequency,
            "detail_basis": detail_basis,
            "benchmark_code": benchmark_code,
            "portfolio": {
                "portfolio_id": portfolio_id,
                "client_id": "CIF_1001",
                "base_currency": "USD",
                "booking_center_code": "SG",
            },
            "overview": {
                "market_value_base": 1250000.0,
                "cash_weight_pct": 0.08,
                "position_count": 42,
            },
            "capabilities": {
                "summary_kpis": {"state": "supported"},
                "return_path": {"state": "supported"},
                "benchmark_comparison": {"state": "supported"},
                "multi_horizon_returns": {"state": "supported"},
                "contribution_ranking": {"state": "supported"},
                "attribution_detail": {"state": "supported"},
                "contribution_detail": {"state": "supported"},
                "evidence": {"state": "supported"},
            },
            "net_performance": {
                "metric_basis": detail_basis,
                "portfolio_return_pct": 5.42,
                "benchmark_return_pct": 4.9,
                "active_return_pct": 0.52,
                "requested_period_supported": True,
                "requested_chart_frequency_supported": True,
                "requested_attribution_dimension_supported": True,
                "benchmark_input_mode": "stateful",
                "lineage_state": "supported",
                "net_chart": [],
                "benchmark_options": [],
            },
            "gross_performance": {
                "metric_basis": "GROSS",
                "portfolio_return_pct": 5.88,
                "benchmark_return_pct": 4.9,
                "active_return_pct": 0.98,
                "benchmark_input_mode": "stateful",
            },
            "money_weighted_return": {
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
            "evidence_view": {"state": "supported", "reason": None, "calculations": []},
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_workspace_summary",
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/summary"
        "?period=EXPLICIT&chart_frequency=weekly&contribution_dimension=sector"
        "&attribution_dimension=country&detail_basis=GROSS"
        "&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
        "&report_start_date=2026-01-01&report_end_date=2026-03-27",
        headers={"X-Correlation-Id": "corr-performance-summary"},
    )

    assert response.status_code == 200
    body = response.json()
    assert captured == {
        "portfolio_id": "PF_1001",
        "correlation_id": "corr-performance-summary",
        "period": "EXPLICIT",
        "chart_frequency": "weekly",
        "contribution_dimension": "sector",
        "attribution_dimension": "country",
        "detail_basis": "GROSS",
        "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
        "explicit_start_date": "2026-01-01",
        "explicit_end_date": "2026-03-27",
    }
    assert body["period"] == "EXPLICIT"
    assert body["report_start_date"] == "2026-01-01"
    assert body["report_end_date"] == "2026-03-27"
    assert body["detail_basis"] == "GROSS"
    assert body["benchmark_code"] == "BMK_GLOBAL_BALANCED_60_40"


def test_workbench_performance_details_router_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["period"] = period
        captured["chart_frequency"] = chart_frequency
        captured["contribution_dimension"] = contribution_dimension
        captured["attribution_dimension"] = attribution_dimension
        captured["detail_basis"] = detail_basis
        captured["benchmark_code"] = benchmark_code
        captured["explicit_start_date"] = explicit_start_date
        captured["explicit_end_date"] = explicit_end_date
        return {
            "correlation_id": correlation_id,
            "contract_version": "v1",
            "portfolio_id": portfolio_id,
            "as_of_date": "2026-02-24",
            "period": period,
            "report_start_date": explicit_start_date,
            "report_end_date": explicit_end_date,
            "chart_frequency": chart_frequency,
            "contribution_dimension": contribution_dimension,
            "attribution_dimension": attribution_dimension,
            "detail_basis": detail_basis,
            "segment": attribution_dimension,
            "benchmark_code": benchmark_code,
            "capabilities": {
                "summary_kpis": {"state": "supported"},
                "return_path": {"state": "supported"},
                "benchmark_comparison": {"state": "supported"},
                "multi_horizon_returns": {"state": "supported"},
                "contribution_ranking": {"state": "supported"},
                "attribution_detail": {"state": "supported"},
                "contribution_detail": {"state": "supported"},
                "evidence": {"state": "partial"},
            },
            "evidence_view": {
                "state": "partial",
                "reason": "Lineage is still pending for one or more calculations.",
                "calculations": [],
            },
            "net_chart": [],
            "gross_chart": [],
            "contribution": {
                "metric_basis": detail_basis,
                "weighting_scheme": "average_weight",
                "portfolio_contribution_pct": 5.42,
                "total_portfolio_return_pct": 5.42,
                "coverage_mv_pct": 98.7,
                "levels": [],
            },
            "attribution": {
                "metric_basis": detail_basis,
                "model": "BF",
                "linking": "carino",
                "benchmark_id": benchmark_code,
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
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/details"
        "?period=EXPLICIT&chart_frequency=weekly&contribution_dimension=sector"
        "&attribution_dimension=country&detail_basis=GROSS"
        "&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
        "&report_start_date=2026-01-01&report_end_date=2026-03-27",
        headers={"X-Correlation-Id": "corr-performance-details"},
    )

    assert response.status_code == 200
    body = response.json()
    assert captured == {
        "portfolio_id": "PF_1001",
        "correlation_id": "corr-performance-details",
        "period": "EXPLICIT",
        "chart_frequency": "weekly",
        "contribution_dimension": "sector",
        "attribution_dimension": "country",
        "detail_basis": "GROSS",
        "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
        "explicit_start_date": "2026-01-01",
        "explicit_end_date": "2026-03-27",
    }
    assert body["period"] == "EXPLICIT"
    assert body["report_start_date"] == "2026-01-01"
    assert body["report_end_date"] == "2026-03-27"
    assert body["detail_basis"] == "GROSS"
    assert body["benchmark_code"] == "BMK_GLOBAL_BALANCED_60_40"


def test_workbench_performance_evidence_artifact_router(monkeypatch):
    captured: dict[str, str] = {}

    async def _artifact(self, calculation_id, artifact_name, correlation_id):
        captured["calculation_id"] = calculation_id
        captured["artifact_name"] = artifact_name
        captured["correlation_id"] = correlation_id
        return b"{}", "application/json"

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_evidence_artifact",
        _artifact,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/evidence/artifacts/"
        "calc-workspace-summary/request.json"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.text == "{}"
    assert captured["calculation_id"] == "calc-workspace-summary"
    assert captured["artifact_name"] == "request.json"
    assert captured["correlation_id"]


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
                    "period_start": "2026-02-01",
                    "period_end": "2026-02-24",
                    "net_return_pct": 1.2,
                    "portfolio_return_pct": 1.2,
                    "benchmark_return_pct": 1.0,
                    "active_return_pct": 0.2,
                    "annualized_return_pct": 1.2,
                },
                {
                    "period": "YTD",
                    "period_start": "2026-01-01",
                    "period_end": "2026-02-24",
                    "net_return_pct": 5.4,
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
    assert body["detail_basis"] == "NET"
    assert body["benchmark_code"] == "MODEL_60_40"
    assert body["benchmark_options"][0]["benchmark_name"] == "Model 60/40"
    assert body["requested_chart_frequency_supported"] is True
    assert body["rows"][0]["period"] == "MTD"
    assert body["rows"][0]["period_start"] == "2026-02-01"
    assert body["rows"][0]["portfolio_return_pct"] == 1.2
    assert body["rows"][0]["net_return_pct"] == 1.2
    assert body["rows"][1]["benchmark_return_pct"] == 4.9
    assert body["rows"][1]["annualized_return_pct"] == 5.4
    assert body["warnings"] == []
    assert body["partial_failures"] == []


def test_workbench_performance_horizon_comparison_router_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        chart_frequency: str,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["period"] = period
        captured["detail_basis"] = detail_basis
        captured["benchmark_code"] = benchmark_code
        captured["chart_frequency"] = chart_frequency
        captured["explicit_start_date"] = explicit_start_date
        captured["explicit_end_date"] = explicit_end_date
        return {
            "correlation_id": correlation_id,
            "contract_version": "v1",
            "portfolio_id": portfolio_id,
            "as_of_date": "2026-02-24",
            "period": period,
            "report_start_date": explicit_start_date,
            "report_end_date": explicit_end_date,
            "detail_basis": detail_basis,
            "chart_frequency": chart_frequency,
            "requested_chart_frequency_supported": True,
            "benchmark_code": benchmark_code,
            "benchmark_options": [],
            "rows": [],
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_horizon_comparison",
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/horizon-comparison"
        "?period=EXPLICIT&detail_basis=GROSS&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
        "&chart_frequency=weekly&report_start_date=2026-01-01&report_end_date=2026-03-27",
        headers={"X-Correlation-Id": "corr-horizon"},
    )

    assert response.status_code == 200
    assert captured == {
        "portfolio_id": "PF_1001",
        "correlation_id": "corr-horizon",
        "period": "EXPLICIT",
        "detail_basis": "GROSS",
        "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
        "chart_frequency": "weekly",
        "explicit_start_date": "2026-01-01",
        "explicit_end_date": "2026-03-27",
    }


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
    assert body["detail_basis"] == "NET"
    assert body["attribution_dimension"] == "asset_class"
    assert body["benchmark_code"] == "MODEL_60_40"
    assert body["requested_chart_frequency_supported"] is True
    assert body["requested_attribution_dimension_supported"] is True
    assert body["rows"][0]["period_label"] == "2026-01"
    assert body["rows"][0]["allocation_pct"] == 0.12
    assert body["rows"][0]["selection_pct"] == 0.08
    assert body["rows"][0]["interaction_pct"] == 0.02
    assert body["rows"][0]["cumulative_total_effect_pct"] == 0.22
    assert body["warnings"] == []
    assert body["partial_failures"] == []


def test_workbench_performance_attribution_trend_router_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["period"] = period
        captured["chart_frequency"] = chart_frequency
        captured["attribution_dimension"] = attribution_dimension
        captured["detail_basis"] = detail_basis
        captured["benchmark_code"] = benchmark_code
        captured["explicit_start_date"] = explicit_start_date
        captured["explicit_end_date"] = explicit_end_date
        return {
            "correlation_id": correlation_id,
            "contract_version": "v1",
            "portfolio_id": portfolio_id,
            "as_of_date": "2026-02-24",
            "period": period,
            "report_start_date": explicit_start_date,
            "report_end_date": explicit_end_date,
            "chart_frequency": chart_frequency,
            "detail_basis": detail_basis,
            "attribution_dimension": attribution_dimension,
            "requested_chart_frequency_supported": True,
            "requested_attribution_dimension_supported": True,
            "benchmark_code": benchmark_code,
            "rows": [],
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        "app.services.performance_workspace_service.PerformanceWorkspaceService.get_performance_attribution_trend",
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/attribution-trend"
        "?period=EXPLICIT&chart_frequency=weekly&attribution_dimension=country"
        "&detail_basis=GROSS&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
        "&report_start_date=2026-01-01&report_end_date=2026-03-27",
        headers={"X-Correlation-Id": "corr-attribution-trend"},
    )

    assert response.status_code == 200
    assert captured == {
        "portfolio_id": "PF_1001",
        "correlation_id": "corr-attribution-trend",
        "period": "EXPLICIT",
        "chart_frequency": "weekly",
        "attribution_dimension": "country",
        "detail_basis": "GROSS",
        "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
        "explicit_start_date": "2026-01-01",
        "explicit_end_date": "2026-03-27",
    }


def test_workbench_performance_monolithic_route_is_absent_from_openapi():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "/api/v1/workbench/{portfolio_id}/performance" not in schema["paths"]


def test_workbench_performance_horizon_comparison_openapi_contract():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    route = schema["paths"]["/api/v1/workbench/{portfolio_id}/performance/horizon-comparison"][
        "get"
    ]
    portfolio_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "portfolio_id"
    )
    period_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "period"
    )
    response_schema = schema["components"]["schemas"]["PerformanceHorizonComparisonResponse"]
    row_schema = schema["components"]["schemas"]["PerformanceHorizonComparisonRow"]

    assert "MTD, QTD, and YTD" in route["description"]
    assert "front-office-safe" in route["description"]
    assert portfolio_parameter["description"]
    assert portfolio_parameter["schema"]["examples"] == ["PF_1001"]
    assert period_parameter["description"]
    assert response_schema["properties"]["correlation_id"]["description"]
    assert response_schema["properties"]["correlation_id"]["examples"] == [
        "corr-performance-horizon-1"
    ]
    assert response_schema["properties"]["contract_version"]["description"]
    assert response_schema["properties"]["contract_version"]["default"] == "v1"
    assert response_schema["properties"]["rows"]["description"]
    assert response_schema["properties"]["benchmark_options"]["description"]
    assert response_schema["properties"]["requested_chart_frequency_supported"]["description"]
    assert row_schema["properties"]["period"]["description"]
    assert row_schema["properties"]["benchmark_return_pct"]["description"]
    assert row_schema["properties"]["active_return_pct"]["description"]
    assert response_schema["example"]["rows"][0]["period"] == "MTD"
    assert (
        response_schema["example"]["benchmark_options"][0]["benchmark_code"]
        == "BMK_GLOBAL_BALANCED_60_40"
    )


def test_workbench_performance_evidence_openapi_contract():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    artifact_route = schema["paths"][
        "/api/v1/workbench/{portfolio_id}/performance/evidence/artifacts/{calculation_id}/{artifact_name}"
    ]["get"]
    summary_schema = schema["components"]["schemas"]["PerformanceWorkspaceSummaryResponse"]
    details_schema = schema["components"]["schemas"]["PerformanceWorkspaceDetailsResponse"]
    evidence_schema = schema["components"]["schemas"]["PerformanceEvidenceView"]
    calculation_schema = schema["components"]["schemas"]["PerformanceCalculationEvidenceView"]
    artifact_schema = schema["components"]["schemas"]["PerformanceEvidenceArtifactView"]

    assert "lineage artifact" in artifact_route["description"]
    assert summary_schema["properties"]["correlation_id"]["description"]
    assert summary_schema["properties"]["correlation_id"]["examples"] == [
        "corr-performance-summary-1"
    ]
    assert summary_schema["properties"]["contract_version"]["description"]
    assert summary_schema["properties"]["contract_version"]["default"] == "v1"
    assert summary_schema["properties"]["portfolio_id"]["description"]
    assert summary_schema["properties"]["as_of_date"]["description"]
    assert summary_schema["properties"]["period"]["description"]
    assert summary_schema["properties"]["report_start_date"]["description"]
    assert summary_schema["properties"]["report_end_date"]["description"]
    assert summary_schema["properties"]["chart_frequency"]["description"]
    assert summary_schema["properties"]["detail_basis"]["description"]
    assert summary_schema["properties"]["requested_chart_frequency_supported"]["description"]
    assert summary_schema["properties"]["requested_contribution_dimension_supported"]["description"]
    assert summary_schema["properties"]["requested_attribution_dimension_supported"]["description"]
    assert summary_schema["properties"]["benchmark_code"]["description"]
    assert summary_schema["properties"]["benchmark_options"]["description"]
    assert summary_schema["properties"]["capabilities"]["description"]
    assert (
        summary_schema["example"]["benchmark_options"][0]["benchmark_code"]
        == "BMK_GLOBAL_BALANCED_60_40"
    )
    assert summary_schema["example"]["evidence_view"]["state"] == "partial"
    assert details_schema["properties"]["correlation_id"]["description"]
    assert details_schema["properties"]["correlation_id"]["examples"] == [
        "corr-performance-details-1"
    ]
    assert details_schema["properties"]["contract_version"]["description"]
    assert details_schema["properties"]["contract_version"]["default"] == "v1"
    assert details_schema["properties"]["portfolio_id"]["description"]
    assert details_schema["properties"]["as_of_date"]["description"]
    assert details_schema["properties"]["period"]["description"]
    assert details_schema["properties"]["report_start_date"]["description"]
    assert details_schema["properties"]["report_end_date"]["description"]
    assert details_schema["properties"]["chart_frequency"]["description"]
    assert details_schema["properties"]["contribution_dimension"]["description"]
    assert details_schema["properties"]["attribution_dimension"]["description"]
    assert details_schema["properties"]["detail_basis"]["description"]
    assert details_schema["properties"]["requested_chart_frequency_supported"]["description"]
    assert details_schema["properties"]["requested_contribution_dimension_supported"]["description"]
    assert details_schema["properties"]["requested_attribution_dimension_supported"]["description"]
    assert details_schema["properties"]["segment"]["description"]
    assert details_schema["properties"]["benchmark_code"]["description"]
    assert details_schema["properties"]["capabilities"]["description"]
    assert details_schema["example"]["segment"] == "asset_class"
    assert details_schema["example"]["contribution"]["coverage_mv_pct"] == 98.7
    assert summary_schema["properties"]["evidence_view"]["description"]
    assert details_schema["properties"]["evidence_view"]["description"]
    assert details_schema["properties"]["net_chart"]["description"]
    assert details_schema["properties"]["gross_chart"]["description"]
    assert details_schema["properties"]["contribution"]["description"]
    assert details_schema["properties"]["attribution"]["description"]
    assert details_schema["properties"]["warnings"]["description"]
    assert details_schema["properties"]["partial_failures"]["description"]
    assert evidence_schema["properties"]["state"]["description"]
    assert evidence_schema["properties"]["calculations"]["description"]
    assert calculation_schema["properties"]["execution_status"]["description"]
    assert calculation_schema["properties"]["lineage_status"]["description"]
    assert calculation_schema["properties"]["artifacts"]["description"]
    assert artifact_schema["properties"]["url"]["description"]


def test_workbench_performance_details_attribution_openapi_contract():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    details_route = schema["paths"]["/api/v1/workbench/{portfolio_id}/performance/details"]["get"]
    attribution_schema = schema["components"]["schemas"]["AttributionSummaryView"]
    attribution_level_schema = schema["components"]["schemas"]["AttributionLevelView"]
    attribution_row_schema = schema["components"]["schemas"]["AttributionRowView"]

    assert details_route["description"]
    assert attribution_schema["properties"]["active_return_pct"]["description"]
    assert attribution_schema["properties"]["levels"]["description"]
    assert attribution_level_schema["properties"]["allocation_total_pct"]["description"]
    assert attribution_level_schema["properties"]["selection_total_pct"]["description"]
    assert attribution_level_schema["properties"]["interaction_total_pct"]["description"]
    assert attribution_level_schema["properties"]["total_effect_pct"]["description"]
    assert (
        "without gateway-side truncation"
        in attribution_level_schema["properties"]["rows"]["description"]
    )
    assert attribution_row_schema["properties"]["portfolio_weight_avg_pct"]["description"]
    assert attribution_row_schema["properties"]["benchmark_return_pct"]["description"]


def test_workbench_performance_attribution_trend_openapi_contract():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    route = schema["paths"]["/api/v1/workbench/{portfolio_id}/performance/attribution-trend"]["get"]
    portfolio_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "portfolio_id"
    )
    period_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "period"
    )
    dimension_parameter = next(
        parameter
        for parameter in route["parameters"]
        if parameter["name"] == "attribution_dimension"
    )
    response_schema = schema["components"]["schemas"]["PerformanceAttributionTrendResponse"]
    row_schema = schema["components"]["schemas"]["PerformanceAttributionTrendRow"]

    assert "allocation, selection, interaction, and total-effect" in route["description"]
    assert portfolio_parameter["description"]
    assert portfolio_parameter["schema"]["examples"] == ["PF_1001"]
    assert period_parameter["description"]
    assert dimension_parameter["description"]
    assert response_schema["properties"]["correlation_id"]["description"]
    assert response_schema["properties"]["correlation_id"]["examples"] == [
        "corr-performance-attribution-1"
    ]
    assert response_schema["properties"]["contract_version"]["description"]
    assert response_schema["properties"]["contract_version"]["default"] == "v1"
    assert response_schema["properties"]["rows"]["description"]
    assert response_schema["properties"]["requested_chart_frequency_supported"]["description"]
    assert response_schema["properties"]["requested_attribution_dimension_supported"]["description"]
    assert row_schema["properties"]["total_effect_pct"]["description"]
    assert row_schema["properties"]["cumulative_total_effect_pct"]["description"]
    assert row_schema["properties"]["residual_pct"]["description"]
    assert response_schema["example"]["rows"][0]["period_label"] == "2026-01"
    assert response_schema["example"]["rows"][1]["cumulative_total_effect_pct"] == 0.4


def test_workbench_performance_advisor_brief_openapi_contract():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    route = schema["paths"]["/api/v1/workbench/{portfolio_id}/performance/advisor-brief"]["get"]
    portfolio_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "portfolio_id"
    )
    period_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "period"
    )
    benchmark_parameter = next(
        parameter for parameter in route["parameters"] if parameter["name"] == "benchmark_code"
    )
    response_schema = schema["components"]["schemas"]["AdvisorBriefResponse"]
    narrative_schema = schema["components"]["schemas"]["AdvisorBriefNarrativeItem"]
    evidence_ref_schema = schema["components"]["schemas"]["AdvisorBriefEvidenceRef"]

    assert "lotus-ai" in route["description"]
    assert portfolio_parameter["description"]
    assert portfolio_parameter["schema"]["examples"] == ["PF_1001"]
    assert period_parameter["description"]
    assert benchmark_parameter["description"]
    assert response_schema["properties"]["correlation_id"]["description"]
    assert response_schema["properties"]["correlation_id"]["examples"] == ["corr-advisor-brief-1"]
    assert response_schema["properties"]["contract_version"]["description"]
    assert response_schema["properties"]["contract_version"]["default"] == "v1"
    assert response_schema["properties"]["summary"]["description"]
    assert response_schema["properties"]["talking_points"]["description"]
    assert response_schema["properties"]["ai_audit"]["description"]
    assert response_schema["properties"]["supportability"]["description"]
    assert narrative_schema["properties"]["evidence_refs"]["description"]
    assert evidence_ref_schema["properties"]["source_surface"]["description"]


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


def test_workbench_performance_advisor_brief_router_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _service(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ):
        captured["portfolio_id"] = portfolio_id
        captured["correlation_id"] = correlation_id
        captured["period"] = period
        captured["chart_frequency"] = chart_frequency
        captured["contribution_dimension"] = contribution_dimension
        captured["attribution_dimension"] = attribution_dimension
        captured["detail_basis"] = detail_basis
        captured["benchmark_code"] = benchmark_code
        captured["explicit_start_date"] = explicit_start_date
        captured["explicit_end_date"] = explicit_end_date
        return AdvisorBriefResponse(
            correlation_id=correlation_id,
            contract_version="v1",
            portfolio_id=portfolio_id,
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id=portfolio_id,
                client_id="CIF_1001",
                base_currency="USD",
                booking_center_code="SG",
            ),
            as_of_date="2026-04-04",
            period=period,
            report_start_date=explicit_start_date or "2026-01-01",
            report_end_date=explicit_end_date or "2026-04-04",
            detail_basis=detail_basis,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            benchmark_code=benchmark_code,
            status=AdvisorBriefStatus.READY,
            summary="Advisor summary.",
            talking_points=[],
            recommended_actions=[],
            risks_and_exceptions=[],
            source_metrics=[],
            supportability=[],
            ai_audit={},
            ai_evidence={},
        )

    monkeypatch.setattr(
        "app.services.advisor_brief_service.AdvisorBriefService.get_performance_advisor_brief",
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/workbench/PF_1001/performance/advisor-brief"
        "?period=EXPLICIT&chart_frequency=weekly&contribution_dimension=sector"
        "&attribution_dimension=country&detail_basis=GROSS"
        "&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
        "&report_start_date=2026-01-01&report_end_date=2026-03-27",
        headers={"X-Correlation-Id": "corr-advisor-brief"},
    )

    assert response.status_code == 200
    assert captured == {
        "portfolio_id": "PF_1001",
        "correlation_id": "corr-advisor-brief",
        "period": "EXPLICIT",
        "chart_frequency": "weekly",
        "contribution_dimension": "sector",
        "attribution_dimension": "country",
        "detail_basis": "GROSS",
        "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
        "explicit_start_date": "2026-01-01",
        "explicit_end_date": "2026-03-27",
    }


def test_workbench_sandbox_changes_router(monkeypatch):
    captured_create: dict[str, object] = {}
    captured_apply: dict[str, object] = {}

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

    async def _create_session(self, portfolio_id, correlation_id, created_by, ttl_hours):
        captured_create["portfolio_id"] = portfolio_id
        captured_create["correlation_id"] = correlation_id
        captured_create["created_by"] = created_by
        captured_create["ttl_hours"] = ttl_hours
        return await _pas_create()

    async def _apply_changes(self, session_id, changes, correlation_id):
        captured_apply["session_id"] = session_id
        captured_apply["changes"] = changes
        captured_apply["correlation_id"] = correlation_id
        return await _pas_add()

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _pas_core)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.create_simulation_session",
        _create_session,
    )
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.add_simulation_changes",
        _apply_changes,
    )
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
        "/api/v1/workbench/PF_1001/sandbox/sessions",
        json={"created_by": "advisor_1", "ttl_hours": 48},
    )
    assert created.status_code == 200
    created_body = created.json()
    assert created_body["portfolio_id"] == "PF_1001"
    assert created_body["session_id"] == "sess_1"
    assert created_body["session_version"] == 1
    assert created_body["projected_positions"][0]["security_id"] == "EQ_1"
    assert created_body["projected_summary"]["net_delta_quantity"] == 2.0
    assert created_body["policy_feedback"] is None
    assert created_body["warnings"] == []
    assert created_body["partial_failures"] == []
    assert captured_create["portfolio_id"] == "PF_1001"
    assert captured_create["created_by"] == "advisor_1"
    assert captured_create["ttl_hours"] == 48
    assert captured_create["correlation_id"]

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
    assert body["projected_positions"][0]["security_id"] == "EQ_1"
    assert body["projected_summary"]["total_baseline_positions"] == 1
    assert body["projected_summary"]["net_delta_quantity"] == 2.0
    assert body["policy_feedback"]["status"] == "PASS"
    assert body["policy_feedback"]["raw"]["status"] == "COMPLETED"
    assert body["warnings"] == []
    assert body["partial_failures"] == []
    assert captured_apply["session_id"] == "sess_1"
    assert captured_apply["correlation_id"]
    assert captured_apply["changes"] == [
        {"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 2.0}
    ]
