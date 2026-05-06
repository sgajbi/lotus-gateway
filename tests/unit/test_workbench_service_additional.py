from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

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
        service._raise_for_lotus_core_error(500, {"detail": "downstream unavailable"})
    assert exc.value.status_code == 502
    assert "downstream unavailable" in str(exc.value.detail)


def test_parse_lotus_core_snapshot_invalid_structure_raises():
    service, _, _, _ = _build_service()
    with pytest.raises(HTTPException) as exc:
        service._parse_lotus_core_snapshot("P1", [], {}, "2026-02-24")
    assert exc.value.status_code == 502


def test_parse_lotus_core_snapshot_uses_fallback_defaults():
    service, _, _, _ = _build_service()
    portfolio, overview, as_of_date = service._parse_lotus_core_snapshot(
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
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_performance_snapshot(result, partial_failures, warnings)
    assert parsed is None
    assert warning in warnings
    assert len(partial_failures) == 1


def test_parse_performance_snapshot_handles_invalid_payload_types():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_performance_snapshot((200, "bad-payload"), partial_failures, warnings)
    assert parsed is None
    assert "PERFORMANCE_SNAPSHOT_UNAVAILABLE" in warnings


def test_parse_performance_snapshot_handles_http_error_payload():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_performance_snapshot(
        (503, {"detail": "lotus-performance down"}),
        partial_failures,
        warnings,
    )
    assert parsed is None
    assert partial_failures[0].error_code == "HTTP_503"


def test_parse_performance_snapshot_handles_non_dict_period_map():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_performance_snapshot(
        (200, {"results_by_period": []}),
        partial_failures,
        warnings,
    )
    assert parsed is None
    assert "PERFORMANCE_SNAPSHOT_INVALID" in warnings


def test_parse_performance_snapshot_falls_back_to_first_period_key():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_performance_snapshot(
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


@pytest.mark.parametrize(
    ("result", "warning"),
    [
        (RuntimeError("boom"), "MANAGE_REBALANCE_UNAVAILABLE"),
        (("bad",), "MANAGE_REBALANCE_UNAVAILABLE"),
    ],
)
def test_parse_dpm_snapshot_handles_exception_and_invalid_result_shape(result, warning):
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_dpm_snapshot(result, partial_failures, warnings)
    assert parsed is None
    assert warning in warnings
    assert len(partial_failures) == 1


def test_parse_dpm_snapshot_handles_invalid_payload_type():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_dpm_snapshot((200, "bad-payload"), partial_failures, warnings)
    assert parsed is None
    assert partial_failures[0].error_code == "INVALID_UPSTREAM_PAYLOAD"


def test_parse_dpm_snapshot_handles_http_error():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_dpm_snapshot((500, {"detail": "dpm down"}), partial_failures, warnings)
    assert parsed is None
    assert partial_failures[0].error_code == "HTTP_500"


def test_parse_dpm_snapshot_with_no_items_returns_not_available():
    service, _, _, _ = _build_service()
    parsed = service._parse_dpm_snapshot((200, {"items": []}), [], [])
    assert parsed is not None
    assert parsed.status == "NOT_AVAILABLE"


def test_parse_dpm_snapshot_with_datetime_created_at_converts_to_utc():
    service, _, _, _ = _build_service()
    created = datetime(2026, 2, 24, 10, 15, tzinfo=UTC)
    parsed = service._parse_dpm_snapshot(
        (200, {"items": [{"status": "READY", "created_at": created, "rebalance_run_id": "rr-1"}]}),
        [],
        [],
    )
    assert parsed is not None
    assert parsed.last_rebalance_run_id == "rr-1"
    assert parsed.last_run_at_utc is not None
    assert parsed.last_run_at_utc.endswith("+00:00")


def test_parse_dpm_snapshot_uses_live_shape_supportability_summary():
    service, _, _, _ = _build_service()
    parsed = service._parse_dpm_snapshot(
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


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"valuation": {"market_value_base": 100}}, 100.0),
        ({"valuation": {"market_value": 101}}, 101.0),
        ({"current_value_base": 102}, 102.0),
        ({"value_base": 103}, 103.0),
        ({"valuation": {"market_value_base": "bad"}}, None),
    ],
)
def test_parse_position_market_value_variants(payload, expected):
    service, _, _, _ = _build_service()
    assert service._parse_position_market_value(payload) == expected


def test_extract_current_positions_handles_non_dict_holdings():
    service, _, _, _ = _build_service()
    assert service._extract_current_positions({"sections": []}) == []


def test_extract_current_positions_computes_weight_and_sorts():
    service, _, _, _ = _build_service()
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
    rows = service._extract_current_positions(payload)
    assert [row.security_id for row in rows] == ["A", "B"]
    assert rows[0].weight_pct == pytest.approx(10.0)
    assert rows[1].weight_pct == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_load_projected_state_raises_when_positions_unavailable():
    service, pas, _, _ = _build_service()
    pas.positions_status = 503
    with pytest.raises(HTTPException) as exc:
        await service._load_projected_state("sess-1", "corr-1")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_load_projected_state_raises_when_summary_unavailable():
    service, pas, _, _ = _build_service()
    pas.summary_status = 503
    with pytest.raises(HTTPException) as exc:
        await service._load_projected_state("sess-1", "corr-1")
    assert exc.value.status_code == 502


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


@pytest.mark.asyncio
async def test_create_sandbox_session_raises_on_pas_error():
    service, pas, _, _ = _build_service()
    pas.create_status = 500
    with pytest.raises(HTTPException) as exc:
        await service.create_sandbox_session("P1", "corr-1", created_by=None, ttl_hours=1)
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_apply_sandbox_changes_raises_on_pas_error():
    service, pas, _, _ = _build_service()
    pas.change_status = 500
    with pytest.raises(HTTPException) as exc:
        await service.apply_sandbox_changes(
            portfolio_id="P1",
            session_id="sess-1",
            correlation_id="corr-1",
            changes=[{"security_id": "EQ_1"}],
            evaluate_policy=False,
        )
    assert exc.value.status_code == 502


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
async def test_get_workbench_analytics_raises_on_pa_error():
    service, _, performance, _ = _build_service()
    performance.analytics_status = 503
    with pytest.raises(HTTPException) as exc:
        await service.get_workbench_analytics(
            portfolio_id="P1",
            correlation_id="corr-1",
            period="YTD",
            group_by="ASSET_CLASS",
            benchmark_code="MODEL",
            session_id=None,
        )
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_get_workbench_analytics_raises_on_invalid_payload_shape():
    service, _, performance, _ = _build_service()
    performance.analytics_payload = {
        "allocationBuckets": [{"bucketKey": "EQ", "currentQuantity": "bad-number"}],
        "topChanges": [],
        "riskProxy": {},
    }
    with pytest.raises(HTTPException) as exc:
        await service.get_workbench_analytics(
            portfolio_id="P1",
            correlation_id="corr-1",
            period="YTD",
            group_by="ASSET_CLASS",
            benchmark_code="MODEL",
            session_id=None,
        )
    assert exc.value.status_code == 502
    assert "Invalid lotus-performance workbench analytics payload" in str(exc.value.detail)


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
    dpm.simulate_payload = {"detail": "policy engine down"}
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


def test_extract_current_positions_returns_empty_when_by_asset_class_not_dict():
    service, _, _, _ = _build_service()
    payload = {"sections": {"positions_baseline": [], "instrument_enrichment": []}}
    assert service._extract_current_positions(payload) == []


def test_extract_current_positions_skips_invalid_item_shapes():
    service, _, _, _ = _build_service()
    payload = {
        "sections": {
            "positions_baseline": ["bad", {"security_id": "EQ_1", "quantity": 1}],
            "portfolio_totals": {"baseline_total_market_value_base": 100.0},
            "instrument_enrichment": [{"security_id": "EQ_1", "instrument_name": "EQ 1"}],
        },
    }
    rows = service._extract_current_positions(payload)
    assert len(rows) == 1
    assert rows[0].security_id == "EQ_1"


def test_extract_current_positions_skips_asset_class_with_non_list_items():
    service, _, _, _ = _build_service()
    payload = {"sections": {"positions_baseline": {"security_id": "EQ_1"}}}
    rows = service._extract_current_positions(payload)
    assert rows == []


def test_parse_position_market_value_skips_non_numeric_in_flat_keys():
    service, _, _, _ = _build_service()
    assert (
        service._parse_position_market_value({"market_value_base": "bad", "value_base": "bad"})
        is None
    )


def test_parse_lotus_core_snapshot_handles_non_dict_overview_and_holdings_shapes():
    service, _, _, _ = _build_service()
    portfolio, overview, _ = service._parse_lotus_core_snapshot(
        fallback_portfolio_id="P1",
        portfolio_payload={"portfolio_id": "P1"},
        snapshot_payload={"sections": []},
        fallback_as_of_date="2026-02-24",
    )
    assert portfolio.portfolio_id == "P1"
    assert overview.market_value_base == 0.0
    assert overview.position_count == 0


def test_parse_performance_snapshot_empty_results_by_period_returns_none():
    service, _, _, _ = _build_service()
    result = service._parse_performance_snapshot((200, {"results_by_period": {}}), [], [])
    assert result is None


def test_parse_performance_snapshot_non_dict_period_payload_returns_none():
    service, _, _, _ = _build_service()
    result = service._parse_performance_snapshot((200, {"results_by_period": {"YTD": []}}), [], [])
    assert result is None


def test_parse_performance_snapshot_none_period_key_returns_none():
    service, _, _, _ = _build_service()
    result = service._parse_performance_snapshot(
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
    service, _, _, _ = _build_service()
    result = service._parse_dpm_snapshot((200, {"items": ["bad"]}), [], [])
    assert result is not None
    assert result.status == "NOT_AVAILABLE"


def test_parse_dpm_snapshot_without_created_at_keeps_last_run_null():
    service, _, _, _ = _build_service()
    result = service._parse_dpm_snapshot((200, {"items": [{"status": "READY"}]}), [], [])
    assert result is not None
    assert result.last_run_at_utc is None


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
