from fastapi.testclient import TestClient

from app.contracts.reporting import (
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
)
from app.main import app


def test_reporting_snapshot_success(monkeypatch):
    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ARG001
        return (
            200,
            {
                "generatedAt": "2026-02-24T07:00:00Z",
                "rows": [
                    {"bucket": "TOTAL", "metric": "market_value_base", "value": 1250000.0},
                    {"bucket": "TOTAL", "metric": "return_ytd_pct", "value": 4.2},
                ],
            },
        )

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolioId"] == "DEMO_DPM_EUR_001"
    assert body["sourceService"] == "lotus-report"
    assert body["contractVersion"] == "v1"
    assert isinstance(body["correlationId"], str)
    assert body["asOfDate"] == "2026-02-24"
    assert body["generatedAt"].startswith("2026-02-24T07:00:00")
    assert len(body["rows"]) == 2
    assert body["rows"][0]["metric"] == "market_value_base"
    assert body["rows"][1]["value"] == 4.2


def test_reporting_snapshot_preserves_portfolio_date_and_correlation_context(monkeypatch):
    captured: dict[str, str] = {}

    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):
        captured["portfolio_id"] = portfolio_id
        captured["as_of_date"] = as_of_date
        captured["correlation_id"] = correlation_id
        return 200, {
            "generatedAt": "2026-02-24T07:00:00Z",
            "rows": [{"bucket": "TOTAL", "metric": "market_value_base", "value": 1.0}],
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")

    assert response.status_code == 200
    body = ReportingSnapshotResponse.model_validate(response.json())
    assert captured["portfolio_id"] == "DEMO_DPM_EUR_001"
    assert captured["as_of_date"] == "2026-02-24"
    assert captured["correlation_id"] == body.correlation_id
    assert body.portfolio_id == "DEMO_DPM_EUR_001"
    assert body.as_of_date == "2026-02-24"


def test_reporting_snapshot_invalid_generated_at_fallback(monkeypatch):
    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ARG001
        return (
            200,
            {
                "generatedAt": "invalid",
                "rows": [{"bucket": "TOTAL", "metric": "market_value_base", "value": 1.0}],
            },
        )

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    assert response.status_code == 200
    body = response.json()
    assert body["generatedAt"] is not None


def test_reporting_snapshot_upstream_error(monkeypatch):
    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ARG001
        return 503, {"detail": "upstream unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    assert response.status_code == 502


def test_reporting_summary_success(monkeypatch):
    async def _mock_post_summary(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        assert payload == {
            "as_of_date": "2026-02-24",
            "sections": ["WEALTH"],
        }
        return 200, {
            "scope": {"portfolio_id": portfolio_id},
            "wealth": {"total_market_value": 123.0},
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_summary",
        _mock_post_summary,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/summary",
        json={"as_of_date": "2026-02-24", "sections": ["WEALTH"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["portfolioId"] == "DEMO_DPM_EUR_001"
    assert body["sourceService"] == "lotus-report"
    assert body["contractVersion"] == "v1"
    assert isinstance(body["correlationId"], str)
    assert body["asOfDate"] == "2026-02-24"
    assert body["data"]["scope"]["portfolio_id"] == "DEMO_DPM_EUR_001"
    assert body["data"]["wealth"]["total_market_value"] == 123.0


def test_reporting_summary_preserves_request_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _mock_post_summary(self, portfolio_id, payload, correlation_id):
        captured["portfolio_id"] = portfolio_id
        captured["payload"] = payload
        captured["correlation_id"] = correlation_id
        return 200, {"scope": {"portfolio_id": portfolio_id}, "wealth": {"total_market_value": 1.0}}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_summary",
        _mock_post_summary,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/summary",
        json={
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": ["WEALTH"],
            "allocationDimensions": ["asset_class"],
            "lookThroughMode": "direct_only",
        },
    )

    assert response.status_code == 200
    body = ReportingSummaryResponse.model_validate(response.json())
    assert captured["portfolio_id"] == "DEMO_DPM_EUR_001"
    assert captured["payload"] == {
        "as_of_date": "2026-02-24",
        "reporting_currency": "USD",
        "sections": ["WEALTH"],
        "allocation_dimensions": ["asset_class"],
        "look_through_mode": "direct_only",
    }
    assert captured["correlation_id"] == body.correlation_id
    assert body.portfolio_id == "DEMO_DPM_EUR_001"
    assert body.as_of_date == "2026-02-24"


def test_reporting_review_success(monkeypatch):
    async def _mock_post_review(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        assert payload == {
            "as_of_date": "2026-02-24",
            "reporting_currency": "USD",
            "sections": ["OVERVIEW"],
            "allocation_dimensions": ["asset_class"],
            "look_through_mode": "full",
            "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
        }
        return 200, {
            "portfolio_id": portfolio_id,
            "readiness": {"status": "partial", "reason": "Risk Review unavailable."},
            "client_sections": [
                {
                    "section_id": "risk_review",
                    "title": "Risk Review",
                    "status": "unavailable",
                    "reason_code": "missing_return_history",
                    "items": [],
                }
            ],
            "advisor_sections": [
                {
                    "section_id": "advisor_discussion",
                    "title": "Advisor Discussion And Follow-Up",
                    "status": "ready",
                    "items": [
                        {
                            "prompt_id": "review_readiness",
                            "advisor_only": True,
                            "prompt": "Confirm report readiness is partial.",
                            "route_targets": [
                                {
                                    "surface": "lotus-workbench",
                                    "route_key": "portfolio_review",
                                    "mutation_allowed": False,
                                }
                            ],
                        }
                    ],
                }
            ],
            "overview": {"total_market_value": 1000.0},
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_review",
        _mock_post_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/review",
        json={
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": ["OVERVIEW"],
            "allocationDimensions": ["asset_class"],
            "lookThroughMode": "full",
            "benchmarkCode": "BMK_PB_GLOBAL_BALANCED_60_40",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["portfolioId"] == "DEMO_DPM_EUR_001"
    assert body["sourceService"] == "lotus-report"
    assert body["contractVersion"] == "v1"
    assert isinstance(body["correlationId"], str)
    assert body["asOfDate"] == "2026-02-24"
    assert body["data"]["portfolio_id"] == "DEMO_DPM_EUR_001"
    assert body["data"]["overview"]["total_market_value"] == 1000.0
    assert body["data"]["readiness"]["status"] == "partial"
    assert body["data"]["client_sections"][0]["status"] == "unavailable"
    assert "advisor_only" not in body["data"]["client_sections"][0]
    advisor_item = body["data"]["advisor_sections"][0]["items"][0]
    assert advisor_item["advisor_only"] is True
    assert advisor_item["route_targets"][0]["mutation_allowed"] is False


def test_reporting_review_preserves_request_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _mock_post_review(self, portfolio_id, payload, correlation_id):
        captured["portfolio_id"] = portfolio_id
        captured["payload"] = payload
        captured["correlation_id"] = correlation_id
        return 200, {"overview": {"total_market_value": 1000.0}}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_review",
        _mock_post_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/review",
        json={
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": ["OVERVIEW"],
            "allocationDimensions": ["asset_class"],
            "lookThroughMode": "full",
        },
    )

    assert response.status_code == 200
    body = ReportingReviewResponse.model_validate(response.json())
    assert captured["portfolio_id"] == "DEMO_DPM_EUR_001"
    assert captured["payload"] == {
        "as_of_date": "2026-02-24",
        "reporting_currency": "USD",
        "sections": ["OVERVIEW"],
        "allocation_dimensions": ["asset_class"],
        "look_through_mode": "full",
    }
    assert captured["correlation_id"] == body.correlation_id
    assert body.portfolio_id == "DEMO_DPM_EUR_001"
    assert body.as_of_date == "2026-02-24"


def test_reporting_summary_upstream_error(monkeypatch):
    async def _mock_post_summary(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        return 503, {"detail": "summary unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_summary",
        _mock_post_summary,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/summary",
        json={"as_of_date": "2026-02-24"},
    )
    assert response.status_code == 502


def test_reporting_review_upstream_error(monkeypatch):
    async def _mock_post_review(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        return 503, {"detail": "review unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_review",
        _mock_post_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/review",
        json={"as_of_date": "2026-02-24"},
    )
    assert response.status_code == 502


def _job_payload():
    return {
        "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["json"],
        "reporting_currency": "USD",
        "options": {
            "sections": ["OVERVIEW", "PERFORMANCE"],
            "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
        },
    }


def test_portfolio_review_job_gateway_route_forwards_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _mock_submit_job(
        self,
        *,
        payload,
        idempotency_key,
        caller_headers,
        correlation_id,
    ):
        captured["payload"] = payload
        captured["idempotency_key"] = idempotency_key
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        return 202, {
            "report_request_id": "rrq_1",
            "report_job_id": "rjob_1",
            "status": "accepted",
            "status_url": "/reports/jobs/rjob_1",
            "idempotency_key": idempotency_key,
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.submit_portfolio_review_job",
        _mock_submit_job,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/portfolio-reviews",
        json=_job_payload(),
        headers={
            "Idempotency-Key": "idem-gateway-1",
            "X-Actor-Id": "advisor-123",
            "X-Caller-Application": "lotus-workbench",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Booking-Center-Code": "SG",
            "X-Role": "advisor",
            "X-Correlation-Id": "corr-gateway-job",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["report_job_id"] == "rjob_1"
    assert body["status_url"] == "/api/v1/report-jobs/rjob_1"
    assert captured["payload"] == _job_payload()
    assert captured["idempotency_key"] == "idem-gateway-1"
    assert captured["caller_headers"] == {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
    }
    assert captured["correlation_id"] == "corr-gateway-job"


def test_portfolio_review_job_gateway_requires_idempotency_key():
    client = TestClient(app)
    response = client.post("/api/v1/reports/portfolio-reviews", json=_job_payload())

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "missing_idempotency_key"


def test_portfolio_review_job_gateway_requires_caller_context():
    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/portfolio-reviews",
        json=_job_payload(),
        headers={"Idempotency-Key": "idem-missing-context"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "missing_caller_context"
    assert detail["missing_headers"] == ["X-Actor-Id", "X-Tenant-Id", "X-Region"]


def test_report_job_status_and_cancel_are_gateway_first(monkeypatch):
    calls: list[tuple[str, str, dict[str, str] | None]] = []

    async def _mock_list_jobs(self, *, filters, caller_headers, correlation_id):
        calls.append(("list", filters["portfolioId"], caller_headers))
        return 200, {
            "count": 1,
            "appliedFilters": {
                "tenantId": "tenant-sg",
                "region": "APAC",
                "status": "accepted",
                "reportType": None,
                "portfolioId": filters["portfolioId"],
                "asOfDate": None,
                "idempotencyKey": None,
                "correlationId": correlation_id,
                "createdFrom": None,
                "createdTo": None,
                "limit": 25,
            },
            "items": [
                {
                    "reportJobId": "rjob_1",
                    "reportRequestId": "rrq_1",
                    "reportType": "portfolio_review",
                    "tenantId": "tenant-sg",
                    "region": "APAC",
                    "portfolioScope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
                    "asOfDate": "2026-04-22",
                    "status": "accepted",
                    "failureCategory": None,
                    "currentStep": "accepted",
                    "retryEligible": False,
                    "cancelRequested": False,
                    "idempotencyKey": "idem-gateway-1",
                    "correlationId": correlation_id,
                    "createdAt": "2026-04-22T09:00:00Z",
                    "updatedAt": "2026-04-22T09:00:00Z",
                }
            ],
        }

    async def _mock_get_job(self, *, job_id, caller_headers, correlation_id):
        calls.append(("get", job_id, caller_headers))
        return 200, {
            "report_job_id": job_id,
            "report_request_id": "rrq_1",
            "report_type": "portfolio_review",
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "status": "accepted",
            "failure_category": None,
            "failure_message": None,
            "current_step": "accepted",
            "retry_eligible": False,
            "cancel_requested": False,
            "created_at": "2026-04-22T09:00:00Z",
            "updated_at": "2026-04-22T09:00:00Z",
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None,
            "correlation_id": correlation_id,
            "trace_id": "trace-job",
        }

    async def _mock_cancel_job(self, *, job_id, caller_headers, correlation_id):
        calls.append(("cancel", job_id, caller_headers))
        return 200, {
            "report_job_id": job_id,
            "report_request_id": "rrq_1",
            "report_type": "portfolio_review",
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "status": "cancelled",
            "failure_category": "cancelled",
            "failure_message": "Report job cancelled before render or archive processing.",
            "current_step": "cancelled",
            "retry_eligible": False,
            "cancel_requested": True,
            "created_at": "2026-04-22T09:00:00Z",
            "updated_at": "2026-04-22T09:01:00Z",
            "started_at": None,
            "completed_at": None,
            "cancelled_at": "2026-04-22T09:01:00Z",
            "correlation_id": correlation_id,
            "trace_id": "trace-job",
        }

    async def _mock_get_job_events(self, *, job_id, caller_headers, correlation_id):
        calls.append(("events", job_id, caller_headers))
        return 200, {
            "report_job_id": job_id,
            "events": [
                {
                    "status_event_id": "rse_1",
                    "report_job_id": job_id,
                    "from_status": None,
                    "to_status": "accepted",
                    "event_type": "job_accepted",
                    "message": "Portfolio review report job accepted.",
                    "actor": "advisor-123",
                    "created_at": "2026-04-22T09:00:00Z",
                    "correlation_id": correlation_id,
                    "trace_id": "trace-job",
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.list_report_jobs", _mock_list_jobs
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_job", _mock_get_job
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_job_events",
        _mock_get_job_events,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.cancel_report_job",
        _mock_cancel_job,
    )

    client = TestClient(app)
    list_response = client.get(
        "/api/v1/report-jobs?portfolioId=PB_SG_GLOBAL_BAL_001",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
    )
    status_response = client.get(
        "/api/v1/report-jobs/rjob_1",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
    )
    events_response = client.get(
        "/api/v1/report-jobs/rjob_1/events",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
    )
    cancel_response = client.post(
        "/api/v1/report-jobs/rjob_1/cancel",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
    )

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["reportJobId"] == "rjob_1"
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "accepted"
    assert events_response.status_code == 200
    assert events_response.json()["events"][0]["event_type"] == "job_accepted"
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert calls[0][0:2] == ("list", "PB_SG_GLOBAL_BAL_001")
    assert calls[0][2]["X-Actor-Id"] == "advisor-123"
    assert calls[0][2]["X-Caller-Application"] == "lotus-gateway"
    assert calls[0][2]["X-Tenant-Id"] == "tenant-sg"
    assert calls[0][2]["X-Region"] == "APAC"
    assert calls[1][0:2] == ("get", "rjob_1")
    assert calls[1][2]["X-Actor-Id"] == "advisor-123"
    assert calls[1][2]["X-Caller-Application"] == "lotus-gateway"
    assert calls[1][2]["X-Region"] == "APAC"
    assert calls[2][0:2] == ("events", "rjob_1")
    assert calls[2][2]["X-Actor-Id"] == "advisor-123"
    assert calls[2][2]["X-Caller-Application"] == "lotus-gateway"
    assert calls[2][2]["X-Region"] == "APAC"
    assert calls[3][0:2] == ("cancel", "rjob_1")


def test_report_job_gateway_errors_are_product_safe(monkeypatch):
    async def _mock_get_job(self, *, job_id, caller_headers, correlation_id):  # noqa: ARG001
        return 500, {"detail": "sqlite traceback internal-host report.dev.lotus"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_job", _mock_get_job
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/report-jobs/rjob_500",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
        },
    )

    assert response.status_code == 502
    body = response.json()
    assert body["detail"]["code"] == "report_job_upstream_unavailable"
    assert "sqlite" not in str(body).lower()
    assert "report.dev.lotus" not in str(body)
