from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPortfolio360Response,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
    WorkbenchProjectedPositionView,
)
from app.services.workbench_analytics_projection import (
    build_workbench_allocation_buckets,
    build_workbench_return_metrics,
    build_workbench_top_changes,
    quantity_change_direction,
    with_controlled_risk_bff_gap,
    workbench_position_bucket_key,
)
from app.services.workbench_core_snapshot import (
    extract_current_positions,
    parse_lotus_core_snapshot,
)
from app.services.workbench_performance_snapshot import parse_performance_snapshot
from app.services.workbench_policy_feedback import (
    build_policy_idempotency_key,
    build_policy_simulation_payload,
    parse_policy_feedback_success,
    parse_policy_feedback_unavailable,
)
from app.services.workbench_projected_state import parse_projected_state
from app.services.workbench_rebalance_snapshot import parse_rebalance_snapshot
from app.services.workbench_service import WorkbenchService


class _StubLotusCoreQueryClient:
    def __init__(self):
        self.portfolio_status = 200
        self.portfolio_payload: dict = {"portfolio_id": "P1", "base_currency": "USD"}
        self.core_status = 200
        self.core_payload: dict = {
            "as_of_date": "2026-02-24",
            "sections": {
                "positions_baseline": [],
                "portfolio_totals": {"baseline_total_market_value_base": 0.0},
                "instrument_enrichment": [],
            },
        }
        self.positions_status = 200
        self.positions_payload: dict = {"positions": []}
        self.summary_status = 200
        self.summary_payload: dict = {
            "total_baseline_positions": 0,
            "total_proposed_positions": 0,
            "net_delta_quantity": 0.0,
        }
        self.create_status = 201
        self.create_payload: dict = {"session": {"session_id": "sess-1", "version": 1}}
        self.change_status = 200
        self.change_payload: dict = {"version": 2}

    async def get_portfolio(self, portfolio_id: str, correlation_id: str):  # noqa: ARG002
        return self.portfolio_status, self.portfolio_payload

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return self.core_status, self.core_payload

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ):
        return 200, {"performance_end_date": "2026-02-24"}

    async def get_projected_positions(self, session_id: str, correlation_id: str):
        return self.positions_status, self.positions_payload

    async def get_projected_summary(self, session_id: str, correlation_id: str):
        return self.summary_status, self.summary_payload

    async def create_simulation_session(
        self, portfolio_id: str, created_by: str | None, ttl_hours: int, correlation_id: str
    ):
        return self.create_status, self.create_payload

    async def add_simulation_changes(
        self, session_id: str, changes: list[dict], correlation_id: str
    ):
        return self.change_status, self.change_payload


class _StubLotusAnalyticsClient:
    def __init__(self):
        self.snapshot_status = 200
        self.snapshot_payload: dict = {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 1.2}}}}
            }
        }
        self.analytics_status = 200
        self.analytics_payload: dict = {
            "allocationBuckets": [],
            "topChanges": [],
            "portfolioReturnPct": 1.0,
            "benchmarkReturnPct": 0.8,
            "activeReturnPct": 0.2,
        }

    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ):
        return self.snapshot_status, self.snapshot_payload

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

    async def get_workspace_summary(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        chart_frequency: str,
        detail_basis: str,
        benchmark_id: str | None,
        reporting_currency: str | None,
        segment: str,
        correlation_id: str,
        periods: list[dict] | None = None,
        include_detail_blocks: bool = False,
    ):
        _ = (
            report_start_date,
            chart_frequency,
            detail_basis,
            benchmark_id,
            reporting_currency,
            segment,
            periods,
            include_detail_blocks,
        )
        return await self.get_stateful_twr(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            period=period,
            correlation_id=correlation_id,
        )

    async def get_workbench_analytics(self, payload: dict, correlation_id: str):
        return self.analytics_status, self.analytics_payload


class _StubDpmClient:
    def __init__(self):
        self.list_runs_status = 200
        self.list_runs_payload: dict = {"items": []}
        self.supportability_status = 200
        self.supportability_payload: dict = {}
        self.simulate_status = 200
        self.simulate_payload: dict = {"status": "AVAILABLE"}

    async def list_runs(self, params: dict, correlation_id: str):
        return self.list_runs_status, self.list_runs_payload

    async def get_supportability_summary(self, correlation_id: str):
        return self.supportability_status, self.supportability_payload

    async def simulate_proposal(self, body: dict, idempotency_key: str, correlation_id: str):
        return self.simulate_status, self.simulate_payload


def _build_service() -> tuple[
    WorkbenchService,
    _StubLotusCoreQueryClient,
    _StubLotusAnalyticsClient,
    _StubDpmClient,
]:
    pas = _StubLotusCoreQueryClient()
    performance = _StubLotusAnalyticsClient()
    dpm = _StubDpmClient()
    return (
        WorkbenchService(lotus_core_query_client=pas, analytics_client=performance, dpm_client=dpm),
        pas,
        performance,
        dpm,
    )


def test_raise_for_lotus_core_error_includes_upstream_detail():
    service, _, _, _ = _build_service()
    with pytest.raises(HTTPException) as exc:
        service._raise_for_lotus_core_error(
            500,
            {
                "detail": "downstream unavailable",
                "portfolio_id": "PB_SENSITIVE",
                "stack_trace": "internal traceback",
            },
        )
    assert exc.value.status_code == 502
    assert exc.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": 500,
        "error_code": "LOTUS_CORE_SNAPSHOT_UNAVAILABLE",
        "detail": "downstream unavailable",
    }


def test_parse_lotus_core_snapshot_invalid_structure_raises():
    with pytest.raises(HTTPException) as exc:
        parse_lotus_core_snapshot("P1", [], {}, "2026-02-24")
    assert exc.value.status_code == 502


def test_parse_lotus_core_snapshot_uses_fallback_defaults():
    portfolio, overview, as_of_date = parse_lotus_core_snapshot(
        fallback_portfolio_id="P1",
        portfolio_payload={},
        snapshot_payload={"sections": {}},
        fallback_as_of_date="2026-02-24",
    )
    assert portfolio.portfolio_id == "P1"
    assert portfolio.base_currency == "USD"
    assert overview.cash_weight_pct == 0.0
    assert as_of_date == "2026-02-24"


@pytest.mark.parametrize(
    ("result", "warning"),
    [
        (RuntimeError("boom"), "PERFORMANCE_SNAPSHOT_UNAVAILABLE"),
        (("bad",), "PERFORMANCE_SNAPSHOT_UNAVAILABLE"),
    ],
)
def test_parse_performance_snapshot_handles_exception_and_invalid_result_shape(result, warning):
    partial_failures = []
    warnings = []
    parsed = parse_performance_snapshot(result, partial_failures, warnings)
    assert parsed is None
    assert warning in warnings
    assert len(partial_failures) == 1


def test_parse_performance_snapshot_handles_invalid_payload_types():
    partial_failures = []
    warnings = []
    parsed = parse_performance_snapshot((200, "bad-payload"), partial_failures, warnings)
    assert parsed is None
    assert "PERFORMANCE_SNAPSHOT_UNAVAILABLE" in warnings


def test_parse_performance_snapshot_handles_http_error_payload():
    partial_failures = []
    warnings = []
    parsed = parse_performance_snapshot(
        (
            503,
            {
                "detail": {
                    "code": "PERFORMANCE_DOWN",
                    "message": "lotus-performance down",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        partial_failures,
        warnings,
    )
    assert parsed is None
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "PERFORMANCE_DOWN: lotus-performance down"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


def test_parse_performance_snapshot_handles_non_dict_period_map():
    partial_failures = []
    warnings = []
    parsed = parse_performance_snapshot(
        (200, {"results_by_period": []}),
        partial_failures,
        warnings,
    )
    assert parsed is None
    assert "PERFORMANCE_SNAPSHOT_INVALID" in warnings


def test_parse_performance_snapshot_falls_back_to_first_period_key():
    partial_failures = []
    warnings = []
    parsed = parse_performance_snapshot(
        (
            200,
            {
                "results_by_period": {
                    "QTD": {"portfolio": {"summary": {"period_return": {"base": 2.2}}}}
                }
            },
        ),
        partial_failures,
        warnings,
    )
    assert parsed is not None
    assert parsed.period == "QTD"
    assert parsed.return_pct == 2.2


def test_parse_performance_snapshot_accepts_workspace_summary_payload():
    partial_failures = []
    warnings = []
    parsed = parse_performance_snapshot(
        (
            200,
            {
                "results_by_period": {
                    "YTD": {
                        "portfolio_twr": {
                            "net": {
                                "summary": {
                                    "period_return": {"base": -0.69},
                                },
                            },
                        },
                        "benchmark": {
                            "net": {
                                "summary": {
                                    "period_return": {"base": 5.1},
                                },
                            },
                        },
                    },
                },
            },
        ),
        partial_failures,
        warnings,
    )
    assert parsed is not None
    assert parsed.period == "YTD"
    assert parsed.return_pct == -0.69
    assert parsed.benchmark_return_pct == 5.1
    assert warnings == []
    assert partial_failures == []


@pytest.mark.parametrize(
    ("result", "warning"),
    [
        (RuntimeError("boom"), "MANAGE_REBALANCE_UNAVAILABLE"),
        (("bad",), "MANAGE_REBALANCE_UNAVAILABLE"),
    ],
)
def test_parse_dpm_snapshot_handles_exception_and_invalid_result_shape(result, warning):
    partial_failures = []
    warnings = []
    parsed = parse_rebalance_snapshot(result, partial_failures, warnings)
    assert parsed is None
    assert warning in warnings
    assert len(partial_failures) == 1


def test_parse_dpm_snapshot_handles_invalid_payload_type():
    partial_failures = []
    warnings = []
    parsed = parse_rebalance_snapshot((200, "bad-payload"), partial_failures, warnings)
    assert parsed is None
    assert partial_failures[0].error_code == "INVALID_UPSTREAM_PAYLOAD"


def test_parse_dpm_snapshot_handles_http_error():
    partial_failures = []
    warnings = []
    parsed = parse_rebalance_snapshot(
        (
            500,
            {
                "detail": {
                    "code": "DPM_DOWN",
                    "message": "dpm down",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        partial_failures,
        warnings,
    )
    assert parsed is None
    assert partial_failures[0].error_code == "HTTP_500"
    assert partial_failures[0].detail == "DPM_DOWN: dpm down"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


def test_parse_dpm_snapshot_with_no_items_returns_not_available():
    parsed = parse_rebalance_snapshot((200, {"items": []}), [], [])
    assert parsed is not None
    assert parsed.status == "NOT_AVAILABLE"


def test_parse_dpm_snapshot_with_datetime_created_at_converts_to_utc():
    created = datetime(2026, 2, 24, 10, 15, tzinfo=UTC)
    parsed = parse_rebalance_snapshot(
        (200, {"items": [{"status": "READY", "created_at": created, "rebalance_run_id": "rr-1"}]}),
        [],
        [],
    )
    assert parsed is not None
    assert parsed.last_rebalance_run_id == "rr-1"
    assert parsed.last_run_at_utc is not None
    assert parsed.last_run_at_utc.endswith("+00:00")


def test_parse_dpm_snapshot_uses_live_shape_supportability_summary():
    parsed = parse_rebalance_snapshot(
        (
            200,
            {
                "items": [
                    {
                        "status": "PENDING_REVIEW",
                        "created_at": "2026-05-06T15:37:05.939203+08:00",
                        "rebalance_run_id": "rr_c09f73d0",
                    }
                ]
            },
        ),
        [],
        [],
        supportability_result=(
            200,
            {
                "store_backend": "POSTGRES",
                "run_count": 82,
                "operation_count": 0,
                "workflow_decision_count": 0,
                "supportability": {
                    "state": "ready",
                    "reason": "supportability_summary_ready",
                    "freshness_bucket": "current",
                    "run_count": 82,
                    "operation_count": 0,
                    "workflow_decision_count": 0,
                },
            },
        ),
    )
    assert parsed is not None
    assert parsed.supportability is not None
    assert parsed.supportability.state == "ready"
    assert parsed.supportability.freshness_bucket == "current"
    assert parsed.supportability.run_count == 82


def test_parse_dpm_snapshot_records_supportability_summary_failure():
    partial_failures = []
    warnings = []
    parsed = parse_rebalance_snapshot(
        (200, {"items": [{"status": "READY"}]}),
        partial_failures,
        warnings,
        supportability_result=(
            503,
            {
                "detail": {
                    "code": "SUPPORTABILITY_DOWN",
                    "message": "summary unavailable",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
    )
    assert parsed is not None
    assert parsed.supportability is None
    assert warnings == ["MANAGE_REBALANCE_SUPPORTABILITY_UNAVAILABLE"]
    assert partial_failures[0].error_code == "SUPPORTABILITY_HTTP_503"
    assert partial_failures[0].detail == "SUPPORTABILITY_DOWN: summary unavailable"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


def test_parse_dpm_snapshot_merges_supportability_counts_from_summary_root():
    parsed = parse_rebalance_snapshot(
        (200, {"items": [{"status": "READY"}]}),
        [],
        [],
        supportability_result=(
            200,
            {
                "run_count": 3,
                "operation_count": 2,
                "workflow_decision_count": 1,
                "supportability": {"state": "ready"},
            },
        ),
    )
    assert parsed is not None
    assert parsed.supportability is not None
    assert parsed.supportability.run_count == 3
    assert parsed.supportability.operation_count == 2
    assert parsed.supportability.workflow_decision_count == 1


def test_parse_dpm_snapshot_preserves_recent_run_error_and_workflow_state():
    parsed = parse_rebalance_snapshot(
        (
            200,
            {
                "items": [
                    {
                        "status": "FAILED",
                        "rebalance_run_id": "rr-1",
                        "created_at": "2026-02-24T00:00:00Z",
                        "error": {"code": "SOURCE_GAP"},
                        "workflow_decision_state": "NEEDS_REVIEW",
                    }
                ]
            },
        ),
        [],
        [],
    )
    assert parsed is not None
    assert parsed.recent_runs[0].error_code == "SOURCE_GAP"
    assert parsed.recent_runs[0].workflow_state == "NEEDS_REVIEW"


def test_extract_current_positions_handles_non_dict_holdings():
    assert extract_current_positions({"sections": []}) == []


def test_extract_current_positions_computes_weight_and_sorts():
    payload = {
        "sections": {
            "positions_baseline": [
                {"security_id": "B", "quantity": 2, "market_value_base": 200.0},
                {"security_id": "A", "quantity": 1, "market_value_base": 100.0},
            ],
            "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
            "instrument_enrichment": [
                {"security_id": "B", "instrument_name": "B Name", "asset_class": "Equity"},
                {"security_id": "A", "instrument_name": "A Name", "asset_class": "Equity"},
            ],
        },
    }
    rows = extract_current_positions(payload)
    assert [row.security_id for row in rows] == ["A", "B"]
    assert rows[0].weight_pct == pytest.approx(10.0)
    assert rows[1].weight_pct == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_load_projected_state_raises_when_positions_unavailable():
    service, pas, _, _ = _build_service()
    pas.positions_status = 503
    pas.positions_payload = {
        "detail": "projection failed",
        "account_number": "ACC-SENSITIVE",
        "raw_positions": [{"security_id": "EQ_1"}],
    }
    with pytest.raises(HTTPException) as exc:
        await service._load_projected_state("sess-1", "corr-1")
    assert exc.value.status_code == 502
    assert exc.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": 503,
        "error_code": "LOTUS_CORE_PROJECTED_POSITIONS_UNAVAILABLE",
        "detail": "projection failed",
    }


@pytest.mark.asyncio
async def test_load_projected_state_raises_when_summary_unavailable():
    service, pas, _, _ = _build_service()
    pas.summary_status = 503
    pas.summary_payload = {"message": "summary failed", "client_name": "Sensitive Client"}
    with pytest.raises(HTTPException) as exc:
        await service._load_projected_state("sess-1", "corr-1")
    assert exc.value.status_code == 502
    assert exc.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": 503,
        "error_code": "LOTUS_CORE_PROJECTED_SUMMARY_UNAVAILABLE",
        "detail": "summary failed",
    }


@pytest.mark.asyncio
async def test_load_projected_state_skips_non_dict_rows():
    service, pas, _, _ = _build_service()
    pas.positions_payload = {"positions": ["bad", {"security_id": "EQ_1", "proposed_quantity": 1}]}
    pas.summary_payload = {
        "total_baseline_positions": 1,
        "total_proposed_positions": 1,
        "net_delta_quantity": 1.0,
    }
    rows, summary = await service._load_projected_state("sess-1", "corr-1")
    assert len(rows) == 1
    assert rows[0].security_id == "EQ_1"
    assert summary.net_delta_quantity == 1.0


def test_parse_projected_state_defaults_missing_fields_and_skips_invalid_rows():
    rows, summary = parse_projected_state(
        positions_payload={
            "positions": [
                "bad",
                {
                    "security_id": "EQ_1",
                    "proposed_quantity": 1.23456,
                    "delta_quantity": 1.23456,
                },
            ]
        },
        summary_payload={"net_delta_quantity": 1.23456},
    )

    assert len(rows) == 1
    assert rows[0].security_id == "EQ_1"
    assert rows[0].instrument_name == "EQ_1"
    assert rows[0].asset_class is None
    assert rows[0].baseline_quantity == pytest.approx(0.0)
    assert rows[0].proposed_quantity == pytest.approx(1.23456)
    assert rows[0].delta_quantity == pytest.approx(1.23456)
    assert summary.total_baseline_positions == 0
    assert summary.total_proposed_positions == 0
    assert summary.net_delta_quantity == pytest.approx(1.23456)


def test_parse_projected_state_handles_non_list_positions_payload():
    rows, summary = parse_projected_state(
        positions_payload={"positions": {"security_id": "EQ_1"}},
        summary_payload={
            "total_baseline_positions": 2,
            "total_proposed_positions": 3,
            "net_delta_quantity": -4.0,
        },
    )

    assert rows == []
    assert summary.total_baseline_positions == 2
    assert summary.total_proposed_positions == 3
    assert summary.net_delta_quantity == pytest.approx(-4.0)


@pytest.mark.asyncio
async def test_create_sandbox_session_raises_on_pas_error():
    service, pas, _, _ = _build_service()
    pas.create_status = 500
    pas.create_payload = {
        "error": "session create failed",
        "session": {"session_id": "sess-sensitive"},
    }
    with pytest.raises(HTTPException) as exc:
        await service.create_sandbox_session("P1", "corr-1", created_by=None, ttl_hours=1)
    assert exc.value.status_code == 502
    assert exc.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": 500,
        "error_code": "LOTUS_CORE_SIMULATION_SESSION_CREATE_FAILED",
        "detail": "session create failed",
    }


@pytest.mark.asyncio
async def test_apply_sandbox_changes_raises_on_pas_error():
    service, pas, _, _ = _build_service()
    pas.change_status = 500
    pas.change_payload = {
        "detail": {"code": "change_failed", "message": "change apply failed"},
        "changes": [{"security_id": "EQ_SENSITIVE"}],
    }
    with pytest.raises(HTTPException) as exc:
        await service.apply_sandbox_changes(
            portfolio_id="P1",
            session_id="sess-1",
            correlation_id="corr-1",
            changes=[{"security_id": "EQ_1"}],
            evaluate_policy=False,
        )
    assert exc.value.status_code == 502
    assert exc.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": 500,
        "error_code": "LOTUS_CORE_SIMULATION_CHANGE_APPLY_FAILED",
        "detail": "change_failed: change apply failed",
    }


@pytest.mark.asyncio
async def test_apply_sandbox_changes_without_policy_evaluation():
    service, _, _, _ = _build_service()
    response = await service.apply_sandbox_changes(
        portfolio_id="P1",
        session_id="sess-1",
        correlation_id="corr-1",
        changes=[{"security_id": "EQ_1"}],
        evaluate_policy=False,
    )
    assert response.policy_feedback is None
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_get_workbench_analytics_degrades_when_performance_snapshot_unavailable():
    service, _, performance, _ = _build_service()
    performance.snapshot_status = 503
    performance.snapshot_payload = {"detail": "lotus-performance unavailable"}
    response = await service.get_workbench_analytics(
        portfolio_id="P1",
        correlation_id="corr-1",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL",
        session_id=None,
    )
    assert response.portfolio_return_pct is None
    assert response.allocation_buckets == []
    assert "PERFORMANCE_SNAPSHOT_UNAVAILABLE" in response.warnings
    assert any(
        failure.source_service == "lotus-performance" and failure.error_code == "HTTP_503"
        for failure in response.partial_failures
    )


@pytest.mark.asyncio
async def test_get_workbench_analytics_builds_security_grouping_without_stale_pa_route():
    service, core, performance, _ = _build_service()
    core.core_payload = {
        "as_of_date": "2026-02-24",
        "sections": {
            "positions_baseline": [
                {
                    "security_id": "EQ_1",
                    "quantity": 10.0,
                    "market_value_base": 100.0,
                    "weight": 1.0,
                }
            ],
            "portfolio_totals": {"baseline_total_market_value_base": 100.0},
            "instrument_enrichment": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                }
            ],
        },
    }
    performance.snapshot_payload = {
        "results_by_period": {"YTD": {"portfolio": {"summary": {"period_return": {"base": 1.0}}}}}
    }
    response = await service.get_workbench_analytics(
        portfolio_id="P1",
        correlation_id="corr-1",
        period="YTD",
        group_by="SECURITY",
        benchmark_code="MODEL",
        session_id=None,
    )
    assert [bucket.bucket_key for bucket in response.allocation_buckets] == ["EQ_1"]
    assert response.allocation_buckets[0].current_quantity == pytest.approx(10.0)
    assert response.allocation_buckets[0].proposed_quantity == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_get_workbench_analytics_ignores_legacy_risk_proxy_payload():
    service, _, performance, _ = _build_service()
    performance.analytics_payload = {
        "allocationBuckets": [],
        "topChanges": [],
        "riskProxy": {"hhiCurrent": 9999.0, "hhiProposed": 9999.0, "hhiDelta": 0.0},
        "portfolioReturnPct": 1.0,
        "benchmarkReturnPct": 0.8,
        "activeReturnPct": 0.2,
    }
    response = await service.get_workbench_analytics(
        portfolio_id="P1",
        correlation_id="corr-1",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL",
        session_id=None,
    )
    assert "risk_proxy" not in response.model_dump()
    assert "RISK_BFF_PENDING" in response.warnings
    assert [
        failure
        for failure in response.partial_failures
        if failure.source_service == "risk" and failure.error_code == "RISK_BFF_NOT_IMPLEMENTED"
    ]


@pytest.mark.asyncio
async def test_evaluate_policy_feedback_handles_dpm_failure():
    service, _, _, dpm = _build_service()
    dpm.simulate_status = 503
    dpm.simulate_payload = {
        "detail": {
            "code": "POLICY_ENGINE_DOWN",
            "message": "policy engine down",
            "debug_payload": {
                "client_name": "Private Client",
                "token": "secret-token",
            },
        }
    }
    warnings: list[str] = []
    partial_failures = []
    feedback = await service._evaluate_policy_feedback(
        portfolio_id="P1",
        session_id="sess-1",
        session_version=2,
        projected_positions=[],
        correlation_id="corr-1",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    assert feedback.status == "UNAVAILABLE"
    assert warnings == ["ADVISE_PROPOSAL_SIMULATION_UNAVAILABLE"]
    assert partial_failures[0].source_service == "lotus-advise"
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "POLICY_ENGINE_DOWN: policy engine down"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


@pytest.mark.asyncio
async def test_evaluate_policy_feedback_uses_status_when_gate_decision_missing():
    service, _, _, dpm = _build_service()
    dpm.simulate_payload = {"status": "PASS"}
    feedback = await service._evaluate_policy_feedback(
        portfolio_id="P1",
        session_id="sess-1",
        session_version=3,
        projected_positions=[],
        correlation_id="corr-1",
        warnings=[],
        partial_failures=[],
    )
    assert feedback.status == "PASS"


def test_build_policy_simulation_payload_filters_non_positive_positions():
    payload = build_policy_simulation_payload(
        portfolio_id="P1",
        base_currency="USD",
        projected_positions=[
            WorkbenchProjectedPositionView(
                security_id="EQ_1",
                instrument_name="Equity 1",
                asset_class="Equity",
                baseline_quantity=1.0,
                proposed_quantity=2.34567,
                delta_quantity=1.34567,
            ),
            WorkbenchProjectedPositionView(
                security_id="CASH_1",
                instrument_name="Cash 1",
                asset_class="Cash",
                baseline_quantity=1.0,
                proposed_quantity=0.0,
                delta_quantity=-1.0,
            ),
        ],
    )

    assert payload["portfolio_snapshot"]["portfolio_id"] == "P1"
    assert payload["portfolio_snapshot"]["base_currency"] == "USD"
    assert payload["portfolio_snapshot"]["positions"] == [
        {"instrument_id": "EQ_1", "quantity": "2.3457"}
    ]
    assert payload["options"]["proposal_block_negative_cash"] is True


def test_build_policy_idempotency_key_uses_session_version():
    assert (
        build_policy_idempotency_key(session_id="sess-1", session_version=3) == "sandbox-sess-1-3"
    )


def test_parse_policy_feedback_success_prefers_gate_decision():
    feedback = parse_policy_feedback_success(
        {"status": "COMPLETED", "gate_decision": {"status": "PASS", "reason_code": "OK"}}
    )
    assert feedback.status == "PASS"
    assert feedback.detail == "OK"


def test_parse_policy_feedback_unavailable_omits_non_dict_raw_payload():
    feedback = parse_policy_feedback_unavailable("upstream unavailable")
    assert feedback.status == "UNAVAILABLE"
    assert feedback.raw is None


def test_extract_current_positions_returns_empty_when_by_asset_class_not_dict():
    payload = {"sections": {"positions_baseline": [], "instrument_enrichment": []}}
    assert extract_current_positions(payload) == []


def test_extract_current_positions_skips_invalid_item_shapes():
    payload = {
        "sections": {
            "positions_baseline": ["bad", {"security_id": "EQ_1", "quantity": 1}],
            "portfolio_totals": {"baseline_total_market_value_base": 100.0},
            "instrument_enrichment": [{"security_id": "EQ_1", "instrument_name": "EQ 1"}],
        },
    }
    rows = extract_current_positions(payload)
    assert len(rows) == 1
    assert rows[0].security_id == "EQ_1"


def test_extract_current_positions_skips_asset_class_with_non_list_items():
    payload = {"sections": {"positions_baseline": {"security_id": "EQ_1"}}}
    rows = extract_current_positions(payload)
    assert rows == []


def test_parse_lotus_core_snapshot_handles_non_dict_overview_and_holdings_shapes():
    portfolio, overview, _ = parse_lotus_core_snapshot(
        fallback_portfolio_id="P1",
        portfolio_payload={"portfolio_id": "P1"},
        snapshot_payload={"sections": []},
        fallback_as_of_date="2026-02-24",
    )
    assert portfolio.portfolio_id == "P1"
    assert overview.market_value_base == 0.0
    assert overview.position_count == 0


def test_parse_performance_snapshot_empty_results_by_period_returns_none():
    result = parse_performance_snapshot((200, {"results_by_period": {}}), [], [])
    assert result is None


def test_parse_performance_snapshot_non_dict_period_payload_returns_none():
    result = parse_performance_snapshot((200, {"results_by_period": {"YTD": []}}), [], [])
    assert result is None


def test_parse_performance_snapshot_none_period_key_returns_none():
    result = parse_performance_snapshot(
        (
            200,
            {
                "results_by_period": {
                    None: {"portfolio": {"summary": {"period_return": {"base": 1.0}}}}
                }
            },
        ),
        [],
        [],
    )
    assert result is None


def test_parse_dpm_snapshot_non_dict_latest_returns_not_available():
    result = parse_rebalance_snapshot((200, {"items": ["bad"]}), [], [])
    assert result is not None
    assert result.status == "NOT_AVAILABLE"


def test_parse_dpm_snapshot_without_created_at_keeps_last_run_null():
    result = parse_rebalance_snapshot((200, {"items": [{"status": "READY"}]}), [], [])
    assert result is not None
    assert result.last_run_at_utc is None


def test_build_workbench_allocation_buckets_merges_projected_and_unchanged_rows():
    current_positions = [
        WorkbenchPositionView(
            security_id="EQ_1",
            instrument_name="Equity 1",
            asset_class="Equity",
            quantity=10.0,
            market_value_base=100.0,
            weight=1.0,
        ),
        WorkbenchPositionView(
            security_id="BOND_1",
            instrument_name="Bond 1",
            asset_class="Fixed Income",
            quantity=30.0,
            market_value_base=300.0,
            weight=1.0,
        ),
    ]
    projected_positions = [
        WorkbenchProjectedPositionView(
            security_id="EQ_1",
            instrument_name="Equity 1",
            asset_class="Equity",
            baseline_quantity=10.0,
            proposed_quantity=20.0,
            delta_quantity=10.0,
        )
    ]

    buckets = build_workbench_allocation_buckets(
        group_by="ASSET_CLASS",
        current_positions=current_positions,
        projected_positions=projected_positions,
    )

    assert [bucket.bucket_key for bucket in buckets] == ["EQUITY", "FIXED INCOME"]
    assert buckets[0].current_quantity == pytest.approx(10.0)
    assert buckets[0].proposed_quantity == pytest.approx(20.0)
    assert buckets[0].current_weight_pct == pytest.approx(25.0)
    assert buckets[0].proposed_weight_pct == pytest.approx(40.0)
    assert buckets[1].current_quantity == pytest.approx(30.0)
    assert buckets[1].proposed_quantity == pytest.approx(30.0)


def test_build_workbench_top_changes_orders_limits_and_skips_unchanged_rows():
    projected_positions = [
        WorkbenchProjectedPositionView(
            security_id=f"EQ_{index}",
            instrument_name=f"Equity {index}",
            asset_class="Equity",
            baseline_quantity=100.0,
            proposed_quantity=100.0 + index,
            delta_quantity=float(index),
        )
        for index in range(12)
    ]
    projected_positions.append(
        WorkbenchProjectedPositionView(
            security_id="BOND_REDUCE",
            instrument_name="Bond Reduce",
            asset_class="Fixed Income",
            baseline_quantity=50.0,
            proposed_quantity=25.0,
            delta_quantity=-25.0,
        )
    )

    top_changes = build_workbench_top_changes(projected_positions)

    assert len(top_changes) == 10
    assert top_changes[0].security_id == "BOND_REDUCE"
    assert top_changes[0].direction == "DECREASE"
    assert "EQ_0" not in {change.security_id for change in top_changes}
    assert top_changes[1].security_id == "EQ_11"
    assert top_changes[1].direction == "INCREASE"


def test_with_controlled_risk_bff_gap_appends_bounded_failure_once_per_projection():
    portfolio_360 = WorkbenchPortfolio360Response(
        correlation_id="corr-1",
        contract_version="v1",
        as_of_date="2026-02-24",
        portfolio=WorkbenchPortfolioSummary(portfolio_id="P1", base_currency="USD"),
        overview=WorkbenchOverviewSummary(
            market_value_base=100.0,
            cash_weight_pct=10.0,
            position_count=1,
        ),
        warnings=["RISK_BFF_PENDING"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code="HTTP_503",
                detail="performance unavailable",
            )
        ],
    )

    projected = with_controlled_risk_bff_gap(portfolio_360)

    assert projected is not portfolio_360
    assert projected.warnings == ["RISK_BFF_PENDING"]
    assert [failure.source_service for failure in projected.partial_failures] == [
        "lotus-performance",
        "risk",
    ]
    assert projected.partial_failures[-1].error_code == "RISK_BFF_NOT_IMPLEMENTED"


def test_build_workbench_return_metrics_quantizes_active_return():
    portfolio_return, benchmark_return, active_return = build_workbench_return_metrics(
        WorkbenchPerformanceSnapshot(
            period="YTD",
            return_pct=1.23456,
            benchmark_return_pct=0.11111,
        )
    )

    assert portfolio_return == pytest.approx(1.23456)
    assert benchmark_return == pytest.approx(0.11111)
    assert active_return == pytest.approx(1.12345)


def test_build_workbench_return_metrics_handles_missing_performance_snapshot():
    assert build_workbench_return_metrics(None) == (None, None, None)


@pytest.mark.parametrize(
    ("group_by", "expected"),
    [
        ("ASSET_CLASS", "UNCLASSIFIED"),
        ("SECURITY", "SEC_1"),
        ("INSTRUMENT", "Instrument 1"),
        ("UNKNOWN", "UNCLASSIFIED"),
    ],
)
def test_workbench_position_bucket_key_supports_expected_groupings(group_by, expected):
    assert (
        workbench_position_bucket_key(
            group_by=group_by,
            security_id="SEC_1",
            instrument_name="Instrument 1",
            asset_class=None,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("delta_quantity", "expected"),
    [(1.0, "INCREASE"), (-1.0, "DECREASE"), (0.0, "UNCHANGED")],
)
def test_quantity_change_direction(delta_quantity, expected):
    assert quantity_change_direction(delta_quantity) == expected


@pytest.mark.asyncio
async def test_workbench_analytics_reports_controlled_risk_gap_until_risk_bff_exists():
    service, _, performance, _ = _build_service()
    performance.analytics_payload = {
        "allocationBuckets": [],
        "topChanges": [],
        "riskProxy": {"hhiCurrent": 100.0, "hhiProposed": 100.0, "hhiDelta": 0.0},
        "portfolioReturnPct": 1.0,
        "benchmarkReturnPct": 0.8,
        "activeReturnPct": 0.2,
    }
    response = await service.get_workbench_analytics(
        portfolio_id="P1",
        correlation_id="corr-1",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL_60_40",
        session_id=None,
    )
    assert "risk_proxy" not in response.model_dump()
    assert "RISK_BFF_PENDING" in response.warnings
    assert response.partial_failures[-1].source_service == "risk"
    assert response.partial_failures[-1].error_code == "RISK_BFF_NOT_IMPLEMENTED"
