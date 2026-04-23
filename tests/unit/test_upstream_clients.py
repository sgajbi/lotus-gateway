import json

import httpx
import pytest

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.reporting_client import ReportingClient


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
        return self._next_response("GET", url)

    async def post(self, url, json=None, data=None, files=None, headers=None):
        self.calls.append(
            {
                "method": "POST",
                "url": url,
                "json": json,
                "data": data,
                "files": files,
                "headers": headers or {},
            }
        )
        return self._next_response("POST", url)

    @classmethod
    def _next_response(cls, method: str, url: str) -> httpx.Response:
        if not cls.responses:
            raise AssertionError("No queued response available.")
        response = cls.responses.pop(0)
        if response.request is None:
            response.request = httpx.Request(method, url)  # type: ignore[misc]
        return response

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


@pytest.fixture(autouse=True)
def _patch_async_client(monkeypatch):
    _FakeAsyncClient.responses = []
    _FakeAsyncClient.calls = []
    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)


@pytest.mark.asyncio
async def test_lotus_analytics_client_calls_and_payload_handling():
    client = LotusAnalyticsClient(base_url="http://pa", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "pa"})
    _FakeAsyncClient.queue_json(
        200,
        {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 2.1}}}}
            }
        },
    )
    _FakeAsyncClient.queue_json(
        200,
        {
            "allocationBuckets": [{"bucketKey": "EQUITY"}],
            "topChanges": [],
            "riskProxy": {},
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
    status_three, payload_three = await client.get_workbench_analytics(
        payload={"portfolioId": "P1", "groupBy": "ASSET_CLASS"},
        correlation_id="corr-1",
    )

    assert status_one == 200
    assert payload_one["sourceService"] == "pa"
    assert status_two == 200
    assert (
        payload_two["results_by_period"]["YTD"]["portfolio"]["summary"]["period_return"]["base"]
        == 2.1
    )
    assert status_three == 200
    assert payload_three["allocationBuckets"][0]["bucketKey"] == "EQUITY"
    assert _FakeAsyncClient.calls[0]["url"] == "http://pa/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert _FakeAsyncClient.calls[1]["url"] == "http://pa/performance/twr"
    assert _FakeAsyncClient.calls[2]["url"] == "http://pa/analytics/workbench"
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
        benchmark_id="BMK_GLOBAL_BALANCED_60_40",
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
    assert request["json"]["benchmark"]["benchmark_id"] == "BMK_GLOBAL_BALANCED_60_40"


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
        benchmark_id="BMK_GLOBAL_BALANCED_60_40",
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
        benchmark_id="BMK_GLOBAL_BALANCED_60_40",
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
        benchmark_id="BMK_GLOBAL_BALANCED_60_40",
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
    client = LotusAnalyticsClient(base_url="http://pa", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(503, "pa unavailable")
    _FakeAsyncClient.queue_json(200, ["analytics"])

    status_one, payload_one = await client.get_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-1",
    )
    status_two, payload_two = await client.get_workbench_analytics(
        payload={"portfolioId": "P1"},
        correlation_id="corr-1",
    )

    assert status_one == 503
    assert payload_one["detail"] == "pa unavailable"
    assert status_two == 200
    assert payload_two["detail"] == ["analytics"]
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_endpoints_and_non_json_response_handling():
    client = LotusCoreQueryClient(base_url="http://pas", timeout_seconds=2.0)
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
    assert _FakeAsyncClient.calls[0]["url"] == "http://pas/portfolios/P1"
    assert _FakeAsyncClient.calls[1]["url"] == "http://pas/portfolios/P1/positions"
    assert _FakeAsyncClient.calls[2]["url"] == "http://pas/portfolios/P1/transactions"
    assert _FakeAsyncClient.calls[3]["url"] == "http://pas/portfolios/P1/cashflow-projection"


@pytest.mark.asyncio
async def test_lotus_core_query_client_transaction_route_supports_advanced_filters_and_sorting():
    client = LotusCoreQueryClient(base_url="http://pas", timeout_seconds=2.0)
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
    assert _FakeAsyncClient.calls[0]["url"] == "http://pas/portfolios/P1/transactions"
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


@pytest.mark.asyncio
async def test_lotus_core_query_client_cash_balances_uses_strategic_holdings_route():
    client = LotusCoreQueryClient(base_url="http://pas", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"cash_accounts": []})

    status_code, payload = await client.get_portfolio_cash_balances(
        portfolio_id="P1",
        correlation_id="corr-cash-balances",
        as_of_date="2026-03-27",
        reporting_currency="SGD",
    )

    assert status_code == 200
    assert payload["cash_accounts"] == []
    assert _FakeAsyncClient.calls[0]["url"] == "http://pas/portfolios/P1/cash-balances"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "as_of_date": "2026-03-27",
        "reporting_currency": "SGD",
    }


@pytest.mark.asyncio
async def test_lotus_core_query_client_core_endpoints():
    client = LotusCoreQueryClient(base_url="http://pas", timeout_seconds=2.0)
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
    assert _FakeAsyncClient.calls[0]["url"] == "http://pas/integration/capabilities"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert _FakeAsyncClient.calls[1]["url"] == "http://pas/integration/policy/effective"
    assert _FakeAsyncClient.calls[1]["params"] == {
        "consumer_system": "lotus-gateway",
        "tenant_id": "default",
    }
    assert _FakeAsyncClient.calls[3]["url"] == "http://pas/lookups/portfolios"
    assert _FakeAsyncClient.calls[3]["params"] == {}
    assert _FakeAsyncClient.calls[4]["json"] == {
        "as_of_date": "2026-02-24",
        "sections": ["positions_baseline"],
        "consumer_system": "lotus-gateway",
    }
    assert (
        _FakeAsyncClient.calls[5]["url"]
        == "http://pas/integration/portfolios/P1/analytics/reference"
    )


@pytest.mark.asyncio
async def test_lotus_core_query_client_lookup_routes_preserve_filter_query_params():
    client = LotusCoreQueryClient(base_url="http://pas", timeout_seconds=2.0)
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

    assert _FakeAsyncClient.calls[0]["url"] == "http://pas/lookups/portfolios"
    assert _FakeAsyncClient.calls[0]["params"] == {
        "client_id": "CIF_1001",
        "booking_center_code": "SG",
        "q": "Alpha",
        "limit": 25,
    }
    assert _FakeAsyncClient.calls[1]["url"] == "http://pas/lookups/instruments"
    assert _FakeAsyncClient.calls[1]["params"] == {
        "limit": 50,
        "product_type": "EQUITY",
        "q": "Apple",
    }
    assert _FakeAsyncClient.calls[2]["url"] == "http://pas/lookups/currencies"
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
    client = LotusCoreQueryClient(base_url="http://pas", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, ["not-dict"])
    status_code, payload = await client.list_portfolios(correlation_id="corr-3")
    assert status_code == 200
    assert payload["detail"] == ["not-dict"]


@pytest.mark.asyncio
async def test_pas_ingestion_client_upload_paths():
    client = LotusCoreIngestionClient(base_url="http://pas-ingest", timeout_seconds=2.0)
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
    assert _FakeAsyncClient.calls[1]["url"] == "http://pas-ingest/ingest/uploads/preview"
    assert _FakeAsyncClient.calls[2]["url"] == "http://pas-ingest/ingest/uploads/commit"
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
    client = LotusCoreIngestionClient(base_url="http://pas-ingest", timeout_seconds=2.0)
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
    client = LotusCoreIngestionClient(base_url="http://pas-ingest", timeout_seconds=2.0)
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
            "simulate_proposal",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proposals/simulate",
        ),
        (
            "create_proposal",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-2",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proposals",
        ),
        (
            "list_proposals",
            {"params": {"portfolio_id": "P1", "status": None}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proposals",
        ),
        (
            "list_runs",
            {"params": {"portfolio_id": "P1", "status": None}, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/runs",
        ),
        (
            "get_proposal",
            {"proposal_id": "PR-1", "include_evidence": True, "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proposals/PR-1",
        ),
        (
            "get_proposal_version",
            {
                "proposal_id": "PR-1",
                "version_no": 2,
                "include_evidence": False,
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proposals/PR-1/versions/2",
        ),
        (
            "create_proposal_version",
            {
                "proposal_id": "PR-1",
                "body": {"changes": []},
                "idempotency_key": "idem-3",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proposals/PR-1/versions",
        ),
        (
            "transition_proposal",
            {
                "proposal_id": "PR-1",
                "body": {"event": "submit"},
                "idempotency_key": "idem-transition-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proposals/PR-1/transitions",
        ),
        (
            "record_approval",
            {
                "proposal_id": "PR-1",
                "body": {"decision": "approve"},
                "idempotency_key": "idem-approval-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/rebalance/proposals/PR-1/approvals",
        ),
        (
            "get_workflow_events",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proposals/PR-1/workflow-events",
        ),
        (
            "get_approvals",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proposals/PR-1/approvals",
        ),
        (
            "get_proposal_lineage",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://dpm/api/v1/rebalance/proposals/PR-1/lineage",
        ),
        (
            "get_capabilities",
            {
                "consumer_system": "lotus-gateway",
                "tenant_id": "default",
                "correlation_id": "corr-5",
            },
            "http://dpm/api/v1/platform/capabilities",
        ),
    ],
)
async def test_dpm_client_all_routes(method_name, kwargs, expected_url):
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)
    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["url"] == expected_url
    methods_with_idempotency = {
        "simulate_proposal",
        "create_proposal",
        "create_proposal_version",
        "transition_proposal",
        "record_approval",
    }
    if method_name in methods_with_idempotency:
        assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == kwargs["idempotency_key"]


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
        "consumerSystem": "lotus-gateway",
        "tenantId": "default",
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
    cancel_status, cancel_payload = await client.cancel_report_job(
        job_id="rjob_1",
        caller_headers={"X-Actor-Id": "advisor-123"},
        correlation_id="corr-job-1",
    )

    assert submit_status == 202
    assert submit_payload["report_job_id"] == "rjob_1"
    assert status_code == 200
    assert status_payload["status"] == "accepted"
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
    assert _FakeAsyncClient.calls[2]["url"] == "http://ras/reports/jobs/rjob_1/cancel"
    assert _FakeAsyncClient.calls[2]["headers"]["X-Actor-Id"] == "advisor-123"


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
        "asOfDate": "2026-02-24",
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
                    "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
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
    assert payload["records"][0]["benchmark_id"] == "BMK_GLOBAL_BALANCED_60_40"
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
async def test_lotus_analytics_client_capabilities_supports_nondefault_consumer_and_tenant():
    client = LotusAnalyticsClient(base_url="http://pa", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "pa"})

    status_code, payload = await client.get_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-a",
        correlation_id="corr-capabilities",
    )

    assert status_code == 200
    assert payload["sourceService"] == "pa"
    assert _FakeAsyncClient.calls[0]["url"] == "http://pa/integration/capabilities"
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
