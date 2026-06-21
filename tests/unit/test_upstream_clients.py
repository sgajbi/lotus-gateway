import json
import logging

import httpx
import pytest

from app.clients.advise_client import AdviseClient
from app.clients.archive_client import ArchiveClient
from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.lotus_core_transaction_params import build_portfolio_transaction_query_params
from app.clients.reporting_client import ReportingClient
from app.middleware.correlation import trace_id_var


class _FakeAsyncClient:
    responses: list[httpx.Response] = []
    calls: list[dict] = []

    def __init__(self, timeout: float, **_: object):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        self.calls.append(
            {"method": "GET", "url": url, "params": params or {}, "headers": headers or {}}
        )
        return self._next_response()

    async def post(self, url, json=None, data=None, files=None, params=None, headers=None):
        self.calls.append(
            {
                "method": "POST",
                "url": url,
                "params": params or {},
                "json": json,
                "data": data,
                "files": files,
                "headers": headers or {},
            }
        )
        return self._next_response()

    async def put(self, url, json=None, headers=None):
        self.calls.append(
            {
                "method": "PUT",
                "url": url,
                "json": json,
                "headers": headers or {},
            }
        )
        return self._next_response()

    @classmethod
    def _next_response(cls) -> httpx.Response:
        if not cls.responses:
            raise AssertionError("No queued response available.")
        return cls.responses.pop(0)

    @classmethod
    def queue_json(cls, status_code: int, payload: dict | list):
        cls.responses.append(
            httpx.Response(
                status_code=status_code,
                content=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                request=httpx.Request("GET", "http://test"),
            )
        )

    @classmethod
    def queue_text(cls, status_code: int, text: str):
        cls.responses.append(
            httpx.Response(
                status_code=status_code,
                content=text.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                request=httpx.Request("GET", "http://test"),
            )
        )

    @classmethod
    def queue_bytes(cls, status_code: int, content: bytes, headers: dict[str, str] | None = None):
        cls.responses.append(
            httpx.Response(
                status_code=status_code,
                content=content,
                headers=headers or {},
                request=httpx.Request("GET", "http://test"),
            )
        )


@pytest.fixture(autouse=True)
def _patch_async_client(monkeypatch):
    _FakeAsyncClient.responses = []
    _FakeAsyncClient.calls = []
    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)


def _fanout_records(records, *, service: str):
    return [
        record
        for record in records
        if record.name == "analytics_ui.gateway"
        and record.message
        in {"gateway.analytics.fanout.completed", "gateway.analytics.fanout.degraded"}
        and record.extra_fields["service"] == service
    ]


@pytest.mark.asyncio
async def test_lotus_analytics_client_calls_and_payload_handling():
    client = LotusAnalyticsClient(base_url="http://lotus-performance", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "lotus-performance"})
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 2.1}}}}
            }
        },
    )
    status_one, payload_one = await client.get_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-1",
    )
    status_two, payload_two = await client.get_stateful_twr(
        portfolio_id="P1",
        report_end_date="2026-02-24",
        period="YTD",
        correlation_id="corr-1",
    )

    assert status_one == 200
    assert payload_one["sourceService"] == "lotus-performance"
    assert status_two == 200
    assert (
        payload_two["results_by_period"]["YTD"]["portfolio"]["summary"]["period_return"]["base"]
        == 2.1
    )
    assert _FakeAsyncClient.calls[0]["url"] == "http://lotus-performance/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert _FakeAsyncClient.calls[1]["url"] == "http://lotus-performance/performance/twr"
    assert _FakeAsyncClient.calls[1]["json"]["portfolio_id"] == "P1"
    assert _FakeAsyncClient.calls[1]["json"]["report_end_date"] == "2026-02-24"
    assert _FakeAsyncClient.calls[1]["json"]["stateful_input"] == {}


@pytest.mark.asyncio
async def test_lotus_analytics_client_performance_workspace_requests_use_owned_contract_keys():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        202,
        {
            "result_path": "/jobs/twr-1/result",
        },
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 5.2}}}}
            }
        },
    )
    _FakeAsyncClient.queue_json(200, {"money_weighted_return": 4.1, "mwr_annualized": 4.1})
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {
                    "summary": {
                        "portfolio_contribution": 5.2,
                        "coverage_mv_pct": 99.2,
                        "weighting_scheme": "average_weight",
                    },
                    "total_portfolio_return": 5.2,
                    "levels": [],
                }
            }
        },
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "model": "BF",
            "linking": "carino",
            "results_by_period": {
                "YTD": {
                    "reconciliation": {
                        "total_active_return": 0.7,
                        "sum_of_effects": 0.69,
                        "residual": 0.01,
                    },
                    "levels": [],
                }
            },
        },
    )

    twr_status, twr_payload = await client.get_twr_analytics(
        portfolio_id="P1",
        report_end_date="2026-02-24",
        report_start_date="2026-01-01",
        period="YTD",
        metric_basis="NET",
        benchmark_id="MODEL_60_40",
        correlation_id="corr-performance",
    )
    mwr_status, _ = await client.get_mwr_analytics(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        window_start_date="2026-01-01",
        correlation_id="corr-performance",
    )
    contribution_status, _ = await client.get_contribution_analytics(
        portfolio_id="P1",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        period="YTD",
        metric_basis="NET",
        dimension="asset_class",
        correlation_id="corr-performance",
    )
    attribution_status, _ = await client.get_attribution_analytics(
        portfolio_id="P1",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        period="YTD",
        metric_basis="GROSS",
        benchmark_id="MODEL_60_40",
        dimension="sector",
        correlation_id="corr-performance",
    )

    assert twr_status == 200
    assert (
        twr_payload["results_by_period"]["YTD"]["portfolio"]["summary"]["period_return"]["base"]
        == 5.2
    )
    assert mwr_status == 200
    assert contribution_status == 200
    assert attribution_status == 200

    twr_post = _FakeAsyncClient.calls[0]
    twr_poll = _FakeAsyncClient.calls[1]
    mwr_post = _FakeAsyncClient.calls[2]
    contribution_post = _FakeAsyncClient.calls[3]
    attribution_post = _FakeAsyncClient.calls[4]

    assert twr_post["url"] == "http://analytics/performance/twr"
    assert twr_post["json"]["portfolio_id"] == "P1"
    assert twr_post["json"]["metric_basis"] == "NET"
    assert twr_post["json"]["report_start_date"] == "2026-01-01"
    assert twr_post["json"]["performance_start_date"] == "2026-01-01"
    assert twr_post["json"]["analyses"][0]["period"] == "EXPLICIT"
    assert twr_post["json"]["include_benchmark"] is True
    assert twr_post["json"]["benchmark"]["benchmark_id"] == "MODEL_60_40"
    assert twr_post["json"]["benchmark"]["return_source"] == "calculated"
    assert twr_poll["url"] == "http://analytics/jobs/twr-1/result"

    assert mwr_post["url"] == "http://analytics/performance/mwr"
    assert mwr_post["json"]["portfolio_id"] == "P1"
    assert mwr_post["json"]["as_of"] == "2026-02-24"
    assert mwr_post["json"]["stateful_input"]["window_start_date"] == "2026-01-01"

    assert contribution_post["url"] == "http://analytics/performance/contribution"
    assert contribution_post["json"]["report_start_date"] == "2026-01-01"
    assert contribution_post["json"]["stateful_input"]["metric_basis"] == "NET"
    assert contribution_post["json"]["stateful_input"]["dimensions"] == ["asset_class"]
    assert contribution_post["json"]["stateful_input"]["include_cash_flows"] is True

    assert attribution_post["url"] == "http://analytics/performance/attribution"
    assert attribution_post["json"]["group_by"] == ["sector"]
    assert attribution_post["json"]["stateful_input"]["metric_basis"] == "GROSS"
    assert attribution_post["json"]["stateful_input"]["benchmark_id"] == "MODEL_60_40"
    assert "calculation_id" not in attribution_post["json"]


@pytest.mark.asyncio
async def test_lotus_analytics_client_calls_composite_performance_routes():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "calculation_id": "calc-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "status": "READY",
            "periods": [],
        },
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "inspection_id": "insp-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "verdict": "supportable",
            "artifacts": [],
        },
    )

    twr_status, twr_payload = await client.post_composite_twr(
        payload={
            "calculation_id": "calc-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        },
        correlation_id="corr-composite",
    )
    inspection_status, inspection_payload = await client.post_composite_inspection(
        payload={
            "inspection_id": "insp-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        },
        correlation_id="corr-composite",
    )

    assert twr_status == 200
    assert twr_payload["status"] == "READY"
    assert inspection_status == 200
    assert inspection_payload["verdict"] == "supportable"
    twr_post = _FakeAsyncClient.calls[0]
    inspection_post = _FakeAsyncClient.calls[1]
    assert twr_post["url"] == "http://analytics/performance/composites/twr"
    assert twr_post["json"]["composite_id"] == "PB_GLOBAL_BALANCED_USD"
    assert twr_post["headers"]["X-Correlation-Id"] == "corr-composite"
    assert inspection_post["url"] == "http://analytics/performance/composites/inspect"
    assert inspection_post["json"]["inspection_id"] == "insp-1"
    assert inspection_post["headers"]["X-Correlation-Id"] == "corr-composite"


@pytest.mark.asyncio
async def test_lotus_analytics_client_omits_stateful_dimension_filter_for_currency_attribution():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {
                    "reconciliation": {
                        "total_active_return": 0.7,
                        "sum_of_effects": 0.69,
                        "residual": 0.01,
                    },
                    "levels": [],
                }
            }
        },
    )

    status, _ = await client.get_attribution_analytics(
        portfolio_id="P1",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        period="YTD",
        metric_basis="NET",
        benchmark_id="MODEL_60_40",
        dimension="currency",
        correlation_id="corr-performance",
    )

    assert status == 200
    attribution_post = _FakeAsyncClient.calls[-1]
    assert attribution_post["json"]["group_by"] == ["currency"]
    assert attribution_post["json"]["stateful_input"]["dimensions"] == []
    assert attribution_post["json"]["stateful_input"]["benchmark_id"] == "MODEL_60_40"


@pytest.mark.asyncio
async def test_lotus_analytics_client_allows_slow_stateful_attribution_to_materialize(monkeypatch):
    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("app.clients.lotus_analytics_client.asyncio.sleep", _no_sleep)

    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(202, {"result_path": "/performance/attribution/results/calc-1"})
    for _ in range(12):
        _FakeAsyncClient.queue_json(202, {"detail": "async attribution result still pending"})
    _FakeAsyncClient.queue_json(
        200,
        {
            "model": "BF",
            "linking": "carino",
            "results_by_period": {
                "YTD": {
                    "reconciliation": {
                        "total_active_return": 0.7,
                        "sum_of_effects": 0.69,
                        "residual": 0.01,
                    },
                    "levels": [],
                }
            },
        },
    )

    status, payload = await client.get_attribution_analytics(
        portfolio_id="P1",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        period="YTD",
        metric_basis="NET",
        benchmark_id="MODEL_60_40",
        dimension="asset_class",
        correlation_id="corr-performance",
    )

    assert status == 200
    assert payload["results_by_period"]["YTD"]["reconciliation"]["sum_of_effects"] == 0.69
    assert len(_FakeAsyncClient.calls) == 14
    assert _FakeAsyncClient.calls[-1]["url"] == (
        "http://analytics/performance/attribution/results/calc-1"
    )


@pytest.mark.asyncio
async def test_lotus_analytics_client_preserves_absolute_async_result_url(monkeypatch):
    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("app.clients.lotus_analytics_client.asyncio.sleep", _no_sleep)

    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(202, {"detail": "pending"})
    _FakeAsyncClient.queue_json(200, {"status": "ready"})

    status, payload = await client._poll_async_result(
        result_path="https://analytics-results.example.com/results/calc-1",
        correlation_id="corr-performance",
        service="lotus-performance",
        operation="performance.attribution",
        max_attempts=2,
        poll_interval_seconds=0.01,
    )

    assert status == 200
    assert payload == {"status": "ready"}
    assert [call["url"] for call in _FakeAsyncClient.calls] == [
        "https://analytics-results.example.com/results/calc-1",
        "https://analytics-results.example.com/results/calc-1",
    ]


@pytest.mark.asyncio
async def test_lotus_analytics_client_uses_canonical_risk_routes() -> None:
    client = LotusAnalyticsClient(base_url="http://risk", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"results": {}})
    _FakeAsyncClient.queue_json(200, {"risk_proxy": {"hhi_current": 100.0}})
    _FakeAsyncClient.queue_json(200, {"results": {}})
    _FakeAsyncClient.queue_json(200, {"results": {}})
    _FakeAsyncClient.queue_json(200, {"results": {}})

    status_one, _ = await client.post_risk_calculate(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-risk",
    )
    status_two, _ = await client.post_risk_concentration(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-risk",
    )
    status_three, _ = await client.post_risk_drawdown(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-risk",
    )
    status_four, _ = await client.post_risk_rolling_metrics(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-risk",
    )
    status_five, _ = await client.post_risk_historical_attribution(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-risk",
    )

    assert status_one == 200
    assert status_two == 200
    assert status_three == 200
    assert status_four == 200
    assert status_five == 200
    assert _FakeAsyncClient.calls[-5]["url"] == "http://risk/analytics/risk/calculate"
    assert _FakeAsyncClient.calls[-4]["url"] == "http://risk/analytics/risk/concentration"
    assert _FakeAsyncClient.calls[-3]["url"] == "http://risk/analytics/risk/drawdown"
    assert _FakeAsyncClient.calls[-2]["url"] == "http://risk/analytics/risk/rolling-metrics"
    assert _FakeAsyncClient.calls[-1]["url"] == "http://risk/analytics/risk/historical-attribution"


@pytest.mark.asyncio
async def test_lotus_ai_client_calls_task_execution_contract_with_correlation_headers():
    client = LotusAiClient(base_url="http://ai", timeout_seconds=3.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "status": "COMPLETED",
            "task_id": "explain.v1",
            "category": "explain",
            "output_label": "EXPLANATION_ONLY",
            "result": {"message": "Advisor summary.", "structured_output": {}},
            "audit": {"request_id": "req-1"},
            "evidence": {"descriptors": []},
        },
    )

    status, payload = await client.execute_task(
        task_id="explain.v1",
        caller_app="lotus-gateway",
        correlation_id="corr-ai-1",
        context_summary="Advisor brief context",
        context_payload={"portfolio_id": "PF_1001"},
        source_refs=["lotus-gateway:workbench:PF_1001:performance-summary:YTD"],
        expected_output_label="EXPLANATION_ONLY",
    )

    assert status == 200
    assert payload["status"] == "COMPLETED"
    assert _FakeAsyncClient.calls[-1]["url"] == "http://ai/ai/tasks/execute"
    assert _FakeAsyncClient.calls[-1]["headers"]["X-Correlation-Id"] == "corr-ai-1"
    assert _FakeAsyncClient.calls[-1]["json"] == {
        "task_id": "explain.v1",
        "input_mode": "STRUCTURED_CONTEXT",
        "caller": {
            "caller_app": "lotus-gateway",
            "correlation_id": "corr-ai-1",
        },
        "context": {
            "summary": "Advisor brief context",
            "payload": {"portfolio_id": "PF_1001"},
            "source_refs": ["lotus-gateway:workbench:PF_1001:performance-summary:YTD"],
        },
        "expected_output_label": "EXPLANATION_ONLY",
    }


@pytest.mark.asyncio
async def test_lotus_ai_client_emits_safe_fanout_metrics_without_prompt_content(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = LotusAiClient(base_url="http://ai", timeout_seconds=3.0)
    _FakeAsyncClient.queue_json(
        503,
        {
            "detail": "upstream communication failure",
            "raw_prompt": "sensitive prompt text",
            "model_output": "sensitive generated output",
        },
    )

    status, payload = await client.execute_task(
        task_id="explain.v1",
        caller_app="lotus-gateway",
        correlation_id="corr-ai-observed",
        context_summary="Advisor brief context",
        context_payload={"portfolio_id": "PF_1001"},
        source_refs=["lotus-gateway:workbench:PF_1001:performance-summary:YTD"],
    )

    assert status == 503
    assert payload["detail"] == "upstream communication failure"
    [record] = _fanout_records(caplog.records, service="lotus-ai")
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.fanout.degraded"
    assert fields["operation"] == "ai.tasks.execute"
    assert fields["status_class"] == "5xx"
    assert fields["reason"] == "UPSTREAM_UNAVAILABLE"
    assert "raw_prompt" not in fields
    assert "model_output" not in fields
    assert "portfolio_id" not in fields


@pytest.mark.asyncio
async def test_lotus_ai_client_posts_workflow_pack_review_actions():
    client = LotusAiClient(base_url="http://ai", timeout_seconds=3.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "run": {
                "run_id": "packrun_advisor_brief_req-1",
                "review_state": "SUPERSEDED",
            }
        },
    )

    status, payload = await client.apply_workflow_pack_run_review_action(
        run_id="packrun_advisor_brief_req-1",
        correlation_id="corr-ai-review-1",
        request_payload={
            "action_type": "SUPERSEDE",
            "caller_app": "lotus-gateway",
            "reviewed_by": "advisor_1",
            "reason": "Advisor brief superseded in favor of the replacement run.",
            "replacement_run_id": "packrun_advisor_brief_req-2",
        },
    )

    assert status == 200
    assert payload["run"]["review_state"] == "SUPERSEDED"
    assert _FakeAsyncClient.calls[-1]["url"] == (
        "http://ai/platform/workflow-packs/runs/packrun_advisor_brief_req-1/review-actions"
    )
    assert _FakeAsyncClient.calls[-1]["headers"]["X-Correlation-Id"] == "corr-ai-review-1"
    assert _FakeAsyncClient.calls[-1]["json"] == {
        "action_type": "SUPERSEDE",
        "caller_app": "lotus-gateway",
        "reviewed_by": "advisor_1",
        "reason": "Advisor brief superseded in favor of the replacement run.",
        "replacement_run_id": "packrun_advisor_brief_req-2",
    }


@pytest.mark.asyncio
async def test_lotus_ai_client_calls_explicit_workflow_pack_execution_contract():
    client = LotusAiClient(base_url="http://ai", timeout_seconds=3.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "service": "lotus-ai",
            "version": "0.1.0",
            "eligibility": {"allowed": True},
            "execution": {
                "status": "COMPLETED",
                "task_id": "explain.v1",
                "category": "explain",
                "output_label": "EXPLANATION_ONLY",
                "result": {"message": "Advisor summary.", "structured_output": {}},
                "audit": {
                    "request_id": "req-1",
                    "workflow_pack_run_id": "packrun_advisor_brief_req-1",
                },
                "evidence": {"descriptors": []},
            },
            "workflow_pack_run": {"run_id": "packrun_advisor_brief_req-1"},
            "summary": [],
        },
    )

    status, payload = await client.execute_workflow_pack(
        pack_id="advisor_brief.pack",
        version="v1",
        environment="DEVELOPMENT",
        caller_identity_class="BANKER_PRODUCT",
        workflow_surface="advisor-brief-workspace",
        task_request={
            "task_id": "explain.v1",
            "input_mode": "STRUCTURED_CONTEXT",
            "caller": {
                "caller_app": "lotus-gateway",
                "correlation_id": "corr-ai-pack-1",
            },
            "context": {
                "summary": "Advisor brief context",
                "payload": {"portfolio_id": "PF_1001"},
                "source_refs": ["lotus-gateway:workbench:PF_1001:performance-summary:YTD"],
            },
            "expected_output_label": "EXPLANATION_ONLY",
        },
        correlation_id="corr-ai-pack-1",
    )

    assert status == 200
    assert payload["execution"]["audit"]["workflow_pack_run_id"] == "packrun_advisor_brief_req-1"
    assert _FakeAsyncClient.calls[-1]["url"] == "http://ai/platform/workflow-packs/execute"
    assert _FakeAsyncClient.calls[-1]["headers"]["X-Correlation-Id"] == "corr-ai-pack-1"
    assert _FakeAsyncClient.calls[-1]["json"] == {
        "pack_id": "advisor_brief.pack",
        "version": "v1",
        "environment": "DEVELOPMENT",
        "caller_identity_class": "BANKER_PRODUCT",
        "workflow_surface": "advisor-brief-workspace",
        "task_request": {
            "task_id": "explain.v1",
            "input_mode": "STRUCTURED_CONTEXT",
            "caller": {
                "caller_app": "lotus-gateway",
                "correlation_id": "corr-ai-pack-1",
            },
            "context": {
                "summary": "Advisor brief context",
                "payload": {"portfolio_id": "PF_1001"},
                "source_refs": ["lotus-gateway:workbench:PF_1001:performance-summary:YTD"],
            },
            "expected_output_label": "EXPLANATION_ONLY",
        },
    }


@pytest.mark.asyncio
async def test_lotus_ai_client_lists_workflow_pack_task_flows_with_bounded_filters():
    client = LotusAiClient(base_url="http://ai", timeout_seconds=3.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "task_flow_count": 1,
            "task_flows": [
                {
                    "task_flow_id": "taskflow_advisor_brief_req-1",
                    "workflow_pack_id": "advisor_brief.pack",
                    "run_refs": ["packrun_advisor_brief_req-1"],
                }
            ],
        },
    )

    status, payload = await client.list_workflow_pack_task_flows(
        correlation_id="corr-ai-task-flow-1",
        workflow_pack_id="advisor_brief.pack",
        caller="lotus-gateway",
        workflow_surface="advisor-brief-workspace",
        limit=25,
    )

    assert status == 200
    assert payload["task_flow_count"] == 1
    assert _FakeAsyncClient.calls[-1]["method"] == "GET"
    assert _FakeAsyncClient.calls[-1]["url"] == "http://ai/platform/workflow-packs/task-flows"
    assert _FakeAsyncClient.calls[-1]["params"] == {
        "limit": 25,
        "workflow_pack_id": "advisor_brief.pack",
        "caller": "lotus-gateway",
        "workflow_surface": "advisor-brief-workspace",
    }
    assert _FakeAsyncClient.calls[-1]["headers"]["X-Correlation-Id"] == "corr-ai-task-flow-1"


@pytest.mark.asyncio
async def test_lotus_analytics_client_twr_request_omits_benchmark_when_not_requested():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 2.1}}}}
            }
        },
    )

    status_code, _ = await client.get_twr_analytics(
        portfolio_id="P1",
        report_end_date="2026-02-24",
        report_start_date=None,
        period="YTD",
        metric_basis="NET",
        benchmark_id=None,
        correlation_id="corr-performance",
    )

    assert status_code == 200
    assert _FakeAsyncClient.calls[0]["json"]["include_benchmark"] is False
    assert "benchmark" not in _FakeAsyncClient.calls[0]["json"]


@pytest.mark.asyncio
async def test_lotus_analytics_client_workspace_summary_uses_canonical_summary_contract():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {
                    "portfolio_twr": {
                        "net": {"summary": {"period_return": {"base": 2.1}}},
                        "gross": {"summary": {"period_return": {"base": 2.2}}},
                    }
                }
            }
        },
    )

    status_code, payload = await client.get_workspace_summary(
        portfolio_id="P1",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        chart_frequency="quarterly",
        detail_basis="NET",
        benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-performance",
    )

    assert status_code == 200
    assert "results_by_period" in payload
    request = _FakeAsyncClient.calls[0]
    assert request["url"] == "http://analytics/performance/workspace-summary"
    assert request["json"]["periods"][0]["period"] == "YTD"
    assert request["json"]["periods"][0]["frequencies"] == ["quarterly", "monthly", "yearly"]
    assert request["json"]["report_ccy"] == "USD"
    assert "currency_mode" not in request["json"]
    assert "segmentation" not in request["json"]
    assert "contribution" not in request["json"]
    assert "attribution" not in request["json"]
    assert request["json"]["benchmark"]["benchmark_id"] == "BMK_PB_GLOBAL_BALANCED_60_40"


@pytest.mark.asyncio
async def test_lotus_analytics_client_workspace_summary_forwards_trace_context():
    trace_id = "0123456789abcdef0123456789abcdef"
    trace_token = trace_id_var.set(trace_id)
    try:
        client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
        _FakeAsyncClient.queue_json(
            200,
            {
                "results_by_period": {
                    "YTD": {
                        "portfolio_twr": {
                            "net": {"summary": {"period_return": {"base": 2.1}}},
                            "gross": {"summary": {"period_return": {"base": 2.2}}},
                        }
                    }
                }
            },
        )

        await client.get_workspace_summary(
            portfolio_id="P1",
            report_end_date="2026-03-27",
            report_start_date=None,
            period="YTD",
            chart_frequency="monthly",
            detail_basis="NET",
            benchmark_id=None,
            reporting_currency="USD",
            segment="asset_class",
            correlation_id="corr-workbench-route-1",
        )
    finally:
        trace_id_var.reset(trace_token)

    headers = _FakeAsyncClient.calls[0]["headers"]
    assert headers["X-Correlation-Id"] == "corr-workbench-route-1"
    assert headers["X-Trace-Id"] == trace_id
    assert headers["traceparent"] == f"00-{trace_id}-0000000000000001-01"
    assert "portfolio_id" not in headers
    assert "client_id" not in headers


@pytest.mark.asyncio
async def test_lotus_analytics_client_emits_safe_structured_fanout_log(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "state": "partial",
            "warnings": ["PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE"],
            "partial_failures": [
                {
                    "source_service": "lotus-performance",
                    "error_code": "PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE",
                    "detail": "upstream unavailable",
                }
            ],
            "supportability": [{"key": "portfolio_returns", "state": "partial"}],
            "results_by_period": {},
        },
    )

    status_code, _ = await client.get_workspace_summary(
        portfolio_id="P1",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_id=None,
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-workbench-route-1",
    )

    assert status_code == 200
    [record] = [
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.fanout.degraded"
    ]
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.fanout.degraded"
    assert fields["route"] == "workbench-analytics"
    assert fields["service"] == "lotus-performance"
    assert fields["operation"] == "performance.workspace-summary"
    assert fields["state"] == "partial"
    assert fields["supportability_state"] == "partial"
    assert fields["reason"] == "PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE"
    assert fields["status_class"] == "2xx"
    assert fields["warning_count"] == 1
    assert fields["partial_failure_count"] == 1
    assert isinstance(fields["duration_ms"], float)
    assert "portfolio_id" not in fields
    assert "client_id" not in fields
    assert "request_body" not in fields
    assert "response_body" not in fields


@pytest.mark.asyncio
async def test_lotus_analytics_client_emits_safe_read_allowed_audit_log(caplog, monkeypatch):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    monkeypatch.setenv("LOTUS_REGION", "AP-SOUTHEAST-1")
    monkeypatch.setenv("LOTUS_ENVIRONMENT", "Local")
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {},
            "request_body": {"portfolio_id": "P1"},
            "response_body": {"client_name": "Sensitive Client"},
        },
    )

    status_code, _ = await client.get_workspace_summary(
        portfolio_id="P1",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_id=None,
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-audit-allowed",
    )

    assert status_code == 200
    [record] = [
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.audit.analytics_read_allowed"
    ]
    fields = record.extra_fields
    assert fields == {
        "event": "gateway.analytics.audit.analytics_read_allowed",
        "route": "workbench-analytics",
        "panel": "performance-summary",
        "operation": "performance.workspace-summary",
        "state": "ready",
        "reason": "upstream_read_succeeded",
        "status_class": "2xx",
        "region": "ap-southeast-1",
        "environment": "local",
    }
    assert "portfolio_id" not in fields
    assert "client_name" not in fields
    assert "request_body" not in fields
    assert "response_body" not in fields


@pytest.mark.asyncio
async def test_lotus_analytics_client_emits_safe_read_denied_audit_log(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        403,
        {
            "detail": "denied for portfolio P1",
            "raw_entitlement_failure": "client_name=Sensitive Client",
        },
    )

    status_code, _ = await client.post_risk_calculate(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-audit-denied",
    )

    assert status_code == 403
    [record] = [
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.audit.analytics_read_denied"
    ]
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.audit.analytics_read_denied"
    assert fields["route"] == "workbench-analytics"
    assert fields["panel"] == "risk-summary"
    assert fields["operation"] == "analytics.risk.calculate"
    assert fields["state"] == "permission_blocked"
    assert fields["reason"] == "upstream_authorization_denied"
    assert fields["status_class"] == "4xx"
    assert fields["region"] == "unknown"
    assert fields["environment"] == "local"
    assert "portfolio_id" not in fields
    assert "raw_entitlement_failure" not in fields


@pytest.mark.asyncio
async def test_lotus_analytics_client_emits_safe_unavailable_fanout_log(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(503, {"detail": "upstream communication failure"})

    status_code, payload = await client.post_risk_calculate(
        payload={"input_mode": "stateful", "stateful_input": {"portfolio_id": "P1"}},
        correlation_id="corr-risk",
    )

    assert status_code == 503
    assert payload["detail"] == "upstream communication failure"
    [record] = [
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.fanout.degraded"
    ]
    fields = record.extra_fields
    assert fields["service"] == "lotus-risk"
    assert fields["operation"] == "analytics.risk.calculate"
    assert fields["state"] == "degraded"
    assert fields["reason"] == "UPSTREAM_UNAVAILABLE"
    assert fields["status_class"] == "5xx"
    assert fields["error_category"] == "upstream_unavailable"
    assert "portfolio_id" not in fields


@pytest.mark.asyncio
async def test_lotus_analytics_client_retries_workspace_summary_when_calculation_id_conflicts():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        409,
        {
            "detail": (
                "A calculation with this calculation_id already exists. "
                "Use a new calculation_id for synchronous execution."
            )
        },
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {
                    "portfolio_twr": {
                        "net": {"summary": {"period_return": {"base": 2.1}}},
                        "gross": {"summary": {"period_return": {"base": 2.2}}},
                    }
                }
            }
        },
    )

    status_code, payload = await client.get_workspace_summary(
        portfolio_id="P1",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        chart_frequency="quarterly",
        detail_basis="NET",
        benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-performance",
    )

    assert status_code == 200
    assert "results_by_period" in payload
    assert len(_FakeAsyncClient.calls) == 2
    first_request = _FakeAsyncClient.calls[0]
    replay_request = _FakeAsyncClient.calls[1]
    assert (
        first_request["url"]
        == replay_request["url"]
        == "http://analytics/performance/workspace-summary"
    )
    assert first_request["json"]["calculation_id"] != replay_request["json"]["calculation_id"]
    assert "currency_mode" not in first_request["json"]
    assert "currency_mode" not in replay_request["json"]
    assert first_request["json"]["report_ccy"] == replay_request["json"]["report_ccy"] == "USD"
    assert first_request["json"]["periods"] == replay_request["json"]["periods"]
    assert first_request["json"]["benchmark"] == replay_request["json"]["benchmark"]


@pytest.mark.asyncio
async def test_lotus_analytics_client_disables_timeout_retries_for_workspace_summary(monkeypatch):
    captured: list[dict] = []

    async def _fake_request_with_retry(**kwargs):
        captured.append(kwargs)
        return 503, {"detail": "upstream communication failure: TimeoutException"}

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.request_with_retry", _fake_request_with_retry
    )

    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=15.0)

    status_code, payload = await client.get_workspace_summary(
        portfolio_id="P1",
        report_end_date="2026-03-27",
        report_start_date="2026-01-01",
        period="QTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-performance",
    )

    assert status_code == 503
    assert payload["detail"] == "upstream communication failure: TimeoutException"
    assert captured[0]["retry_timeout_exceptions"] is False
    assert captured[0]["timeout_seconds"] == 15.0


@pytest.mark.asyncio
async def test_lotus_analytics_client_workspace_summary_omits_unsupported_currency_breakout():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {
                    "portfolio_twr": {
                        "net": {"summary": {"period_return": {"base": 2.1}}},
                        "gross": {"summary": {"period_return": {"base": 2.2}}},
                    }
                }
            }
        },
    )

    status_code, payload = await client.get_workspace_summary(
        portfolio_id="P1",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-performance",
    )

    assert status_code == 200
    assert "results_by_period" in payload
    assert len(_FakeAsyncClient.calls) == 1
    request = _FakeAsyncClient.calls[0]["json"]
    assert "currency_mode" not in request
    assert request["report_ccy"] == "USD"
    assert "segmentation" not in request
    assert "contribution" not in request
    assert "attribution" not in request


@pytest.mark.asyncio
async def test_lotus_analytics_client_fetches_execution_and_lineage_evidence():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "calculation_id": "calc-workspace-summary",
            "status": "complete",
            "execution_mode": "sync",
        },
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "calculation_id": "calc-workspace-summary",
            "status": "complete",
            "artifacts": {"request.json": {"url": "http://performance/path"}},
        },
    )

    execution_status, execution_payload = await client.get_execution(
        calculation_id="calc-workspace-summary",
        correlation_id="corr-performance",
    )
    lineage_status, lineage_payload = await client.get_lineage(
        calculation_id="calc-workspace-summary",
        correlation_id="corr-performance",
    )

    assert execution_status == 200
    assert execution_payload["status"] == "complete"
    assert lineage_status == 200
    assert lineage_payload["artifacts"]["request.json"]["url"] == "http://performance/path"
    assert (
        _FakeAsyncClient.calls[0]["url"]
        == "http://analytics/performance/executions/calc-workspace-summary"
    )
    assert (
        _FakeAsyncClient.calls[1]["url"]
        == "http://analytics/performance/lineage/calc-workspace-summary"
    )


@pytest.mark.asyncio
async def test_lotus_analytics_client_downloads_lineage_artifact_bytes():
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=2.0)
    _FakeAsyncClient.responses.append(
        httpx.Response(
            status_code=200,
            content=b"{}",
            headers={"Content-Type": "application/json"},
            request=httpx.Request("GET", "http://test"),
        )
    )

    status_code, content, content_type = await client.get_lineage_artifact(
        calculation_id="calc-workspace-summary",
        artifact_name="request.json",
        correlation_id="corr-performance",
    )

    assert status_code == 200
    assert content == b"{}"
    assert content_type == "application/json"
    assert (
        _FakeAsyncClient.calls[0]["url"]
        == "http://analytics/performance/lineage/calc-workspace-summary/artifacts/request.json"
    )


@pytest.mark.asyncio
async def test_lotus_core_query_client_fetches_benchmark_assignment():
    client = LotusCoreQueryClient(
        base_url="http://core-query",
        control_plane_base_url="http://core-control",
        timeout_seconds=2.0,
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
            "assignment_status": "active",
        },
    )

    status_code, payload = await client.get_benchmark_assignment(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        as_of_date="2026-03-28",
        reporting_currency="USD",
        correlation_id="corr-performance",
    )

    assert status_code == 200
    assert payload["benchmark_id"] == "BMK_PB_GLOBAL_BALANCED_60_40"
    request = _FakeAsyncClient.calls[0]
    assert request["url"] == (
        "http://core-control/integration/portfolios/PB_SG_GLOBAL_BAL_001/benchmark-assignment"
    )
    assert request["json"] == {
        "as_of_date": "2026-03-28",
        "reporting_currency": "USD",
    }


@pytest.mark.asyncio
async def test_lotus_analytics_client_non_json_and_non_dict_payload_handling():
    client = LotusAnalyticsClient(base_url="http://lotus-performance", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(503, "lotus-performance unavailable")
    _FakeAsyncClient.queue_json(200, ["analytics"])

    status_one, payload_one = await client.get_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-1",
    )
    status_two, payload_two = await client.get_stateful_twr(
        portfolio_id="P1",
        report_end_date="2026-02-24",
        period="YTD",
        correlation_id="corr-1",
    )

    assert status_one == 503
    assert payload_one["detail"] == "lotus-performance unavailable"
    assert status_two == 200
    assert payload_two["detail"] == ["analytics"]
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_endpoints_and_non_json_response_handling():
    client = LotusCoreQueryClient(base_url="http://lotus-performances", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"portfolio_id": "P1"})
    _FakeAsyncClient.queue_json(200, {"positions": [{"security_id": "EQ_1"}]})
    _FakeAsyncClient.queue_json(200, {"transactions": [{"transaction_id": "TX_1"}]})
    _FakeAsyncClient.queue_json(200, {"points": [{"projection_date": "2026-03-25"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"portfolio_id": "P1"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"instrument_id": "AAPL"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"value": "USD"}]})
    _FakeAsyncClient.queue_json(201, {"session": {"session_id": "S1", "version": 1}})
    _FakeAsyncClient.queue_json(200, {"version": 2})
    _FakeAsyncClient.queue_json(200, {"positions": []})
    _FakeAsyncClient.queue_text(503, "service unavailable")

    assert (await client.get_portfolio(portfolio_id="P1", correlation_id="corr-2"))[0] == 200
    assert (await client.get_portfolio_positions(portfolio_id="P1", correlation_id="corr-2"))[
        0
    ] == 200
    assert (await client.get_portfolio_transactions(portfolio_id="P1", correlation_id="corr-2"))[
        0
    ] == 200
    assert (await client.get_cashflow_projection(portfolio_id="P1", correlation_id="corr-2"))[
        0
    ] == 200
    assert (await client.get_portfolio_lookups(correlation_id="corr-2"))[0] == 200
    assert (await client.get_instrument_lookups(limit=25, correlation_id="corr-2"))[0] == 200
    assert (await client.get_currency_lookups(correlation_id="corr-2"))[0] == 200
    assert (
        await client.create_simulation_session(
            portfolio_id="P1",
            created_by="advisor",
            ttl_hours=4,
            correlation_id="corr-2",
        )
    )[0] == 201
    assert (
        await client.add_simulation_changes(
            session_id="S1",
            changes=[{"kind": "trade"}],
            correlation_id="corr-2",
        )
    )[0] == 200
    projected_positions_status, _ = await client.get_projected_positions(
        session_id="S1",
        correlation_id="corr-2",
    )
    assert projected_positions_status == 200
    status_summary, payload_summary = await client.get_projected_summary(
        session_id="S1", correlation_id="corr-2"
    )
    assert status_summary == 503
    assert payload_summary["detail"] == "service unavailable"
    assert _FakeAsyncClient.calls[0]["url"] == "http://lotus-performances/portfolios/P1"
    assert _FakeAsyncClient.calls[1]["url"] == "http://lotus-performances/portfolios/P1/positions"
    assert (
        _FakeAsyncClient.calls[2]["url"] == "http://lotus-performances/portfolios/P1/transactions"
    )
    assert (
        _FakeAsyncClient.calls[3]["url"]
        == "http://lotus-performances/portfolios/P1/cashflow-projection"
    )


@pytest.mark.asyncio
async def test_lotus_core_query_client_transaction_route_supports_advanced_filters_and_sorting():
    client = LotusCoreQueryClient(base_url="http://lotus-performances", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"transactions": [{"transaction_id": "TX_1"}]})

    status_code, payload = await client.get_portfolio_transactions(
        portfolio_id="P1",
        correlation_id="corr-2-advanced",
        limit=25,
        skip=5,
        sort_by="settlement_date",
        sort_order="asc",
        as_of_date="2026-03-27",
        include_projected=True,
        transaction_type="FX_FORWARD",
        security_id="SEC_EQ_1",
        instrument_id="INST_EQ_1",
        component_type="FX_CONTRACT_OPEN",
        linked_transaction_group_id="LTG-FX-2026-0001",
        fx_contract_id="FXC-2026-0001",
        swap_event_id="FXSWAP-2026-0001",
        near_leg_group_id="FXSWAP-2026-0001-NEAR",
        far_leg_group_id="FXSWAP-2026-0001-FAR",
        start_date="2026-03-01",
        end_date="2026-03-27",
    )

    assert status_code == 200
    assert payload["transactions"][0]["transaction_id"] == "TX_1"
    assert (
        _FakeAsyncClient.calls[0]["url"] == "http://lotus-performances/portfolios/P1/transactions"
    )
    assert _FakeAsyncClient.calls[0]["params"] == {
        "limit": 25,
        "skip": 5,
        "sort_by": "settlement_date",
        "sort_order": "asc",
        "include_projected": "true",
        "as_of_date": "2026-03-27",
        "transaction_type": "FX_FORWARD",
        "security_id": "SEC_EQ_1",
        "instrument_id": "INST_EQ_1",
        "component_type": "FX_CONTRACT_OPEN",
        "linked_transaction_group_id": "LTG-FX-2026-0001",
        "fx_contract_id": "FXC-2026-0001",
        "swap_event_id": "FXSWAP-2026-0001",
        "near_leg_group_id": "FXSWAP-2026-0001-NEAR",
        "far_leg_group_id": "FXSWAP-2026-0001-FAR",
        "start_date": "2026-03-01",
        "end_date": "2026-03-27",
    }


def test_lotus_core_transaction_query_params_omit_unset_optional_filters():
    assert build_portfolio_transaction_query_params(
        limit=10,
        skip=0,
        sort_by="transaction_date",
        sort_order="desc",
        include_projected=False,
        as_of_date=None,
        transaction_type=None,
        security_id=None,
        instrument_id=None,
        component_type=None,
        linked_transaction_group_id=None,
        fx_contract_id=None,
        swap_event_id=None,
        near_leg_group_id=None,
        far_leg_group_id=None,
        start_date=None,
        end_date=None,
        reporting_currency="SGD",
    ) == {
        "limit": 10,
        "skip": 0,
        "sort_by": "transaction_date",
        "sort_order": "desc",
        "include_projected": "false",
        "reporting_currency": "SGD",
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_cash_balances_uses_strategic_holdings_route():
    client = LotusCoreQueryClient(base_url="http://lotus-performances", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"cash_accounts": []})

    status_code, payload = await client.get_portfolio_cash_balances(
        portfolio_id="P1",
        correlation_id="corr-cash-balances",
        as_of_date="2026-03-27",
        reporting_currency="SGD",
    )

    assert status_code == 200
    assert payload["cash_accounts"] == []
    assert (
        _FakeAsyncClient.calls[0]["url"] == "http://lotus-performances/portfolios/P1/cash-balances"
    )
    assert _FakeAsyncClient.calls[0]["params"] == {
        "as_of_date": "2026-03-27",
        "reporting_currency": "SGD",
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_core_endpoints():
    client = LotusCoreQueryClient(base_url="http://lotus-performances", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "pas"})
    _FakeAsyncClient.queue_json(200, {"allowedSections": ["OVERVIEW"]})
    _FakeAsyncClient.queue_json(200, {"portfolios": []})
    _FakeAsyncClient.queue_json(200, {"items": [{"id": "P1", "label": "Portfolio 1"}]})
    _FakeAsyncClient.queue_json(200, {"as_of_date": "2026-02-24", "sections": {}})
    _FakeAsyncClient.queue_json(200, {"performance_end_date": "2026-02-24"})
    _FakeAsyncClient.queue_json(200, {"items": [{"instrument_id": "AAPL"}]})

    assert (
        await client.get_capabilities(
            consumer_system="lotus-gateway", tenant_id="default", correlation_id="corr-3"
        )
    )[0] == 200
    assert (
        await client.get_effective_policy(
            consumer_system="lotus-gateway", tenant_id="default", correlation_id="corr-3"
        )
    )[0] == 200
    assert (await client.list_portfolios(correlation_id="corr-3"))[0] == 200
    assert (await client.get_portfolio_lookups(correlation_id="corr-3"))[0] == 200
    assert (
        await client.get_core_snapshot(
            portfolio_id="P1",
            as_of_date="2026-02-24",
            sections=["positions_baseline"],
            consumer_system="lotus-gateway",
            correlation_id="corr-3",
        )
    )[0] == 200
    assert (
        await client.get_portfolio_analytics_reference(
            portfolio_id="P1",
            as_of_date="2026-02-24",
            consumer_system="lotus-gateway",
            correlation_id="corr-3",
        )
    )[0] == 200
    assert (await client.list_instruments(limit=10, correlation_id="corr-3"))[0] == 200
    assert _FakeAsyncClient.calls[0]["url"] == "http://lotus-performances/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert (
        _FakeAsyncClient.calls[1]["url"] == "http://lotus-performances/integration/policy/effective"
    )
    assert _FakeAsyncClient.calls[1]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert _FakeAsyncClient.calls[3]["url"] == "http://lotus-performances/lookups/portfolios"
    assert _FakeAsyncClient.calls[3]["params"] == {}
    assert _FakeAsyncClient.calls[4]["json"] == {
        "as_of_date": "2026-02-24",
        "sections": ["positions_baseline"],
        "consumer_system": "lotus-gateway",
    }
    assert (
        _FakeAsyncClient.calls[5]["url"]
        == "http://lotus-performances/integration/portfolios/P1/analytics/reference"
    )


@pytest.mark.asyncio
async def test_lotus_core_query_client_lookup_routes_preserve_filter_query_params():
    client = LotusCoreQueryClient(base_url="http://lotus-performances", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"items": [{"id": "PF_1", "label": "PF_1"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"id": "SEC_1", "label": "SEC_1"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"id": "USD", "label": "USD"}]})

    assert (
        await client.get_portfolio_lookups(
            correlation_id="corr-lookups",
            cif_id="CIF_1001",
            booking_center="SG",
            q="Alpha",
            limit=25,
        )
    )[0] == 200
    assert (
        await client.get_instrument_lookups(
            limit=50,
            correlation_id="corr-lookups",
            product_type="EQUITY",
            q="Apple",
        )
    )[0] == 200
    assert (
        await client.get_currency_lookups(
            correlation_id="corr-lookups",
            instrument_page_limit=500,
            source="ALL",
            q="USD",
            limit=10,
        )
    )[0] == 200

    assert _FakeAsyncClient.calls[0]["url"] == "http://lotus-performances/lookups/portfolios"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "client_id": "CIF_1001",
        "booking_center_code": "SG",
        "q": "Alpha",
        "limit": 25,
    }
    assert _FakeAsyncClient.calls[1]["url"] == "http://lotus-performances/lookups/instruments"
    assert _FakeAsyncClient.calls[1]["params"] == {
        "limit": 50,
        "product_type": "EQUITY",
        "q": "Apple",
    }
    assert _FakeAsyncClient.calls[2]["url"] == "http://lotus-performances/lookups/currencies"
    assert _FakeAsyncClient.calls[2]["params"] == {
        "instrument_page_limit": 500,
        "source": "ALL",
        "q": "USD",
        "limit": 10,
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_capability_routes_use_canonical_snake_case_query_params():
    client = LotusCoreQueryClient(
        base_url="http://core-query",
        control_plane_base_url="http://core-control",
        timeout_seconds=2.0,
    )
    _FakeAsyncClient.queue_json(200, {"consumer_system": "lotus-workbench"})
    _FakeAsyncClient.queue_json(200, {"policyProvenance": {"policyVersion": "pas-policy-v7"}})

    capability_status, capability_payload = await client.get_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-a",
        correlation_id="corr-core-capabilities",
    )
    policy_status, policy_payload = await client.get_effective_policy(
        consumer_system="lotus-workbench",
        tenant_id="tenant-a",
        correlation_id="corr-core-capabilities",
    )

    assert capability_status == 200
    assert capability_payload["consumer_system"] == "lotus-workbench"
    assert policy_status == 200
    assert policy_payload["policyProvenance"]["policyVersion"] == "pas-policy-v7"
    assert _FakeAsyncClient.calls[0]["url"] == "http://core-control/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-workbench",
        "tenant_id": "tenant-a",
    }
    assert _FakeAsyncClient.calls[1]["url"] == "http://core-control/integration/policy/effective"
    assert _FakeAsyncClient.calls[1]["params"] == {
        "consumer_system": "lotus-workbench",
        "tenant_id": "tenant-a",
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_non_dict_payload_branch():
    client = LotusCoreQueryClient(base_url="http://lotus-performances", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, ["not-dict"])
    status_code, payload = await client.list_portfolios(correlation_id="corr-3")
    assert status_code == 200
    assert payload["detail"] == ["not-dict"]


@pytest.mark.asyncio
async def test_pas_ingestion_client_upload_paths():
    client = LotusCoreIngestionClient(
        base_url="http://lotus-performances-ingest", timeout_seconds=2.0
    )
    _FakeAsyncClient.queue_json(202, {"status": "accepted"})
    _FakeAsyncClient.queue_json(200, {"columns": ["portfolio_id"]})
    _FakeAsyncClient.queue_json(201, {"importedRows": 10})

    status_ingest, _ = await client.ingest_portfolio_bundle(
        body={"portfolio": {"portfolio_id": "P1"}},
        correlation_id="corr-4",
    )
    status_preview, _ = await client.preview_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        sample_size=5,
        correlation_id="corr-4",
    )
    status_commit, _ = await client.commit_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        allow_partial=False,
        correlation_id="corr-4",
    )

    assert status_ingest == 202
    assert status_preview == 200
    assert status_commit == 201
    assert (
        _FakeAsyncClient.calls[1]["url"]
        == "http://lotus-performances-ingest/ingest/uploads/preview"
    )
    assert (
        _FakeAsyncClient.calls[2]["url"] == "http://lotus-performances-ingest/ingest/uploads/commit"
    )
    assert _FakeAsyncClient.calls[1]["data"] == {
        "entity_type": "transactions",
        "sample_size": "5",
    }
    assert _FakeAsyncClient.calls[2]["data"] == {
        "entity_type": "transactions",
        "allow_partial": "false",
    }
    assert "X-Idempotency-Key" not in _FakeAsyncClient.calls[0]["headers"]


@pytest.mark.asyncio
async def test_pas_ingestion_client_non_dict_and_text_payload_handling():
    client = LotusCoreIngestionClient(
        base_url="http://lotus-performances-ingest", timeout_seconds=2.0
    )
    _FakeAsyncClient.queue_json(200, [{"preview": "row"}])
    _FakeAsyncClient.queue_text(503, "ingestion unavailable")

    preview_status, preview_payload = await client.preview_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        sample_size=1,
        correlation_id="corr-4",
    )
    commit_status, commit_payload = await client.commit_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        allow_partial=True,
        correlation_id="corr-4",
    )
    assert preview_status == 200
    assert preview_payload["detail"] == [{"preview": "row"}]
    assert commit_status == 503
    assert commit_payload["detail"] == "ingestion unavailable"
    assert _FakeAsyncClient.calls[0]["data"] == {
        "entity_type": "transactions",
        "sample_size": "1",
    }
    assert _FakeAsyncClient.calls[1]["data"] == {
        "entity_type": "transactions",
        "allow_partial": "true",
    }


@pytest.mark.asyncio
async def test_pas_ingestion_client_forwards_bundle_idempotency_header():
    client = LotusCoreIngestionClient(
        base_url="http://lotus-performances-ingest", timeout_seconds=2.0
    )
    _FakeAsyncClient.queue_json(202, {"status": "accepted"})

    status_ingest, _ = await client.ingest_portfolio_bundle(
        body={"portfolio": {"portfolio_id": "P1"}},
        correlation_id="corr-4",
        idempotency_key="bundle-idem-1001",
    )

    assert status_ingest == 202
    assert _FakeAsyncClient.calls[0]["headers"]["X-Idempotency-Key"] == "bundle-idem-1001"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_url"),
    [
        (
            "list_runs",
            {"params": {"portfolio_id": "P1", "status": None}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/runs",
        ),
        (
            "get_supportability_summary",
            {"correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/supportability/summary",
        ),
        (
            "get_capabilities",
            {
                "consumer_system": "lotus-gateway",
                "tenant_id": "default",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/integration/capabilities",
        ),
        (
            "list_outcome_reviews",
            {
                "params": {
                    "portfolio_id": "P1",
                    "state": None,
                    "source_system": "lotus-performance",
                    "source_type": "PortfolioRealizedTaxSummary:v1",
                    "source_scan_limit": 250,
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/outcome-reviews",
        ),
        (
            "get_outcome_review",
            {"outcome_review_id": "or_1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/outcome-reviews/or_1",
        ),
        (
            "get_outcome_review_supportability",
            {"outcome_review_id": "or_1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/outcome-reviews/or_1/supportability",
        ),
        (
            "get_outcome_review_report_input",
            {"outcome_review_id": "or_1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/outcome-reviews/or_1/report-input",
        ),
        (
            "get_outcome_review_ai_evidence_input",
            {"outcome_review_id": "or_1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/outcome-reviews/or_1/ai-evidence-input",
        ),
        (
            "get_run_outcome_review",
            {"rebalance_run_id": "rr_1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/runs/rr_1/outcome-review",
        ),
        (
            "get_construction_alternative_set",
            {"alternative_set_id": "cas_1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/construction/alternative-sets/cas_1",
        ),
        (
            "get_proof_pack",
            {"proof_pack_id": "dpp_rr_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proof-packs/dpp_rr_001",
        ),
        (
            "get_proof_pack_report_input",
            {"proof_pack_id": "dpp_rr_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proof-packs/dpp_rr_001/report-input",
        ),
        (
            "get_proof_pack_ai_evidence_input",
            {"proof_pack_id": "dpp_rr_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proof-packs/dpp_rr_001/ai-evidence-input",
        ),
        (
            "get_portfolio_memory",
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "params": {"limit": 50, "cursor": None},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/portfolio-memory/PB_SG_GLOBAL_BAL_001",
        ),
        (
            "search_portfolio_memory",
            {
                "params": {
                    "portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
                    "source_system": "lotus-performance",
                    "source_type": "PortfolioRealizedTaxSummary:v1",
                    "source_scan_limit": 250,
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/portfolio-memory/search",
        ),
        (
            "list_pm_operating_quality_score_runs",
            {"params": {"pm_id": "PM_SG_DPM_001"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/score-runs",
        ),
        (
            "list_pm_operating_quality_fairness_analyses",
            {"params": {"policy_id": "pmq_sg_dpm"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/fairness-analyses",
        ),
        (
            "list_pm_operating_quality_review_actions",
            {"params": {"target_type": "SCORE_RUN"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/review-actions",
        ),
        (
            "list_pm_operating_quality_summary_invocations",
            {"params": {"score_run_id": "pmq_run_001"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/summary-invocations",
        ),
        (
            "get_pm_operating_quality_score_run",
            {"score_run_id": "pmq_run_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/score-runs/pmq_run_001",
        ),
        (
            "get_pm_operating_quality_fairness_analysis",
            {"fairness_analysis_id": "pmq_fair_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/fairness-analyses/pmq_fair_001",
        ),
        (
            "get_pm_operating_quality_review_action",
            {"review_action_id": "pmq_review_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/review-actions/pmq_review_001",
        ),
        (
            "get_pm_operating_quality_summary_invocation",
            {"summary_invocation_id": "pmq_summary_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/summary-invocations/pmq_summary_001",
        ),
        (
            "list_pm_operating_quality_policies",
            {"params": {"policy_id": "pmq_sg_dpm"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/policies",
        ),
        (
            "get_pm_operating_quality_policy",
            {
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/policies/pmq_sg_dpm/versions/2026.05",
        ),
        (
            "list_wave_outcome_reviews",
            {"wave_id": "wave_1", "params": {"state": None}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/wave_1/outcome-reviews",
        ),
        (
            "list_waves",
            {
                "params": {"state": "HANDOFF_READY", "trigger_type": None},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves",
        ),
        (
            "get_wave",
            {"wave_id": "dwv_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/dwv_001",
        ),
        (
            "list_campaign_definitions",
            {
                "params": {"campaign_status": "ACTIVE", "campaign_id": None},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions",
        ),
        (
            "get_campaign_definition",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05",
        ),
        (
            "get_campaign_definition_lifecycle_events",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/lifecycle-events",
        ),
        (
            "get_campaign_definition_preview_readiness",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"requested_as_of_date": "2026-05-10", "actor_id": "pm_sg_1"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/preview-readiness",
        ),
        (
            "get_campaign_definition_launch_history",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"limit": 25, "offset": 0},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/launch-history",
        ),
        (
            "get_campaign_definition_launch_package",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {
                    "requested_as_of_date": "2026-05-10",
                    "actor_id": "pm_sg_1",
                    "correlation_id": "corr-launch",
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/launch-package",
        ),
        (
            "launch_campaign_definition",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {
                    "requested_as_of_date": "2026-05-10",
                    "actor_id": "pm_sg_1",
                    "correlation_id": "corr-launch",
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/launch",
        ),
        (
            "retire_campaign_definition",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {"actor_id": "pm_sg_1", "reason_code": "CAMPAIGN_RETIRED"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/retire",
        ),
        (
            "supersede_campaign_definition",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {
                    "actor_id": "pm_sg_1",
                    "reason_code": "CAMPAIGN_SUPERSEDED",
                    "replacement_campaign_version": "2026.06",
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/supersede",
        ),
        (
            "discover_campaigns",
            {
                "params": {"campaign_status": "ACTIVE", "active_on": "2026-05-16"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-discovery",
        ),
        (
            "get_campaign_operating_queue",
            {"params": {"campaign_id": "campaign-holdings-202605"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/campaign-operating-queue",
        ),
        (
            "get_campaign_approval_inbox",
            {"params": {"campaign_id": "campaign-holdings-202605"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/campaign-approval-inbox",
        ),
        (
            "get_campaign_workflow_board",
            {"params": {"campaign_id": "campaign-holdings-202605"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/campaign-workflow-board",
        ),
        (
            "get_campaign_assignment_plan",
            {"params": {"campaign_id": "campaign-holdings-202605"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/campaign-assignment-plan",
        ),
        (
            "get_campaign_workflow_automation",
            {"params": {"campaign_id": "campaign-holdings-202605"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/campaign-workflow-automation",
        ),
        (
            "list_campaign_approval_decisions",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"limit": 25},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/approval-decisions",
        ),
        (
            "create_campaign_approval_decision",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {"decision": "ACKNOWLEDGED"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/approval-decisions",
        ),
        (
            "list_campaign_assignment_actions",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"limit": 25},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/assignment-actions",
        ),
        (
            "create_campaign_assignment_action",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {"action_type": "ASSIGN"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/assignment-actions",
        ),
        (
            "list_campaign_assignment_tasks",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"limit": 25},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/assignment-tasks",
        ),
        (
            "create_campaign_assignment_task",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {"task_ref": "task-review-001"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/assignment-tasks",
        ),
        (
            "transition_campaign_assignment_task",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "task_ref": "task-review-001",
                "body": {"transition_type": "MARK_SUPPORTABLE"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/assignment-tasks/"
            "task-review-001/transitions",
        ),
        (
            "list_campaign_maker_checker_controls",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"limit": 25},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/maker-checker-controls",
        ),
        (
            "create_campaign_maker_checker_control",
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {"control_type": "MAKER_CHECKER_REVIEW"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
            "campaign-holdings-202605/versions/2026.05/maker-checker-controls",
        ),
        (
            "get_wave_items",
            {"wave_id": "dwv_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/dwv_001/items",
        ),
        (
            "get_wave_proof_pack_posture",
            {"wave_id": "dwv_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/dwv_001/proof-pack",
        ),
        (
            "get_wave_supportability",
            {"wave_id": "dwv_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/dwv_001/supportability",
        ),
        (
            "get_wave_report_input",
            {"wave_id": "dwv_001", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/dwv_001/report-input",
        ),
    ],
)
async def test_dpm_client_manage_routes(method_name, kwargs, expected_url):
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)
    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["url"] == expected_url
    if method_name == "get_capabilities":
        assert _FakeAsyncClient.calls[0]["params"] == {
            "consumer_system": "lotus-gateway",
            "tenant_id": "default",
        }
    elif method_name == "get_campaign_definition_launch_history":
        assert _FakeAsyncClient.calls[0]["params"] == kwargs["params"]
    elif method_name == "get_campaign_definition_preview_readiness":
        assert _FakeAsyncClient.calls[0]["params"] == kwargs["params"]


@pytest.mark.asyncio
async def test_dpm_client_capabilities_uses_gateway_consumer_for_manage_contract():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    status_code, payload = await client.get_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-sg",
        correlation_id="corr-workbench",
    )

    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["url"] == "http://dpm/api/v1/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "tenant-sg",
    }


@pytest.mark.asyncio
async def test_dpm_client_uses_only_canonical_manage_api_v1_contracts():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    calls = [
        (
            client.list_runs,
            {"params": {"portfolio_id": "P1"}, "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_supportability_summary,
            {"correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_capabilities,
            {
                "consumer_system": "lotus-workbench",
                "tenant_id": "default",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.preview_outcome_review,
            {"body": {"portfolio_id": "P1"}, "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.create_outcome_review,
            {"body": {"rebalance_run_id": "rr_1"}, "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.list_outcome_reviews,
            {"params": {"portfolio_id": "P1"}, "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_outcome_review,
            {"outcome_review_id": "or_1", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.refresh_outcome_review_sources,
            {
                "outcome_review_id": "or_1",
                "body": {"refresh_reason": "late fill"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_outcome_review_supportability,
            {"outcome_review_id": "or_1", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_outcome_review_report_input,
            {"outcome_review_id": "or_1", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_outcome_review_ai_evidence_input,
            {"outcome_review_id": "or_1", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_run_outcome_review,
            {"rebalance_run_id": "rr_1", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.list_wave_outcome_reviews,
            {
                "wave_id": "wave_1",
                "params": {"state": "READY"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.preview_wave,
            {
                "body": {"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.create_wave,
            {
                "body": {"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
                "idempotency_key": "idem-wave-canonical",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.list_waves,
            {"params": {"state": "HANDOFF_READY"}, "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_wave,
            {"wave_id": "dwv_001", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_wave_items,
            {"wave_id": "dwv_001", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.source_check_wave,
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.simulate_wave,
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1", "item_inputs": []},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.select_wave_item,
            {
                "wave_id": "dwv_001",
                "wave_item_id": "dwi_001",
                "body": {"alternative_id": "alt_1", "actor_id": "pm_sg_1"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.approve_wave,
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1", "reason_code": "APPROVED"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.stage_wave,
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "ops_sg_1", "reason_code": "STAGED"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.handoff_wave,
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "ops_sg_1", "reason_code": "HANDOFF_READY"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.cancel_wave,
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1", "reason_code": "CANCELLED"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_wave_proof_pack_posture,
            {"wave_id": "dwv_001", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_wave_supportability,
            {"wave_id": "dwv_001", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_wave_report_input,
            {"wave_id": "dwv_001", "correlation_id": "corr-rfc36-canonical"},
        ),
        (
            client.get_campaign_operating_queue,
            {
                "params": {"campaign_id": "campaign-holdings-202605"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.create_campaign_assignment_task,
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "body": {"task_ref": "task-review-001"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.transition_campaign_assignment_task,
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "task_ref": "task-review-001",
                "body": {"transition_type": "MARK_SUPPORTABLE"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.list_campaign_maker_checker_controls,
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "params": {"limit": 25},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.generate_construction_alternative_set,
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-rfc36-canonical",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_construction_alternative_set,
            {
                "alternative_set_id": "cas_1",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.select_construction_alternative,
            {
                "alternative_set_id": "cas_1",
                "body": {"alternative_id": "alt_1", "actor_id": "pm_1"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.generate_proof_pack,
            {
                "body": {"source_type": "REBALANCE_RUN", "rebalance_run_id": "rr_1"},
                "idempotency_key": "idem-rfc40-canonical",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_proof_pack,
            {
                "proof_pack_id": "dpp_rr_001",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_proof_pack_markdown,
            {
                "proof_pack_id": "dpp_rr_001",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_proof_pack_report_input,
            {
                "proof_pack_id": "dpp_rr_001",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_proof_pack_ai_evidence_input,
            {
                "proof_pack_id": "dpp_rr_001",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_portfolio_memory,
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "params": {"limit": 100},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.preview_pm_operating_quality_score_run,
            {
                "body": {"pm_id": "PM_SG_DPM_001", "policy_id": "pmq_sg_dpm"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.create_pm_operating_quality_score_run,
            {
                "body": {"pm_id": "PM_SG_DPM_001", "policy_id": "pmq_sg_dpm"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.list_pm_operating_quality_score_runs,
            {
                "params": {"pm_id": "PM_SG_DPM_001"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_pm_operating_quality_score_run,
            {
                "score_run_id": "pmq_run_001",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.put_pm_operating_quality_policy,
            {
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "body": {"policy_id": "pmq_sg_dpm", "policy_version": "2026.05"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.list_pm_operating_quality_policies,
            {
                "params": {"policy_id": "pmq_sg_dpm"},
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
        (
            client.get_pm_operating_quality_policy,
            {
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "correlation_id": "corr-rfc36-canonical",
            },
        ),
    ]
    for _method, _kwargs in calls:
        _FakeAsyncClient.queue_json(200, {"ok": True})

    for method, kwargs in calls:
        await method(**kwargs)

    forbidden_fragments = (
        "/dpm-execution-context",
        "/integration/capabilities",
        "/rebalance/runs",
        "/rebalance/supportability",
        "/construction/alternative-sets",
        "/dpm/",
    )
    manage_urls = [call["url"] for call in _FakeAsyncClient.calls]
    assert manage_urls
    assert all(url.startswith("http://dpm/api/v1/") for url in manage_urls)
    for url in manage_urls:
        path = url.removeprefix("http://dpm")
        assert not any(path.startswith(fragment) for fragment in forbidden_fragments)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_url"),
    [
        (
            "preview_outcome_review",
            {"body": {"portfolio_id": "P1"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/outcome-reviews/preview",
        ),
        (
            "create_outcome_review",
            {"body": {"rebalance_run_id": "rr_1"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/outcome-reviews",
        ),
        (
            "refresh_outcome_review_sources",
            {
                "outcome_review_id": "or_1",
                "body": {"refresh_reason": "late fill"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/outcome-reviews/or_1/refresh-sources",
        ),
        (
            "select_construction_alternative",
            {
                "alternative_set_id": "cas_1",
                "body": {"alternative_id": "alt_1", "actor_id": "pm_sg_1"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/construction/alternative-sets/cas_1/selections",
        ),
        (
            "generate_proof_pack",
            {
                "body": {"source_type": "REBALANCE_RUN", "rebalance_run_id": "rr_1"},
                "idempotency_key": "idem-proof-pack-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proof-packs",
        ),
        (
            "preview_wave",
            {"body": {"trigger_type": "EXPLICIT_PORTFOLIO_LIST"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/waves/preview",
        ),
        (
            "create_wave",
            {
                "body": {"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
                "idempotency_key": "idem-wave-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves",
        ),
        (
            "source_check_wave",
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/source-check",
        ),
        (
            "simulate_wave",
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1", "item_inputs": []},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/simulate",
        ),
        (
            "select_wave_item",
            {
                "wave_id": "dwv_001",
                "wave_item_id": "dwi_001",
                "body": {"alternative_id": "alt_1", "actor_id": "pm_sg_1"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/items/dwi_001/select",
        ),
        (
            "approve_wave",
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1", "reason_code": "APPROVED"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/approve",
        ),
        (
            "stage_wave",
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "ops_sg_1", "reason_code": "STAGED"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/stage",
        ),
        (
            "handoff_wave",
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "ops_sg_1", "reason_code": "HANDOFF_READY"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/handoff",
        ),
        (
            "cancel_wave",
            {
                "wave_id": "dwv_001",
                "body": {"actor_id": "pm_sg_1", "reason_code": "CANCELLED"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/waves/dwv_001/cancel",
        ),
        (
            "preview_pm_operating_quality_score_run",
            {"body": {"pm_id": "PM_SG_DPM_001"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/score-runs/preview",
        ),
        (
            "create_pm_operating_quality_score_run",
            {"body": {"pm_id": "PM_SG_DPM_001"}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/pm-operating-quality/score-runs",
        ),
        (
            "preview_pm_operating_quality_fairness_analysis",
            {
                "body": {"score_run_ids": ["pmq_run_001"], "segments": []},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/fairness-analyses/preview",
        ),
        (
            "create_pm_operating_quality_fairness_analysis",
            {
                "body": {"score_run_ids": ["pmq_run_001"], "segments": []},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/fairness-analyses",
        ),
        (
            "preview_pm_operating_quality_review_action",
            {
                "body": {"target_type": "SCORE_RUN", "target_id": "pmq_run_001"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/review-actions/preview",
        ),
        (
            "create_pm_operating_quality_review_action",
            {
                "body": {"target_type": "SCORE_RUN", "target_id": "pmq_run_001"},
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/review-actions",
        ),
        (
            "preview_pm_operating_quality_summary_invocation",
            {
                "body": {
                    "score_run_id": "pmq_run_001",
                    "review_action_id": "pmq_review_001",
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/summary-invocations/preview",
        ),
        (
            "create_pm_operating_quality_summary_invocation",
            {
                "body": {
                    "score_run_id": "pmq_run_001",
                    "review_action_id": "pmq_review_001",
                },
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/pm-operating-quality/summary-invocations",
        ),
    ],
)
async def test_dpm_client_outcome_review_command_routes(method_name, kwargs, expected_url):
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)
    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["method"] == "POST"
    assert _FakeAsyncClient.calls[0]["url"] == expected_url
    assert _FakeAsyncClient.calls[0]["json"] == kwargs["body"]
    if "idempotency_key" in kwargs:
        assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == kwargs["idempotency_key"]


@pytest.mark.asyncio
async def test_dpm_client_put_campaign_definition_uses_manage_contract():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    status_code, payload = await client.put_campaign_definition(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        body={"status": "ACTIVE"},
        correlation_id="corr-5",
    )

    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["method"] == "PUT"
    assert (
        _FakeAsyncClient.calls[0]["url"]
        == "http://dpm/api/v1/rebalance/waves/campaign-definitions/"
        "campaign-holdings-202605/versions/2026.05"
    )
    assert _FakeAsyncClient.calls[0]["json"] == {"status": "ACTIVE"}


@pytest.mark.asyncio
async def test_dpm_client_put_pm_operating_quality_policy_uses_manage_contract():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"policy_id": "pmq_sg_dpm"})

    status_code, payload = await client.put_pm_operating_quality_policy(
        policy_id="pmq_sg_dpm",
        policy_version="2026.05",
        body={"policy_id": "pmq_sg_dpm", "policy_version": "2026.05"},
        correlation_id="corr-5",
    )

    assert status_code == 200
    assert payload["policy_id"] == "pmq_sg_dpm"
    assert _FakeAsyncClient.calls[0]["method"] == "PUT"
    assert (
        _FakeAsyncClient.calls[0]["url"]
        == "http://dpm/api/v1/rebalance/pm-operating-quality/policies/"
        "pmq_sg_dpm/versions/2026.05"
    )
    assert _FakeAsyncClient.calls[0]["json"] == {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
    }


@pytest.mark.asyncio
async def test_dpm_client_construction_generate_route_forwards_idempotency_key():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"alternative_set_id": "cas_1"})

    status_code, payload = await client.generate_construction_alternative_set(
        body={"input_mode": "stateless"},
        idempotency_key="idem-construction-1",
        correlation_id="corr-construction-1",
    )

    assert status_code == 200
    assert payload["alternative_set_id"] == "cas_1"
    assert _FakeAsyncClient.calls[0]["method"] == "POST"
    assert (
        _FakeAsyncClient.calls[0]["url"]
        == "http://dpm/api/v1/construction/alternative-sets/generate"
    )
    assert _FakeAsyncClient.calls[0]["json"] == {"input_mode": "stateless"}
    assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == "idem-construction-1"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-construction-1"


@pytest.mark.asyncio
async def test_dpm_client_proof_pack_markdown_preserves_text_payload():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(200, "# DPM proof pack\n")

    status_code, markdown, error_payload = await client.get_proof_pack_markdown(
        proof_pack_id="dpp_rr_001",
        correlation_id="corr-proof-pack-md-client-1",
    )

    assert status_code == 200
    assert markdown == "# DPM proof pack\n"
    assert error_payload == {}
    assert _FakeAsyncClient.calls[0]["method"] == "GET"
    assert (
        _FakeAsyncClient.calls[0]["url"]
        == "http://dpm/api/v1/rebalance/proof-packs/dpp_rr_001/summary.md"
    )
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == (
        "corr-proof-pack-md-client-1"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_url", "expected_method"),
    [
        (
            "get_command_center",
            {
                "params": {
                    "tenant_id": "default",
                    "portfolio_manager_id": "PM_SG_DPM_001",
                    "book_id": None,
                },
                "correlation_id": "corr-rfc38",
            },
            "http://dpm/api/v1/dpm/command-center",
            "GET",
        ),
        (
            "run_monitoring_once",
            {
                "body": {"mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"]},
                "correlation_id": "corr-rfc38",
            },
            "http://dpm/api/v1/dpm/monitoring/run-once",
            "POST",
        ),
        (
            "list_monitoring_runs",
            {
                "params": {"status_filter": "SUCCEEDED", "cursor": None},
                "correlation_id": "corr-rfc38",
            },
            "http://dpm/api/v1/dpm/monitoring/runs",
            "GET",
        ),
        (
            "get_monitoring_run",
            {"monitoring_run_id": "dmr_1", "correlation_id": "corr-rfc38"},
            "http://dpm/api/v1/dpm/monitoring/runs/dmr_1",
            "GET",
        ),
        (
            "list_monitoring_exceptions",
            {
                "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "state": "ACTIVE"},
                "correlation_id": "corr-rfc38",
            },
            "http://dpm/api/v1/dpm/exceptions",
            "GET",
        ),
        (
            "resolve_monitoring_exception",
            {
                "exception_id": "me_1",
                "body": {"resolution_reason": "SOURCE_REPAIRED"},
                "correlation_id": "corr-rfc38",
            },
            "http://dpm/api/v1/dpm/exceptions/me_1/resolve",
            "POST",
        ),
        (
            "get_mandate_by_portfolio",
            {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "correlation_id": "corr-rfc38"},
            "http://dpm/api/v1/mandates/by-portfolio/PB_SG_GLOBAL_BAL_001",
            "GET",
        ),
        (
            "get_mandate",
            {"mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001", "correlation_id": "corr-rfc38"},
            "http://dpm/api/v1/mandates/MANDATE_PB_SG_GLOBAL_BAL_001",
            "GET",
        ),
        (
            "get_mandate_health",
            {"mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001", "correlation_id": "corr-rfc38"},
            "http://dpm/api/v1/mandates/MANDATE_PB_SG_GLOBAL_BAL_001/health",
            "GET",
        ),
        (
            "get_mandate_diff",
            {
                "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
                "params": {"from_version": "2", "to_version": "3"},
                "correlation_id": "corr-rfc38",
            },
            "http://dpm/api/v1/mandates/MANDATE_PB_SG_GLOBAL_BAL_001/diff",
            "GET",
        ),
    ],
)
async def test_dpm_client_rfc38_command_center_routes(
    method_name,
    kwargs,
    expected_url,
    expected_method,
):
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)

    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["method"] == expected_method
    assert _FakeAsyncClient.calls[0]["url"] == expected_url
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-rfc38"
    if expected_method == "GET" and "params" in kwargs:
        assert None not in _FakeAsyncClient.calls[0]["params"].values()
    if expected_method == "POST":
        assert _FakeAsyncClient.calls[0]["json"] == kwargs["body"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_url"),
    [
        (
            "simulate_proposal",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/simulate",
        ),
        (
            "create_proposal",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-2",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals",
        ),
        (
            "list_proposals",
            {"params": {"portfolio_id": "P1", "status": None}, "correlation_id": "corr-5"},
            "http://advise/advisory/proposals",
        ),
        (
            "get_proposal",
            {"proposal_id": "PR-1", "include_evidence": True, "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1",
        ),
        (
            "get_proposal_version",
            {
                "proposal_id": "PR-1",
                "version_no": 2,
                "include_evidence": False,
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/versions/2",
        ),
        (
            "create_proposal_version",
            {
                "proposal_id": "PR-1",
                "body": {"changes": []},
                "idempotency_key": "idem-3",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/versions",
        ),
        (
            "transition_proposal",
            {
                "proposal_id": "PR-1",
                "body": {"event": "submit"},
                "idempotency_key": "idem-transition-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/transitions",
        ),
        (
            "record_approval",
            {
                "proposal_id": "PR-1",
                "body": {"decision": "approve"},
                "idempotency_key": "idem-approval-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/approvals",
        ),
        (
            "get_workflow_events",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1/workflow-events",
        ),
        (
            "get_approvals",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1/approvals",
        ),
        (
            "get_proposal_lineage",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1/lineage",
        ),
        (
            "review_proposal_narrative",
            {
                "proposal_id": "PR-1",
                "version_no": 2,
                "body": {"action": "APPROVE", "reviewed_by": "compliance_1"},
                "idempotency_key": "idem-narrative-review-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/versions/2/narrative/review",
        ),
        (
            "create_report_request",
            {
                "proposal_id": "PR-1",
                "body": {
                    "report_type": "PORTFOLIO_REVIEW",
                    "include_reviewed_narrative": True,
                },
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/report-requests",
        ),
        (
            "get_delivery_summary",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1/delivery-summary",
        ),
        (
            "get_delivery_events",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1/delivery-events",
        ),
        (
            "create_proposal_async",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-async-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/async",
        ),
        (
            "create_proposal_version_async",
            {
                "proposal_id": "PR-1",
                "body": {"changes": []},
                "idempotency_key": "idem-version-async-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/versions/async",
        ),
        (
            "get_proposal_operation",
            {"operation_id": "op-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/operations/op-1",
        ),
        (
            "get_proposal_operation_by_correlation",
            {"operation_correlation_id": "op-corr-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/operations/by-correlation/op-corr-1",
        ),
        (
            "get_execution_status",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://advise/advisory/proposals/PR-1/execution-status",
        ),
        (
            "record_execution_update",
            {
                "proposal_id": "PR-1",
                "body": {"status": "SUBMITTED"},
                "idempotency_key": "idem-execution-update-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/execution-updates",
        ),
        (
            "create_proposal_memo",
            {
                "proposal_id": "PR-1",
                "version_no": 2,
                "body": {"audience": "COMMITTEE"},
                "idempotency_key": "idem-memo-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/versions/2/memo",
        ),
        (
            "request_proposal_memo_report_package",
            {
                "proposal_id": "PR-1",
                "version_no": 2,
                "body": {"package_type": "INVESTMENT_REVIEW"},
                "idempotency_key": "idem-memo-report-1",
                "correlation_id": "corr-5",
            },
            "http://advise/advisory/proposals/PR-1/versions/2/memo/report-packages",
        ),
    ],
)
async def test_advise_client_proposal_routes(method_name, kwargs, expected_url):
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)
    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["url"] == expected_url
    if "idempotency_key" in kwargs:
        assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == kwargs["idempotency_key"]


@pytest.mark.asyncio
async def test_advise_client_bank_demo_proof_routes_preserve_correlation_and_body():
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {"scenario_id": "RFC28_BANK_DEMO_CLIENT_READY_PROOF_CANONICAL"},
    )
    _FakeAsyncClient.queue_json(200, {"claims": []})
    _FakeAsyncClient.queue_json(
        200,
        {"proof_pack": {"proof_marker": "BANK_DEMO_PROOF_PACK_CREATED"}},
    )

    await client.get_bank_demo_proof_scenario_contract(correlation_id="corr-rfc0028")
    await client.get_bank_demo_supported_claim_register(correlation_id="corr-rfc0028")
    await client.build_bank_demo_proof_pack(
        body={"live_runtime_payload": {"parity": {}}, "runtime_posture": {"endpoints": []}},
        correlation_id="corr-rfc0028",
    )

    assert [call["url"] for call in _FakeAsyncClient.calls] == [
        "http://advise/advisory/bank-demo-proof/scenario-contract",
        "http://advise/advisory/bank-demo-proof/supported-claim-register",
        "http://advise/advisory/bank-demo-proof/proof-packs",
    ]
    assert [call["method"] for call in _FakeAsyncClient.calls] == ["GET", "GET", "POST"]
    assert all(
        call["headers"]["X-Correlation-Id"] == "corr-rfc0028" for call in _FakeAsyncClient.calls
    )
    assert _FakeAsyncClient.calls[2]["json"] == {
        "live_runtime_payload": {"parity": {}},
        "runtime_posture": {"endpoints": []},
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_method", "expected_url"),
    [
        (
            "list_policy_packs",
            {"correlation_id": "corr-policy"},
            "GET",
            "http://advise/advisory/policy-packs",
        ),
        (
            "get_policy_pack_version",
            {
                "policy_pack_id": "policy_pack_sg_private_banking",
                "policy_version": "2026.05",
                "correlation_id": "corr-policy",
            },
            "GET",
            "http://advise/advisory/policy-packs/policy_pack_sg_private_banking/versions/2026.05",
        ),
        (
            "validate_policy_pack_version",
            {
                "policy_pack_id": "policy_pack_sg_private_banking",
                "policy_version": "2026.05",
                "body": {"validated_by": "policy_admin_1"},
                "idempotency_key": "idem-policy-validate",
                "correlation_id": "corr-policy",
            },
            "POST",
            "http://advise/advisory/policy-packs/"
            "policy_pack_sg_private_banking/versions/2026.05/validate",
        ),
        (
            "create_policy_evaluation",
            {
                "proposal_id": "pp_001",
                "proposal_version_id": "ppv_001",
                "body": {"requested_by": "advisor_1"},
                "idempotency_key": "idem-policy-evaluation",
                "correlation_id": "corr-policy",
            },
            "POST",
            "http://advise/advisory/proposals/pp_001/versions/ppv_001/policy-evaluations",
        ),
        (
            "request_policy_ai_evidence",
            {
                "evaluation_id": "pev_001",
                "body": {"requested_by": "advisor_1"},
                "idempotency_key": "idem-policy-ai",
                "correlation_id": "corr-policy",
            },
            "POST",
            "http://advise/advisory/policy-evaluations/pev_001/ai-evidence",
        ),
    ],
)
async def test_advise_client_policy_routes_forward_correlation_and_idempotency(
    method_name,
    kwargs,
    expected_method,
    expected_url,
):
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)

    assert status_code == 200
    assert payload["ok"] is True
    call = _FakeAsyncClient.calls[0]
    assert call["method"] == expected_method
    assert call["url"] == expected_url
    assert call["headers"]["X-Correlation-Id"] == "corr-policy"
    if expected_method == "POST":
        assert call["json"] == kwargs["body"]
    if "idempotency_key" in kwargs:
        assert call["headers"]["Idempotency-Key"] == kwargs["idempotency_key"]


@pytest.mark.asyncio
async def test_advise_client_policy_review_queue_omits_empty_filters() -> None:
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    status_code, _ = await client.get_policy_review_queue(
        evaluation_status=None,
        portfolio_id=None,
        correlation_id="corr-policy-queue",
    )

    assert status_code == 200
    assert _FakeAsyncClient.calls[0]["url"] == (
        "http://advise/advisory/policy-evaluations/review-queue"
    )
    assert _FakeAsyncClient.calls[0]["params"] == {}
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-policy-queue"


@pytest.mark.asyncio
async def test_advise_client_policy_review_queue_forwards_portfolio_filter() -> None:
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    status_code, _ = await client.get_policy_review_queue(
        evaluation_status="PENDING_REVIEW",
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-policy-queue",
    )

    assert status_code == 200
    assert _FakeAsyncClient.calls[0]["url"] == (
        "http://advise/advisory/policy-evaluations/review-queue"
    )
    assert _FakeAsyncClient.calls[0]["params"] == {
        "evaluation_status": "PENDING_REVIEW",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
    }


@pytest.mark.asyncio
async def test_advise_client_advisor_cockpit_routes_forward_filters_and_idempotency() -> None:
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    for _ in range(7):
        _FakeAsyncClient.queue_json(200, {"ok": True})

    action_filters = {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "advisor_id": "advisor_sg_001",
        "role": "ADVISOR",
        "limit": 25,
        "cursor": None,
    }
    acknowledgement_filters = {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "advisor_id": None,
        "role": "ADVISOR",
    }

    await client.list_advisor_cockpit_actions(action_filters, correlation_id="corr-cockpit")
    await client.list_advisor_cockpit_preparation_packets(
        action_filters,
        correlation_id="corr-cockpit",
    )
    await client.get_advisor_cockpit_action(
        "cockpit_action_001",
        acknowledgement_filters,
        correlation_id="corr-cockpit",
    )
    await client.get_advisor_cockpit_snapshot(
        acknowledgement_filters,
        correlation_id="corr-cockpit",
    )
    await client.get_advisor_cockpit_supportability(
        acknowledgement_filters,
        correlation_id="corr-cockpit",
    )
    await client.acknowledge_advisor_cockpit_action(
        "cockpit_action_001",
        body={"action_item_version": 1, "acknowledged_by": "advisor_sg_001"},
        params=acknowledgement_filters,
        idempotency_key="idem-cockpit-ack",
        correlation_id="corr-cockpit",
    )
    await client.evaluate_advisor_cockpit_house_view_cohort(
        body={
            "tactical_view": {"tactical_view_id": "thv_2026_05_asia_duration"},
            "candidate_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
        },
        correlation_id="corr-cockpit",
    )

    assert _FakeAsyncClient.calls[0]["method"] == "GET"
    assert _FakeAsyncClient.calls[0]["url"] == "http://advise/advisory/cockpit/actions"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "advisor_id": "advisor_sg_001",
        "role": "ADVISOR",
        "limit": 25,
    }
    assert _FakeAsyncClient.calls[1]["url"] == (
        "http://advise/advisory/cockpit/preparation-packets"
    )
    assert _FakeAsyncClient.calls[1]["params"] == {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "advisor_id": "advisor_sg_001",
        "role": "ADVISOR",
        "limit": 25,
    }
    assert _FakeAsyncClient.calls[2]["url"] == (
        "http://advise/advisory/cockpit/actions/cockpit_action_001"
    )
    assert _FakeAsyncClient.calls[3]["url"] == "http://advise/advisory/cockpit/snapshot"
    assert _FakeAsyncClient.calls[4]["url"] == "http://advise/advisory/cockpit/supportability"
    acknowledgement_call = _FakeAsyncClient.calls[5]
    assert acknowledgement_call["method"] == "POST"
    assert acknowledgement_call["url"] == (
        "http://advise/advisory/cockpit/actions/cockpit_action_001/acknowledgements"
    )
    assert acknowledgement_call["params"] == {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "role": "ADVISOR",
    }
    assert acknowledgement_call["json"] == {
        "action_item_version": 1,
        "acknowledged_by": "advisor_sg_001",
    }
    assert acknowledgement_call["headers"]["Idempotency-Key"] == "idem-cockpit-ack"
    house_view_call = _FakeAsyncClient.calls[6]
    assert house_view_call["method"] == "POST"
    assert house_view_call["url"] == ("http://advise/advisory/tactical-house-view/cohorts/evaluate")
    assert house_view_call["json"] == {
        "tactical_view": {"tactical_view_id": "thv_2026_05_asia_duration"},
        "candidate_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
    }
    for call in _FakeAsyncClient.calls:
        assert call["headers"]["X-Correlation-Id"] == "corr-cockpit"


@pytest.mark.asyncio
async def test_advise_client_capabilities_uses_gateway_consumer_and_tenant_context():
    client = AdviseClient(base_url="http://advise", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    status_code, payload = await client.get_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-sg",
        correlation_id="corr-workbench",
    )

    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["url"] == "http://advise/platform/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "tenant-sg",
    }


@pytest.mark.asyncio
async def test_dpm_client_has_no_stale_proposal_routes():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)

    assert not hasattr(client, "simulate_proposal")
    assert not hasattr(client, "create_proposal")
    assert not hasattr(client, "list_proposals")
    assert not hasattr(client, "get_proposal")


@pytest.mark.asyncio
async def test_dpm_client_non_json_and_non_dict_payload_handling():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(502, "dpm unavailable")
    _FakeAsyncClient.queue_json(200, ["not-dict"])

    status_one, payload_one = await client.get_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-5",
    )
    status_two, payload_two = await client.list_runs(
        params={"portfolio_id": "P1"},
        correlation_id="corr-5",
    )
    assert status_one == 502
    assert payload_one["detail"] == "dpm unavailable"
    assert status_two == 200
    assert payload_two["detail"] == ["not-dict"]


@pytest.mark.asyncio
async def test_dpm_client_emits_safe_fanout_metrics_for_manage_routes(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(503, {"detail": "upstream unavailable", "portfolio_id": "P1"})

    status_code, payload = await client.list_runs(
        params={"portfolio_id": "P1"},
        correlation_id="corr-dpm-observed",
    )

    assert status_code == 503
    assert payload["detail"] == "upstream unavailable"
    [record] = _fanout_records(caplog.records, service="lotus-manage")
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.fanout.degraded"
    assert fields["route"] == "workbench-analytics"
    assert fields["service"] == "lotus-manage"
    assert fields["operation"] == "manage.rebalance.runs.list"
    assert fields["state"] == "degraded"
    assert fields["reason"] == "UPSTREAM_UNAVAILABLE"
    assert fields["status_class"] == "5xx"
    assert "portfolio_id" not in fields
    assert "request_body" not in fields
    assert "response_body" not in fields


@pytest.mark.asyncio
async def test_reporting_client_handles_non_dict_payload():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, [{"metric": "market_value_base"}])
    status_code, payload = await client.get_portfolio_snapshot(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        correlation_id="corr-6",
    )
    assert status_code == 200
    assert payload["detail"] == [{"metric": "market_value_base"}]


@pytest.mark.asyncio
async def test_reporting_client_summary_and_review_routes():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "lotus-report"})
    _FakeAsyncClient.queue_json(200, {"scope": {"portfolio_id": "P1"}})
    _FakeAsyncClient.queue_json(200, {"portfolio_id": "P1", "overview": {}})

    capabilities_status, capabilities_payload = await client.get_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-7",
    )
    summary_status, summary_payload = await client.post_portfolio_summary(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24", "sections": ["WEALTH"]},
        correlation_id="corr-7",
    )
    review_status, review_payload = await client.post_portfolio_review(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24", "sections": ["OVERVIEW"]},
        correlation_id="corr-7",
    )

    assert capabilities_status == 200
    assert capabilities_payload["sourceService"] == "lotus-report"
    assert summary_status == 200
    assert summary_payload["scope"]["portfolio_id"] == "P1"
    assert review_status == 200
    assert review_payload["portfolio_id"] == "P1"
    assert _FakeAsyncClient.calls[0]["url"] == "http://ras/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-7"
    assert _FakeAsyncClient.calls[1]["url"] == "http://ras/reports/portfolios/P1/summary"
    assert _FakeAsyncClient.calls[1]["json"] == {
        "as_of_date": "2026-02-24",
        "sections": ["WEALTH"],
    }
    assert _FakeAsyncClient.calls[1]["headers"]["X-Correlation-Id"] == "corr-7"
    assert _FakeAsyncClient.calls[2]["url"] == "http://ras/reports/portfolios/P1/review"
    assert _FakeAsyncClient.calls[2]["json"] == {
        "as_of_date": "2026-02-24",
        "sections": ["OVERVIEW"],
    }
    assert _FakeAsyncClient.calls[2]["headers"]["X-Correlation-Id"] == "corr-7"


@pytest.mark.asyncio
async def test_reporting_client_report_job_routes_forward_governed_headers():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(202, {"report_job_id": "rjob_1"})
    _FakeAsyncClient.queue_json(200, {"status": "accepted"})
    _FakeAsyncClient.queue_json(200, {"events": []})
    _FakeAsyncClient.queue_json(200, {"status": "cancelled"})

    submit_status, submit_payload = await client.submit_portfolio_review_job(
        payload={
            "portfolio_scope": {"portfolio_ids": ["P1"]},
            "as_of_date": "2026-04-22",
            "requested_output_formats": ["json"],
        },
        idempotency_key="idem-job-1",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Role": "advisor",
        },
        correlation_id="corr-job-1",
    )
    status_code, status_payload = await client.get_report_job(
        job_id="rjob_1",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Role": "advisor",
        },
        correlation_id="corr-job-1",
    )
    events_status, events_payload = await client.get_report_job_events(
        job_id="rjob_1",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Role": "advisor",
        },
        correlation_id="corr-job-1",
    )
    cancel_status, cancel_payload = await client.cancel_report_job(
        job_id="rjob_1",
        caller_headers={"X-Actor-Id": "advisor-123"},
        correlation_id="corr-job-1",
    )

    assert submit_status == 202
    assert submit_payload["report_job_id"] == "rjob_1"
    assert status_code == 200
    assert status_payload["status"] == "accepted"
    assert events_status == 200
    assert events_payload["events"] == []
    assert cancel_status == 200
    assert cancel_payload["status"] == "cancelled"
    assert _FakeAsyncClient.calls[0]["url"] == "http://ras/reports/portfolio-reviews"
    assert _FakeAsyncClient.calls[0]["json"]["portfolio_scope"] == {"portfolio_ids": ["P1"]}
    assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == "idem-job-1"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Actor-Id"] == "advisor-123"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Tenant-Id"] == "tenant-sg"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-job-1"
    assert _FakeAsyncClient.calls[1]["url"] == "http://ras/reports/jobs/rjob_1"
    assert _FakeAsyncClient.calls[1]["headers"]["X-Actor-Id"] == "advisor-123"
    assert _FakeAsyncClient.calls[1]["headers"]["X-Tenant-Id"] == "tenant-sg"
    assert _FakeAsyncClient.calls[1]["headers"]["X-Correlation-Id"] == "corr-job-1"
    assert _FakeAsyncClient.calls[2]["url"] == "http://ras/reports/jobs/rjob_1/events"
    assert _FakeAsyncClient.calls[2]["headers"]["X-Actor-Id"] == "advisor-123"
    assert _FakeAsyncClient.calls[2]["headers"]["X-Tenant-Id"] == "tenant-sg"
    assert _FakeAsyncClient.calls[2]["headers"]["X-Correlation-Id"] == "corr-job-1"
    assert _FakeAsyncClient.calls[3]["url"] == "http://ras/reports/jobs/rjob_1/cancel"
    assert _FakeAsyncClient.calls[3]["headers"]["X-Actor-Id"] == "advisor-123"


@pytest.mark.asyncio
async def test_reporting_client_outcome_review_report_job_route_forwards_governed_headers():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        202,
        {
            "report_request_id": "rrq_outcome_1",
            "report_job_id": "rjob_outcome_1",
            "status": "accepted",
        },
    )

    status_code, payload = await client.submit_outcome_review_report_job(
        payload={"outcome_report_input": {"outcome_review_id": "dor_001"}},
        idempotency_key="outcome-review-dor_001-pdf",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
        correlation_id="corr-outcome-report",
    )

    assert status_code == 202
    assert payload["report_job_id"] == "rjob_outcome_1"
    assert _FakeAsyncClient.calls[0]["url"] == "http://ras/reports/outcome-reviews"
    assert _FakeAsyncClient.calls[0]["json"] == {
        "outcome_report_input": {"outcome_review_id": "dor_001"}
    }
    assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == ("outcome-review-dor_001-pdf")
    assert _FakeAsyncClient.calls[0]["headers"]["X-Actor-Id"] == "advisor-123"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-outcome-report"


@pytest.mark.asyncio
async def test_reporting_client_report_batch_routes_forward_governed_headers():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    caller_headers = {
        "X-Actor-Id": "operator-123",
        "X-Caller-Application": "lotus-gateway",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
    }
    _FakeAsyncClient.queue_json(202, {"batch_id": "rbch_1"})
    _FakeAsyncClient.queue_json(200, {"batch_id": "rbch_1", "status": "materialized"})
    _FakeAsyncClient.queue_json(200, {"batch_id": "rbch_1", "status": "paused"})
    _FakeAsyncClient.queue_json(200, {"batch_id": "rbch_1", "status": "completed"})
    _FakeAsyncClient.queue_json(200, {"scheduler_id": "scheduler-1", "schedule_count": 1})
    _FakeAsyncClient.queue_json(200, {"scheduler_id": "scheduler-1", "materialized_count": 1})

    create_status, create_payload = await client.create_report_batch(
        payload={"selector_mode": "explicit_portfolio_list"},
        idempotency_key="idem-batch-1",
        caller_headers=caller_headers,
        correlation_id="corr-batch-1",
    )
    status_code, status_payload = await client.get_report_batch(
        batch_id="rbch_1",
        caller_headers=caller_headers,
        correlation_id="corr-batch-1",
    )
    pause_status, pause_payload = await client.control_report_batch(
        batch_id="rbch_1",
        action="pause",
        caller_headers=caller_headers,
        correlation_id="corr-batch-1",
    )
    run_status, run_payload = await client.control_report_batch(
        batch_id="rbch_1",
        action="run-once",
        caller_headers=caller_headers,
        correlation_id="corr-batch-1",
        payload={"worker_id": "worker-1"},
    )
    schedules_status, schedules_payload = await client.list_report_batch_schedules(
        caller_headers=caller_headers,
        correlation_id="corr-batch-1",
    )
    run_due_status, run_due_payload = await client.run_due_report_batch_schedules(
        payload={"pass_sequence": 2},
        caller_headers=caller_headers,
        correlation_id="corr-batch-1",
    )

    assert create_status == 202
    assert create_payload["batch_id"] == "rbch_1"
    assert status_code == 200
    assert status_payload["status"] == "materialized"
    assert pause_status == 200
    assert pause_payload["status"] == "paused"
    assert run_status == 200
    assert run_payload["status"] == "completed"
    assert schedules_status == 200
    assert schedules_payload["schedule_count"] == 1
    assert run_due_status == 200
    assert run_due_payload["materialized_count"] == 1
    assert _FakeAsyncClient.calls[0]["url"] == "http://ras/reports/batches"
    assert _FakeAsyncClient.calls[0]["json"] == {"selector_mode": "explicit_portfolio_list"}
    assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == "idem-batch-1"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Actor-Id"] == "operator-123"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Caller-Application"] == "lotus-gateway"
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-batch-1"
    assert _FakeAsyncClient.calls[1]["url"] == "http://ras/reports/batches/rbch_1"
    assert _FakeAsyncClient.calls[2]["url"] == "http://ras/reports/batches/rbch_1:pause"
    assert _FakeAsyncClient.calls[3]["url"] == "http://ras/reports/batches/rbch_1:run-once"
    assert _FakeAsyncClient.calls[3]["json"] == {"worker_id": "worker-1"}
    assert _FakeAsyncClient.calls[4]["url"] == "http://ras/reports/batch-schedules"
    assert _FakeAsyncClient.calls[4]["headers"]["X-Actor-Id"] == "operator-123"
    assert _FakeAsyncClient.calls[5]["url"] == "http://ras/reports/batch-schedules:run-due"
    assert _FakeAsyncClient.calls[5]["json"] == {"pass_sequence": 2}


@pytest.mark.asyncio
async def test_reporting_client_snapshot_request_uses_live_aggregation_query_contract():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"rows": []})

    status_code, payload = await client.get_portfolio_snapshot(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        correlation_id="corr-8",
    )

    assert status_code == 200
    assert payload["rows"] == []
    assert _FakeAsyncClient.calls[0]["url"] == "http://ras/aggregations/portfolios/P1"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "as_of_date": "2026-02-24",
        "live": "true",
    }
    assert _FakeAsyncClient.calls[0]["headers"]["X-Correlation-Id"] == "corr-8"


@pytest.mark.asyncio
async def test_reporting_client_summary_review_non_json_payloads():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(502, "summary failure")
    _FakeAsyncClient.queue_json(200, ["review-item"])

    summary_status, summary_payload = await client.post_portfolio_summary(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24"},
        correlation_id="corr-7",
    )
    review_status, review_payload = await client.post_portfolio_review(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24"},
        correlation_id="corr-7",
    )
    assert summary_status == 502
    assert summary_payload["detail"] == "summary failure"
    assert review_status == 200
    assert review_payload["detail"] == ["review-item"]


@pytest.mark.asyncio
async def test_reporting_client_emits_safe_fanout_metrics_without_runtime_ids(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        200,
        {
            "state": "partial",
            "partial_failures": [{"source_service": "lotus-report"}],
            "request_body": {"portfolio_id": "P1"},
        },
    )

    status_code, payload = await client.get_report_job(
        job_id="rjob_sensitive_1",
        caller_headers={"X-Actor-Id": "advisor-123"},
        correlation_id="corr-report-observed",
    )

    assert status_code == 200
    assert payload["state"] == "partial"
    [record] = _fanout_records(caplog.records, service="lotus-report")
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.fanout.degraded"
    assert fields["operation"] == "report.jobs.get"
    assert fields["state"] == "partial"
    assert fields["status_class"] == "2xx"
    assert fields["partial_failure_count"] == 1
    assert "rjob_sensitive_1" not in fields.values()
    assert "portfolio_id" not in fields


@pytest.mark.asyncio
async def test_archive_client_metadata_and_download_routes_forward_archive_context():
    client = ArchiveClient(base_url="http://archive", timeout_seconds=2.0)
    caller_headers = {
        "X-Actor-Id": "advisor-123",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Role": "advisor",
        "X-Booking-Center-Code": "SG",
    }
    _FakeAsyncClient.queue_json(200, {"document_id": "doc_1"})
    _FakeAsyncClient.queue_json(200, {"document_id": "doc_2"})
    _FakeAsyncClient.queue_bytes(
        200,
        b"%PDF-1.4",
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="doc_1.pdf"',
            "X-Document-Checksum-Algorithm": "sha256",
            "X-Document-Checksum": "abc123",
        },
    )

    metadata_status, metadata_payload = await client.get_document_metadata(
        document_id="doc_1",
        caller_headers=caller_headers,
        correlation_id="corr-archive-1",
    )
    current_status, current_payload = await client.get_document_metadata(
        document_id="doc_1",
        caller_headers=caller_headers,
        correlation_id="corr-archive-1",
        current=True,
    )
    download_status, content, headers, error_payload = await client.download_document(
        document_id="doc_1",
        caller_headers=caller_headers,
        correlation_id="corr-archive-1",
    )

    assert metadata_status == 200
    assert metadata_payload["document_id"] == "doc_1"
    assert current_status == 200
    assert current_payload["document_id"] == "doc_2"
    assert download_status == 200
    assert content == b"%PDF-1.4"
    assert headers["content-type"] == "application/pdf"
    assert error_payload == {}
    assert _FakeAsyncClient.calls[0]["url"] == "http://archive/documents/doc_1"
    assert _FakeAsyncClient.calls[1]["url"] == "http://archive/documents/doc_1/current"
    assert _FakeAsyncClient.calls[2]["url"] == "http://archive/documents/doc_1/download"
    for call in _FakeAsyncClient.calls:
        assert call["headers"]["X-Caller-Service"] == "lotus-gateway"
        assert call["headers"]["X-Actor-Type"] == "advisor"
        assert call["headers"]["X-Actor-Id"] == "advisor-123"
        assert call["headers"]["X-Tenant-Id"] == "tenant-sg"
        assert call["headers"]["X-Region"] == "APAC"
        assert call["headers"]["X-Booking-Center-Code"] == "SG"
        assert call["headers"]["X-Correlation-Id"] == "corr-archive-1"


@pytest.mark.asyncio
async def test_archive_client_download_returns_error_payload_without_binary_leakage():
    client = ArchiveClient(base_url="http://archive", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        404,
        {
            "error": {
                "code": "document_binary_missing",
                "message": "The archived document binary could not be found.",
            }
        },
    )

    status_code, content, headers, error_payload = await client.download_document(
        document_id="doc_1",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
        correlation_id="corr-archive-2",
    )

    assert status_code == 404
    assert b"document_binary_missing" in content
    assert headers["content-type"] == "application/json"
    assert error_payload["error"]["code"] == "document_binary_missing"


@pytest.mark.asyncio
async def test_archive_client_emits_safe_binary_fanout_metrics(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = ArchiveClient(base_url="http://archive", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        404,
        {"error": {"code": "document_binary_missing", "document_id": "doc_sensitive_1"}},
    )

    status_code, _, _, error_payload = await client.download_document(
        document_id="doc_sensitive_1",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
        correlation_id="corr-archive-observed",
    )

    assert status_code == 404
    assert error_payload["error"]["code"] == "document_binary_missing"
    [record] = _fanout_records(caplog.records, service="lotus-archive")
    fields = record.extra_fields
    assert fields["operation"] == "archive.documents.download"
    assert fields["status_class"] == "4xx"
    assert fields["state"] == "error"
    assert fields["error_category"] == "upstream_error"
    assert "doc_sensitive_1" not in fields.values()
    assert "document_id" not in fields


@pytest.mark.asyncio
async def test_lotus_core_query_client_posts_benchmark_catalog_request():
    client = LotusCoreQueryClient(
        base_url="http://core-query",
        control_plane_base_url="http://core-control",
        timeout_seconds=2.0,
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "records": [
                {
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_name": "Global Balanced 60/40",
                }
            ]
        },
    )

    status_code, payload = await client.get_benchmark_catalog(
        as_of_date="2026-03-27",
        benchmark_currency="USD",
        correlation_id="corr-3",
    )

    assert status_code == 200
    assert payload["records"][0]["benchmark_id"] == "BMK_PB_GLOBAL_BALANCED_60_40"
    request = _FakeAsyncClient.calls[0]
    assert request["url"] == "http://core-control/integration/benchmarks/catalog"
    assert request["json"]["as_of_date"] == "2026-03-27"
    assert request["json"]["benchmark_currency"] == "USD"
    assert request["json"]["benchmark_status"] == "active"
    assert request["json"]["benchmark_type"] == "composite"


@pytest.mark.asyncio
async def test_lotus_core_query_client_support_routes_use_control_plane_contract():
    client = LotusCoreQueryClient(
        base_url="http://core-query",
        control_plane_base_url="http://core-control",
        timeout_seconds=2.0,
    )
    _FakeAsyncClient.queue_json(200, {"publish_allowed": True})
    _FakeAsyncClient.queue_json(200, {"holdings": {"status": "READY"}})

    overview_status, overview_payload = await client.get_support_overview(
        portfolio_id="P1",
        correlation_id="corr-support",
    )
    readiness_status, readiness_payload = await client.get_portfolio_readiness(
        portfolio_id="P1",
        correlation_id="corr-support",
        as_of_date="2026-03-27",
    )

    assert overview_status == 200
    assert overview_payload["publish_allowed"] is True
    assert readiness_status == 200
    assert readiness_payload["holdings"]["status"] == "READY"
    assert _FakeAsyncClient.calls[0]["url"] == "http://core-control/support/portfolios/P1/overview"
    assert _FakeAsyncClient.calls[0]["params"] == {}
    assert _FakeAsyncClient.calls[1]["url"] == "http://core-control/support/portfolios/P1/readiness"
    assert _FakeAsyncClient.calls[1]["params"] == {"as_of_date": "2026-03-27"}


@pytest.mark.asyncio
async def test_lotus_core_query_client_external_execution_acknowledgement_uses_control_plane():
    client = LotusCoreQueryClient(
        base_url="http://core-query",
        control_plane_base_url="http://core-control",
        timeout_seconds=2.0,
    )
    core_payload = {
        "product_name": "ExternalOrderExecutionAcknowledgement",
        "product_version": "v1",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "acknowledgements": [],
        "supportability": {
            "state": "UNAVAILABLE",
            "reason": "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
            "acknowledgement_count": 0,
            "missing_data_families": ["external_oms_order_execution_acknowledgement"],
            "blocked_capabilities": ["oms_acknowledgement", "fills", "settlement"],
        },
        "lineage": {"runtime_posture": "fail_closed"},
    }
    request_payload = {
        "as_of_date": "2026-05-18",
        "tenant_id": "default",
        "order_reference_ids": ["ord-001"],
    }
    _FakeAsyncClient.queue_json(200, core_payload)

    status_code, payload = await client.get_external_order_execution_acknowledgement(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        payload=request_payload,
        correlation_id="corr-exec-ack",
    )

    assert status_code == 200
    assert payload == core_payload
    request = _FakeAsyncClient.calls[0]
    assert request["method"] == "POST"
    assert request["url"] == (
        "http://core-control/integration/portfolios/"
        "PB_SG_GLOBAL_BAL_001/external-order-execution-acknowledgement"
    )
    assert request["json"] == request_payload
    assert request["headers"]["X-Correlation-Id"] == "corr-exec-ack"


@pytest.mark.asyncio
async def test_lotus_core_query_client_emits_safe_fanout_metrics_without_runtime_ids(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = LotusCoreQueryClient(
        base_url="http://core-query",
        control_plane_base_url="http://core-control",
        timeout_seconds=2.0,
    )
    _FakeAsyncClient.queue_json(
        503,
        {
            "state": "degraded",
            "partial_failures": [{"error_code": "CORE_SIMULATION_UNAVAILABLE"}],
            "session_id": "sim_sensitive_1",
            "portfolio_id": "P1",
            "request_body": {"portfolio_id": "P1"},
        },
    )

    status_code, payload = await client.get_projected_positions(
        session_id="sim_sensitive_1",
        correlation_id="corr-core-observed",
    )

    assert status_code == 503
    assert payload["partial_failures"][0]["error_code"] == "CORE_SIMULATION_UNAVAILABLE"
    [record] = _fanout_records(caplog.records, service="lotus-core")
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.fanout.degraded"
    assert fields["operation"] == "core.simulation-sessions.projected-positions.get"
    assert fields["status_class"] == "5xx"
    assert fields["reason"] == "CORE_SIMULATION_UNAVAILABLE"
    assert fields["partial_failure_count"] == 1
    assert "sim_sensitive_1" not in fields.values()
    assert "session_id" not in fields
    assert "portfolio_id" not in fields
    assert "request_body" not in fields


@pytest.mark.asyncio
async def test_lotus_core_ingestion_client_emits_safe_fanout_metrics_without_payload_ids(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = LotusCoreIngestionClient(base_url="http://core-ingestion", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(
        400,
        {
            "state": "error",
            "portfolio_id": "P1",
            "upload_id": "upload_sensitive_1",
            "request_body": {"portfolio_id": "P1"},
        },
    )

    status_code, payload = await client.ingest_portfolio_bundle(
        body={"portfolio_id": "P1"},
        correlation_id="corr-core-ingestion-observed",
        idempotency_key="idem-sensitive-1",
    )

    assert status_code == 400
    assert payload["state"] == "error"
    [record] = _fanout_records(caplog.records, service="lotus-core")
    fields = record.extra_fields
    assert fields["event"] == "gateway.analytics.fanout.degraded"
    assert fields["operation"] == "core.ingest.portfolio-bundle.create"
    assert fields["status_class"] == "4xx"
    assert fields["reason"] == "UPSTREAM_ERROR"
    assert "P1" not in fields.values()
    assert "upload_sensitive_1" not in fields.values()
    assert "portfolio_id" not in fields
    assert "upload_id" not in fields
    assert "request_body" not in fields


@pytest.mark.asyncio
async def test_lotus_analytics_client_capabilities_supports_nondefault_consumer_and_tenant():
    client = LotusAnalyticsClient(base_url="http://lotus-performance", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "lotus-performance"})

    status_code, payload = await client.get_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-a",
        correlation_id="corr-capabilities",
    )

    assert status_code == 200
    assert payload["sourceService"] == "lotus-performance"
    assert _FakeAsyncClient.calls[0]["url"] == "http://lotus-performance/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-workbench",
        "tenant_id": "tenant-a",
    }


@pytest.mark.asyncio
async def test_lotus_analytics_client_capabilities_omits_query_params_when_contract_is_unshaped():
    client = LotusAnalyticsClient(base_url="http://risk", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "risk"})

    status_code, payload = await client.get_capabilities(correlation_id="corr-risk-capabilities")

    assert status_code == 200
    assert payload["sourceService"] == "risk"
    assert _FakeAsyncClient.calls[0]["url"] == "http://risk/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {}
