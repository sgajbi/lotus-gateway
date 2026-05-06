import pytest

from app.services.workbench_service import WorkbenchService


class _StubLotusCoreQueryClient:
    def __init__(
        self,
        portfolio_status_code: int,
        portfolio_payload: dict,
        snapshot_status_code: int,
        snapshot_payload: dict,
    ):
        self.portfolio_status_code = portfolio_status_code
        self.portfolio_payload = portfolio_payload
        self.snapshot_status_code = snapshot_status_code
        self.snapshot_payload = snapshot_payload
        self.reference_calls = 0
        self.snapshot_calls: list[dict[str, object]] = []

    async def get_portfolio(self, portfolio_id: str, correlation_id: str):  # noqa: ARG002
        return self.portfolio_status_code, self.portfolio_payload

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        self.snapshot_calls.append(
            {
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date,
                "sections": sections,
                "consumer_system": consumer_system,
                "correlation_id": correlation_id,
            }
        )
        return self.snapshot_status_code, self.snapshot_payload

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ):
        self.reference_calls += 1
        return 200, {"performance_end_date": "2026-02-23"}

    async def get_projected_positions(self, session_id: str, correlation_id: str):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "baseline_quantity": 10.0,
                    "proposed_quantity": 15.0,
                    "delta_quantity": 5.0,
                }
            ]
        }

    async def get_projected_summary(self, session_id: str, correlation_id: str):
        return 200, {
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 5.0,
        }

    async def create_simulation_session(
        self,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ):
        return 201, {"session": {"session_id": "sess_1", "version": 1}}

    async def add_simulation_changes(
        self,
        session_id: str,
        changes: list[dict],
        correlation_id: str,
    ):
        return 200, {"session_id": session_id, "version": 2}


class _StubLotusAnalyticsClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload
        self.last_report_end_date: str | None = None
        self.workbench_status_code = 200
        self.workbench_payload = {
            "portfolioId": "PF_1001",
            "period": "YTD",
            "groupBy": "ASSET_CLASS",
            "benchmarkCode": "MODEL_60_40",
            "portfolioReturnPct": 1.0,
            "benchmarkReturnPct": 3.1,
            "activeReturnPct": -2.1,
            "allocationBuckets": [
                {
                    "bucketKey": "EQUITY",
                    "bucketLabel": "EQUITY",
                    "currentQuantity": 10.0,
                    "proposedQuantity": 15.0,
                    "deltaQuantity": 5.0,
                    "currentWeightPct": 100.0,
                    "proposedWeightPct": 100.0,
                }
            ],
            "topChanges": [
                {
                    "securityId": "EQ_1",
                    "instrumentName": "Equity 1",
                    "deltaQuantity": 5.0,
                    "direction": "INCREASE",
                }
            ],
        }
        self.twr_calls = 0

    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ):
        self.twr_calls += 1
        self.last_report_end_date = report_end_date
        return self.status_code, self.payload

    async def get_twr_analytics(
        self,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
    ):
        _ = report_start_date, metric_basis, benchmark_id
        return await self.get_stateful_twr(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            period=period,
            correlation_id=correlation_id,
        )

    async def get_workbench_analytics(self, payload: dict, correlation_id: str):  # noqa: ARG002
        return self.workbench_status_code, self.workbench_payload


class _StubDpmClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload
        self.list_runs_calls = 0

    async def list_runs(self, params: dict, correlation_id: str):
        self.list_runs_calls += 1
        return self.status_code, self.payload

    async def simulate_proposal(
        self,
        body: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        return 200, {"status": "COMPLETED", "gate_decision": {"status": "PASS"}}


@pytest.mark.asyncio
async def test_workbench_overview_success():
    analytics_client = _StubLotusAnalyticsClient(
        200,
        {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 3.2}}}}
            },
        },
    )
    lotus_core_client = _StubLotusCoreQueryClient(
        200,
        {
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
            "client_id": "CIF_1001",
        },
        200,
        {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 10,
                        "market_value_base": 400.0,
                        "weight": 0.4,
                    },
                    {
                        "security_id": "EQ_2",
                        "quantity": 5,
                        "market_value_base": 400.0,
                        "weight": 0.4,
                    },
                    {
                        "security_id": "CASH_USD",
                        "quantity": 200.0,
                        "market_value_base": 200.0,
                        "weight": 0.2,
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
                        "security_id": "EQ_2",
                        "instrument_name": "Equity 2",
                        "asset_class": "Equity",
                    },
                    {
                        "security_id": "CASH_USD",
                        "instrument_name": "US Dollar Cash",
                        "asset_class": "Cash",
                    },
                ],
            },
        },
    )
    service = WorkbenchService(
        lotus_core_query_client=lotus_core_client,
        analytics_client=analytics_client,
        dpm_client=_StubDpmClient(
            200,
            {
                "items": [
                    {
                        "rebalance_run_id": "rr_1",
                        "status": "READY",
                        "created_at": "2026-02-23T00:00:00Z",
                        "workflow_state": "PM_REVIEW_REQUIRED",
                    },
                    {
                        "rebalance_run_id": "rr_0",
                        "status": "FAILED",
                        "created_at": "2026-02-22T00:00:00Z",
                        "error_code": "SOURCE_READINESS_BLOCKED",
                    },
                ],
                "supportability": {
                    "feature_key": "manage.observability.action_register_supportability",
                    "state": "healthy",
                    "reason": "action_register_current",
                    "freshness_bucket": "fresh",
                    "run_count": 2,
                    "operation_count": 4,
                    "workflow_decision_count": 1,
                },
            },
        ),
    )

    response = await service.get_workbench_overview(
        portfolio_id="PF_1001",
        correlation_id="corr-1",
    )

    assert response.portfolio.portfolio_id == "PF_1001"
    assert response.overview.position_count == 3
    assert response.performance_snapshot is not None
    assert lotus_core_client.snapshot_calls[0]["portfolio_id"] == "PF_1001"
    assert lotus_core_client.snapshot_calls[0]["sections"] == [
        "positions_baseline",
        "portfolio_totals",
        "instrument_enrichment",
    ]
    assert lotus_core_client.snapshot_calls[0]["consumer_system"] == "lotus-gateway"
    assert response.performance_snapshot.return_pct == 3.2
    assert response.portfolio.client_id == "CIF_1001"
    assert response.portfolio.booking_center_code == "SG"
    assert response.overview.market_value_base == 1000.0
    assert response.overview.cash_weight_pct == pytest.approx(20.0)
    assert analytics_client.last_report_end_date == "2026-02-23"
    assert response.rebalance_snapshot is not None
    assert response.rebalance_snapshot.status == "READY"
    assert response.rebalance_snapshot.last_rebalance_run_id == "rr_1"
    assert response.rebalance_snapshot.last_run_at_utc == "2026-02-23T00:00:00Z"
    assert response.rebalance_snapshot.supportability is not None
    assert response.rebalance_snapshot.supportability.state == "healthy"
    assert response.rebalance_snapshot.supportability.freshness_bucket == "fresh"
    assert response.rebalance_snapshot.supportability.run_count == 2
    assert response.rebalance_snapshot.supportability.operation_count == 4
    assert response.rebalance_snapshot.supportability.workflow_decision_count == 1
    assert len(response.rebalance_snapshot.recent_runs) == 2
    assert response.rebalance_snapshot.recent_runs[0].rebalance_run_id == "rr_1"
    assert response.rebalance_snapshot.recent_runs[0].workflow_state == "PM_REVIEW_REQUIRED"
    assert response.rebalance_snapshot.recent_runs[1].status == "FAILED"
    assert response.rebalance_snapshot.recent_runs[1].error_code == "SOURCE_READINESS_BLOCKED"
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_workbench_overview_partial_failures():
    service = WorkbenchService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            200,
            {
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
            },
            200,
            {
                "as_of_date": "2026-02-23",
                "sections": {
                    "positions_baseline": [
                        {
                            "security_id": "EQ_1",
                            "quantity": 5,
                            "market_value_base": 450.0,
                            "weight": 0.9,
                        },
                        {
                            "security_id": "CASH_USD",
                            "quantity": 50.0,
                            "market_value_base": 50.0,
                            "weight": 0.1,
                        },
                    ],
                    "portfolio_totals": {"baseline_total_market_value_base": 500.0},
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
            },
        ),
        analytics_client=_StubLotusAnalyticsClient(
            503, {"detail": "lotus-performance unavailable"}
        ),
        dpm_client=_StubDpmClient(500, {"detail": "dpm unavailable"}),
    )

    response = await service.get_workbench_overview(
        portfolio_id="PF_1001",
        correlation_id="corr-2",
    )

    assert response.performance_snapshot is None
    assert response.rebalance_snapshot is None
    assert len(response.partial_failures) == 2
    assert response.warnings == [
        "PERFORMANCE_SNAPSHOT_UNAVAILABLE",
        "MANAGE_REBALANCE_UNAVAILABLE",
    ]


@pytest.mark.asyncio
async def test_workbench_overview_can_skip_performance_and_rebalance_fetches():
    query_client = _StubLotusCoreQueryClient(
        200,
        {
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
            "client_id": "CIF_1001",
        },
        200,
        {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 10,
                        "market_value_base": 750.0,
                        "weight": 0.75,
                    }
                ],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                    }
                ],
            },
        },
    )
    analytics_client = _StubLotusAnalyticsClient(
        200,
        {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 3.2}}}}
            },
        },
    )
    dpm_client = _StubDpmClient(200, {"items": []})
    service = WorkbenchService(
        lotus_core_query_client=query_client,
        analytics_client=analytics_client,
        dpm_client=dpm_client,
    )

    response = await service.get_workbench_overview(
        portfolio_id="PF_1001",
        correlation_id="corr-skip",
        include_performance_snapshot=False,
        include_rebalance_snapshot=False,
    )

    assert response.performance_snapshot is None
    assert response.rebalance_snapshot is None
    assert response.warnings == []
    assert response.partial_failures == []
    assert query_client.reference_calls == 0
    assert analytics_client.twr_calls == 0
    assert dpm_client.list_runs_calls == 0


@pytest.mark.asyncio
async def test_workbench_portfolio_360_with_projected_state():
    lotus_core_client = _StubLotusCoreQueryClient(
        200,
        {
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
            "client_id": "CIF_1001",
        },
        200,
        {
            "as_of_date": "2026-02-23",
            "sections": {
                "positions_baseline": [
                    {
                        "security_id": "EQ_1",
                        "quantity": 10,
                        "market_value_base": 420.5,
                        "weight": 0.4205,
                    }
                ],
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "instrument_enrichment": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                    }
                ],
            },
        },
    )
    service = WorkbenchService(
        lotus_core_query_client=lotus_core_client,
        analytics_client=_StubLotusAnalyticsClient(
            200,
            {
                "results_by_period": {
                    "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.0}}}}
                }
            },
        ),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )
    response = await service.get_portfolio_360(
        portfolio_id="PF_1001",
        correlation_id="corr-3",
        session_id="sess_1",
    )
    assert response.active_session_id == "sess_1"
    assert len(lotus_core_client.snapshot_calls) == 1
    assert len(response.current_positions) == 1
    assert response.current_positions[0].security_id == "EQ_1"
    assert response.current_positions[0].instrument_name == "Equity 1"
    assert response.current_positions[0].asset_class == "Equity"
    assert response.current_positions[0].quantity == 10.0
    assert response.current_positions[0].market_value_base == 420.5
    assert response.current_positions[0].weight_pct == pytest.approx(42.05)
    assert len(response.projected_positions) == 1
    assert response.projected_summary is not None
    assert response.projected_positions[0].baseline_quantity == 10.0
    assert response.projected_positions[0].proposed_quantity == 15.0
    assert response.projected_positions[0].delta_quantity == 5.0
    assert response.projected_summary.net_delta_quantity == 5.0


@pytest.mark.asyncio
async def test_create_sandbox_session_returns_projected_state():
    service = WorkbenchService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            200,
            {
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
            },
            200,
            {
                "as_of_date": "2026-02-23",
                "sections": {
                    "positions_baseline": [],
                    "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                    "instrument_enrichment": [],
                },
            },
        ),
        analytics_client=_StubLotusAnalyticsClient(
            200,
            {
                "results_by_period": {
                    "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.0}}}}
                }
            },
        ),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )

    response = await service.create_sandbox_session(
        portfolio_id="PF_1001",
        correlation_id="corr-create",
        created_by="advisor_1",
        ttl_hours=24,
    )

    assert response.portfolio_id == "PF_1001"
    assert response.session_id == "sess_1"
    assert response.session_version == 1
    assert response.projected_positions[0].security_id == "EQ_1"
    assert response.projected_positions[0].proposed_quantity == 15.0
    assert response.projected_summary.total_baseline_positions == 1
    assert response.projected_summary.total_proposed_positions == 1
    assert response.projected_summary.net_delta_quantity == 5.0
    assert response.policy_feedback is None
    assert response.warnings == []
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_workbench_apply_sandbox_changes_with_policy_eval():
    service = WorkbenchService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            200,
            {
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
            },
            200,
            {
                "as_of_date": "2026-02-23",
                "sections": {
                    "positions_baseline": [],
                    "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                    "instrument_enrichment": [],
                },
            },
        ),
        analytics_client=_StubLotusAnalyticsClient(
            200,
            {
                "results_by_period": {
                    "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.0}}}}
                }
            },
        ),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )
    response = await service.apply_sandbox_changes(
        portfolio_id="PF_1001",
        session_id="sess_1",
        correlation_id="corr-4",
        changes=[{"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 5}],
        evaluate_policy=True,
    )
    assert response.session_id == "sess_1"
    assert response.session_version == 2
    assert response.projected_positions[0].security_id == "EQ_1"
    assert response.projected_positions[0].delta_quantity == 5.0
    assert response.projected_summary.total_baseline_positions == 1
    assert response.projected_summary.net_delta_quantity == 5.0
    assert response.policy_feedback is not None
    assert response.policy_feedback.status == "PASS"
    assert response.policy_feedback.raw == {
        "status": "COMPLETED",
        "gate_decision": {"status": "PASS"},
    }


@pytest.mark.asyncio
async def test_workbench_analytics_response():
    service = WorkbenchService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            200,
            {
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
            },
            200,
            {
                "as_of_date": "2026-02-23",
                "sections": {
                    "positions_baseline": [
                        {
                            "security_id": "EQ_1",
                            "quantity": 10,
                            "market_value_base": 300.0,
                            "weight": 0.3,
                        }
                    ],
                    "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                    "instrument_enrichment": [
                        {
                            "security_id": "EQ_1",
                            "instrument_name": "Equity 1",
                            "asset_class": "Equity",
                        }
                    ],
                },
            },
        ),
        analytics_client=_StubLotusAnalyticsClient(
            200,
            {
                "results_by_period": {
                    "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.0}}}}
                }
            },
        ),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )
    response = await service.get_workbench_analytics(
        portfolio_id="PF_1001",
        correlation_id="corr-5",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL_60_40",
        session_id="sess_1",
    )
    assert response.portfolio_id == "PF_1001"
    assert response.group_by == "ASSET_CLASS"
    assert response.session_id == "sess_1"
    assert response.period == "YTD"
    assert response.benchmark_code == "MODEL_60_40"
    assert response.portfolio_return_pct == pytest.approx(1.0)
    assert response.benchmark_return_pct == pytest.approx(3.1)
    assert response.active_return_pct == pytest.approx(-2.1)
    assert len(response.allocation_buckets) == 1
    assert response.allocation_buckets[0].bucket_key == "EQUITY"
    assert response.allocation_buckets[0].current_quantity == pytest.approx(10.0)
    assert response.allocation_buckets[0].proposed_quantity == pytest.approx(15.0)
    assert response.allocation_buckets[0].delta_quantity == pytest.approx(5.0)
    assert response.top_changes[0].security_id == "EQ_1"
    assert response.top_changes[0].instrument_name == "Equity 1"
    assert response.top_changes[0].delta_quantity == pytest.approx(5.0)
    assert response.top_changes[0].direction == "INCREASE"
    assert "risk_proxy" not in response.model_dump()
    assert "RISK_BFF_PENDING" in response.warnings
    assert any(
        failure.source_service == "risk" and failure.error_code == "RISK_BFF_NOT_IMPLEMENTED"
        for failure in response.partial_failures
    )
