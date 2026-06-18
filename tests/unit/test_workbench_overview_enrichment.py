import pytest

from app.services.workbench_overview_enrichment import (
    load_workbench_overview_enrichment,
    resolve_workbench_performance_snapshot_end_date,
)


class _CoreClient:
    def __init__(self, *, performance_end_date: str = "2026-06-17", status_code: int = 200):
        self.performance_end_date = performance_end_date
        self.status_code = status_code
        self.reference_calls = 0

    async def get_portfolio_analytics_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ):
        self.reference_calls += 1
        return self.status_code, {"performance_end_date": self.performance_end_date}


class _PerformanceClient:
    def __init__(self):
        self.workspace_summary_calls = 0
        self.last_report_end_date: str | None = None
        self.last_benchmark_id: str | None = None

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
        self.workspace_summary_calls += 1
        self.last_report_end_date = report_end_date
        self.last_benchmark_id = benchmark_id
        return (
            200,
            {
                "results_by_period": {
                    "YTD": {
                        "portfolio": {"summary": {"period_return": {"base": 3.2}}},
                        "benchmark": {"summary": {"period_return": {"base": 2.1}}},
                    }
                }
            },
        )


class _ManageClient:
    def __init__(self):
        self.list_runs_calls = 0
        self.supportability_summary_calls = 0

    async def list_runs(self, *, params: dict, correlation_id: str):
        self.list_runs_calls += 1
        return (
            200,
            {
                "items": [
                    {
                        "rebalance_run_id": "run-1",
                        "status": "READY",
                        "created_at": "2026-06-17T10:00:00Z",
                    }
                ]
            },
        )

    async def get_supportability_summary(self, *, correlation_id: str):
        self.supportability_summary_calls += 1
        return (
            200,
            {
                "supportability": {
                    "feature_key": "manage.observability.action_register_supportability",
                    "state": "supported",
                    "run_count": 5,
                }
            },
        )


@pytest.mark.asyncio
async def test_resolve_workbench_performance_snapshot_end_date_clamps_canonical_portfolio():
    core_client = _CoreClient(performance_end_date="2026-06-17")

    report_end_date = await resolve_workbench_performance_snapshot_end_date(
        core_client=core_client,
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        as_of_date="2026-06-17",
        correlation_id="corr-1",
    )

    assert report_end_date == "2026-04-10"


@pytest.mark.asyncio
async def test_load_workbench_overview_enrichment_skips_downstream_calls_when_excluded():
    core_client = _CoreClient()
    performance_client = _PerformanceClient()
    manage_client = _ManageClient()

    (
        performance_snapshot,
        rebalance_snapshot,
        warnings,
        partial_failures,
    ) = await load_workbench_overview_enrichment(
        core_client=core_client,
        analytics_client=performance_client,
        dpm_client=manage_client,
        portfolio_id="PF_1001",
        as_of_date="2026-06-17",
        correlation_id="corr-1",
        include_performance_snapshot=False,
        include_rebalance_snapshot=False,
    )

    assert performance_snapshot is None
    assert rebalance_snapshot is None
    assert warnings == []
    assert partial_failures == []
    assert core_client.reference_calls == 0
    assert performance_client.workspace_summary_calls == 0
    assert manage_client.list_runs_calls == 0
    assert manage_client.supportability_summary_calls == 0


@pytest.mark.asyncio
async def test_load_workbench_overview_enrichment_preserves_snapshot_routing():
    core_client = _CoreClient(performance_end_date="2026-05-31")
    performance_client = _PerformanceClient()
    manage_client = _ManageClient()

    (
        performance_snapshot,
        rebalance_snapshot,
        warnings,
        partial_failures,
    ) = await load_workbench_overview_enrichment(
        core_client=core_client,
        analytics_client=performance_client,
        dpm_client=manage_client,
        portfolio_id="PF_1001",
        as_of_date="2026-06-17",
        correlation_id="corr-1",
        include_performance_snapshot=True,
        include_rebalance_snapshot=True,
        benchmark_code="MODEL_60_40",
    )

    assert performance_snapshot is not None
    assert performance_snapshot.return_pct == 3.2
    assert performance_snapshot.benchmark_return_pct == 2.1
    assert rebalance_snapshot is not None
    assert rebalance_snapshot.status == "READY"
    assert rebalance_snapshot.supportability is not None
    assert rebalance_snapshot.supportability.state == "supported"
    assert warnings == []
    assert partial_failures == []
    assert performance_client.last_report_end_date == "2026-05-31"
    assert performance_client.last_benchmark_id == "MODEL_60_40"
    assert manage_client.list_runs_calls == 1
    assert manage_client.supportability_summary_calls == 1
