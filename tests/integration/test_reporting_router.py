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


def _outcome_report_job_payload():
    return {
        "outcome_report_input": {
            "contract_version": "1.0",
            "outcome_review_id": "dor_001",
            "outcome_review_content_hash": "sha256:outcome-review",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "proof_pack_id": "dpp_001",
            "review_window": {"start_date": "2026-04-22", "end_date": "2026-04-23"},
            "report_title": "Post-Trade Outcome Review - PB_SG_GLOBAL_BAL_001",
            "state": "READY",
            "overall_outcome": "Execution outcome aligned with pre-trade proof.",
            "dimensions": [],
            "source_lineage": [],
            "source_hashes": {"realized": "sha256:realized"},
            "section_hashes": {"proof_pack": "sha256:proof-pack"},
            "redaction_policy": "NO_RAW_PAYLOADS",
            "content_hash": "sha256:report-input",
        },
        "requested_output_formats": ["pdf"],
        "reporting_currency": "USD",
        "options": {"retention_policy_id": "generated-report-standard"},
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


def test_outcome_review_report_job_gateway_route_forwards_context(monkeypatch):
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
            "report_request_id": "rrq_outcome_1",
            "report_job_id": "rjob_outcome_1",
            "status": "accepted",
            "status_url": "/reports/jobs/rjob_outcome_1",
            "idempotency_key": idempotency_key,
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.submit_outcome_review_report_job",
        _mock_submit_job,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/outcome-reviews",
        json=_outcome_report_job_payload(),
        headers={
            "Idempotency-Key": "outcome-review-dor_001-pdf",
            "X-Actor-Id": "advisor-123",
            "X-Caller-Application": "lotus-workbench",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Booking-Center-Code": "SG",
            "X-Role": "advisor",
            "X-Correlation-Id": "corr-outcome-report",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["report_job_id"] == "rjob_outcome_1"
    assert body["status_url"] == "/api/v1/report-jobs/rjob_outcome_1"
    assert captured["payload"] == _outcome_report_job_payload()
    assert captured["idempotency_key"] == "outcome-review-dor_001-pdf"
    assert captured["caller_headers"]["X-Caller-Application"] == "lotus-workbench"
    assert captured["correlation_id"] == "corr-outcome-report"


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


def test_report_job_lineage_gateway_routes_forward_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _mock_get_job_lineage(
        self,
        *,
        job_id,
        caller_headers,
        correlation_id,
    ):
        captured["job_id"] = job_id
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        return 200, {
            "snapshot": {
                "snapshot_id": "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf",
                "report_job_id": job_id,
                "report_type": "portfolio_review",
                "report_data_contract_version": "v1",
                "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
                "as_of_date": "2026-04-22",
                "snapshot_payload": {
                    "report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22"
                },
                "snapshot_hash": (
                    "sha256:7a5486f4a7ef1962f27fe67c6ef392fd0da0dfc7c98a84e426238637f4a5b7dd"
                ),
                "snapshot_storage_ref": None,
                "supportability_status": "complete",
                "completeness_status": "complete",
                "lineage_summary": {
                    "sourceServices": ["lotus-core"],
                    "callCount": 1,
                    "supportability_status": "complete",
                    "partialCallCount": 0,
                    "unavailableCallCount": 0,
                    "notSupportedCallCount": 0,
                    "redactedCallCount": 0,
                },
                "captured_at": "2026-04-22T09:00:03Z",
                "created_at": "2026-04-22T09:00:03Z",
                "correlation_id": correlation_id,
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            },
            "upstream_calls": [
                {
                    "upstream_call_id": "ruc_1",
                    "snapshot_id": "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf",
                    "service_name": "lotus-core",
                    "endpoint": "/reporting/portfolio-summary/query",
                    "method": "POST",
                    "contract_version": "v1",
                    "request_hash": (
                        "sha256:0f5de8ef5cf305bf2e38ed33139e1df8f06fdf531f80903c123c25f6d8c09780"
                    ),
                    "response_hash": (
                        "sha256:9de9c193650baf615ff8dca094d10ff18bdaabf0915963c4b3d74a3a07844f52"
                    ),
                    "response_ref": None,
                    "status_code": 200,
                    "latency_ms": 184,
                    "supportability_status": "complete",
                    "completeness_status": "complete",
                    "failure_category": "none",
                    "failure_message": None,
                    "captured_at": "2026-04-22T09:00:03Z",
                    "created_at": "2026-04-22T09:00:03Z",
                    "correlation_id": correlation_id,
                    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_job_lineage",
        _mock_get_job_lineage,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/report-jobs/rjob_1/lineage",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Caller-Application": "lotus-workbench",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Booking-Center-Code": "SG",
            "X-Role": "advisor",
            "X-Correlation-Id": "corr-lineage-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["snapshotId"] == "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf"
    assert body["snapshot"]["reportJobId"] == "rjob_1"
    assert len(body["upstreamCalls"]) == 1
    assert body["upstreamCalls"][0]["upstreamCallId"] == "ruc_1"
    assert captured["job_id"] == "rjob_1"
    assert captured["caller_headers"] == {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
    }
    assert captured["correlation_id"] == "corr-lineage-1"


def test_report_snapshot_endpoints_forward_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _mock_get_snapshot(self, *, snapshot_id, caller_headers, correlation_id):
        captured["snapshot_id"] = snapshot_id
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        payload = {
            "snapshot_id": snapshot_id,
            "report_job_id": "rjob_1",
            "report_type": "portfolio_review",
            "report_data_contract_version": "v1",
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "as_of_date": "2026-04-22",
            "snapshot_payload": {"report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22"},
            "snapshot_hash": (
                "sha256:7a5486f4a7ef1962f27fe67c6ef392fd0da0dfc7c98a84e426238637f4a5b7dd"
            ),
            "snapshot_storage_ref": None,
            "supportability_status": "complete",
            "completeness_status": "complete",
            "lineage_summary": {
                "sourceServices": ["lotus-core"],
                "callCount": 1,
                "supportability_status": "complete",
                "partialCallCount": 0,
                "unavailableCallCount": 0,
                "notSupportedCallCount": 0,
                "redactedCallCount": 0,
            },
            "captured_at": "2026-04-22T09:00:03Z",
            "created_at": "2026-04-22T09:00:03Z",
            "correlation_id": correlation_id,
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        }
        return 200, payload

    async def _mock_get_snapshot_lineage(self, *, snapshot_id, caller_headers, correlation_id):
        captured["lineage_snapshot_id"] = snapshot_id
        captured["lineage_caller_headers"] = caller_headers
        captured["lineage_correlation_id"] = correlation_id
        return 200, {
            "snapshot": {
                "snapshot_id": snapshot_id,
                "report_job_id": "rjob_1",
                "report_type": "portfolio_review",
                "report_data_contract_version": "v1",
                "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
                "as_of_date": "2026-04-22",
                "snapshot_payload": {
                    "report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22"
                },
                "snapshot_hash": (
                    "sha256:7a5486f4a7ef1962f27fe67c6ef392fd0da0dfc7c98a84e426238637f4a5b7dd"
                ),
                "snapshot_storage_ref": None,
                "supportability_status": "complete",
                "completeness_status": "complete",
                "lineage_summary": {
                    "sourceServices": ["lotus-core"],
                    "callCount": 1,
                    "supportability_status": "complete",
                    "partialCallCount": 0,
                    "unavailableCallCount": 0,
                    "notSupportedCallCount": 0,
                    "redactedCallCount": 0,
                },
                "captured_at": "2026-04-22T09:00:03Z",
                "created_at": "2026-04-22T09:00:03Z",
                "correlation_id": correlation_id,
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            },
            "upstream_calls": [
                {
                    "upstream_call_id": "ruc_1",
                    "snapshot_id": snapshot_id,
                    "service_name": "lotus-core",
                    "endpoint": "/reporting/portfolio-summary/query",
                    "method": "POST",
                    "contract_version": "v1",
                    "request_hash": (
                        "sha256:0f5de8ef5cf305bf2e38ed33139e1df8f06fdf531f80903c123c25f6d8c09780"
                    ),
                    "response_hash": (
                        "sha256:9de9c193650baf615ff8dca094d10ff18bdaabf0915963c4b3d74a3a07844f52"
                    ),
                    "response_ref": None,
                    "status_code": 200,
                    "latency_ms": 184,
                    "supportability_status": "complete",
                    "completeness_status": "complete",
                    "failure_category": "none",
                    "failure_message": None,
                    "captured_at": "2026-04-22T09:00:03Z",
                    "created_at": "2026-04-22T09:00:03Z",
                    "correlation_id": correlation_id,
                    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_snapshot",
        _mock_get_snapshot,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_snapshot_lineage",
        _mock_get_snapshot_lineage,
    )

    client = TestClient(app)
    snapshot_response = client.get(
        "/api/v1/reports/snapshots/rsnap_1",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Correlation-Id": "corr-snapshot-route",
        },
    )
    lineage_response = client.get(
        "/api/v1/reports/snapshots/rsnap_1/lineage",
        headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-sg",
            "X-Region": "APAC",
            "X-Correlation-Id": "corr-snapshot-route",
        },
    )

    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["snapshotId"] == "rsnap_1"
    assert snapshot_response.json()["supportabilityStatus"] == "complete"
    assert snapshot_response.json()["lineageSummary"]["callCount"] == 1
    assert lineage_response.status_code == 200
    assert lineage_response.json()["upstreamCalls"][0]["upstreamCallId"] == "ruc_1"
    assert captured["snapshot_id"] == "rsnap_1"
    assert captured["correlation_id"] == "corr-snapshot-route"
    assert captured["caller_headers"]["X-Actor-Id"] == "advisor-123"
    assert captured["lineage_snapshot_id"] == "rsnap_1"
    assert captured["lineage_correlation_id"] == "corr-snapshot-route"
    assert captured["lineage_caller_headers"]["X-Caller-Application"] == "lotus-gateway"


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


def test_report_snapshot_gateway_errors_are_product_safe(monkeypatch):
    async def _mock_get_snapshot(self, *, snapshot_id, caller_headers, correlation_id):  # noqa: ARG001
        return 500, {"detail": "snapshot postgres internal-host report.dev.lotus"}

    async def _mock_get_snapshot_lineage(self, *, snapshot_id, caller_headers, correlation_id):  # noqa: ARG001
        return 500, {"detail": "snapshot lineage postgres internal-host report.dev.lotus"}

    async def _mock_get_job_lineage(self, *, job_id, caller_headers, correlation_id):  # noqa: ARG001
        return 404, {"detail": {"code": "report_snapshot_not_found", "message": "missing snapshot"}}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_snapshot",
        _mock_get_snapshot,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_snapshot_lineage",
        _mock_get_snapshot_lineage,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_job_lineage",
        _mock_get_job_lineage,
    )

    client = TestClient(app)
    snapshot_response = client.get(
        "/api/v1/reports/snapshots/rsnap_500",
        headers={"X-Actor-Id": "advisor-123", "X-Tenant-Id": "tenant-sg", "X-Region": "APAC"},
    )
    snapshot_lineage_response = client.get(
        "/api/v1/reports/snapshots/rsnap_500/lineage",
        headers={"X-Actor-Id": "advisor-123", "X-Tenant-Id": "tenant-sg", "X-Region": "APAC"},
    )
    job_lineage_response = client.get(
        "/api/v1/report-jobs/rjob_500/lineage",
        headers={"X-Actor-Id": "advisor-123", "X-Tenant-Id": "tenant-sg", "X-Region": "APAC"},
    )

    assert snapshot_response.status_code == 502
    assert snapshot_response.json()["detail"]["code"] == "report_job_upstream_unavailable"
    assert "internal-host" not in str(snapshot_response.json())
    assert snapshot_lineage_response.status_code == 502
    assert snapshot_lineage_response.json()["detail"]["code"] == "report_job_upstream_unavailable"
    assert "internal-host" not in str(snapshot_lineage_response.json())
    assert job_lineage_response.status_code == 404
    assert job_lineage_response.json()["detail"]["code"] == "report_snapshot_not_found"
    assert job_lineage_response.json()["detail"]["message"] == "missing snapshot"


def _batch_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "operator-123",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
        "X-Correlation-Id": "corr-gateway-batch",
    }


def _batch_payload() -> dict[str, object]:
    return {
        "selector_mode": "explicit_portfolio_list",
        "portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["pdf"],
        "reporting_currency": "USD",
        "options": {"sections": ["OVERVIEW"]},
        "max_batch_size": 250,
    }


def _batch_status_payload(status: str = "materialized") -> dict[str, object]:
    return {
        "batch_id": "rbch_1",
        "selector_mode": "explicit_portfolio_list",
        "tenant_id": "tenant-sg",
        "region": "APAC",
        "materialized_portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["pdf"],
        "reporting_currency": "USD",
        "status": status,
        "item_count": 1,
        "status_counts": {status: 1},
        "items": [
            {
                "batch_item_id": "rbci_1",
                "item_position": 1,
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "status": status,
                "report_job_id": None,
                "attempt_count": 0,
                "retry_eligible": False,
                "next_retry_at": None,
                "last_error_category": None,
                "last_error_summary": None,
                "created_at": "2026-04-22T09:00:00Z",
                "started_at": None,
                "completed_at": None,
                "cancelled_at": None,
            }
        ],
        "created_at": "2026-04-22T09:00:00Z",
        "updated_at": "2026-04-22T09:00:00Z",
        "started_at": None,
        "completed_at": None,
        "cancelled_at": None,
        "failed_at": None,
        "correlation_id": "corr-gateway-batch",
        "trace_id": "trace-batch",
    }


def test_report_batch_gateway_routes_forward_context_and_rewrite_status_urls(monkeypatch):
    calls: list[tuple[str, str | None, dict[str, str]]] = []

    async def _mock_create_batch(
        self,
        *,
        payload,
        idempotency_key,
        caller_headers,
        correlation_id,
    ):
        calls.append(("create", idempotency_key, caller_headers))
        assert payload == {
            **_batch_payload(),
            "source_candidates": [
                {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "tenant_id": "tenant-sg",
                    "region": "APAC",
                    "active": True,
                    "selected": True,
                    "source_system": "lotus-core",
                    "source_object": "PortfolioManagerBookMembership:v1",
                }
            ],
        }
        assert correlation_id == "corr-gateway-batch"
        return 202, {
            "batch_id": "rbch_1",
            "status": "materialized",
            "status_url": "/reports/batches/rbch_1",
            "idempotency_key": idempotency_key,
            "item_count": 1,
        }

    async def _mock_get_book_memberships(
        self,
        *,
        portfolio_manager_id,
        as_of_date,
        booking_center_code,
        portfolio_types,
        correlation_id,
    ):
        assert portfolio_manager_id == "operator-123"
        assert as_of_date == "2026-04-22"
        assert booking_center_code == "SG"
        assert portfolio_types == ["ADVISORY", "DISCRETIONARY"]
        assert correlation_id == "corr-gateway-batch"
        return 200, {
            "product_name": "PortfolioManagerBookMembership",
            "product_version": "v1",
            "portfolio_manager_id": "operator-123",
            "tenant_id": "tenant-sg",
            "generated_at": "2026-04-22T08:00:00Z",
            "as_of_date": "2026-04-22",
            "latest_evidence_timestamp": "2026-04-22T07:59:00Z",
            "snapshot_id": "pm-book-sg",
            "content_hash": "sha256:report-batch-book",
            "data_quality_status": "ACCEPTED",
            "source_evidence_current": True,
            "freshness_status": "CURRENT",
            "booking_center_code": "SG",
            "members": [
                {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "client_id": "CIF_SG_001",
                    "booking_center_code": "SG",
                    "portfolio_type": "DISCRETIONARY",
                    "status": "ACTIVE",
                    "open_date": "2025-03-31",
                    "close_date": None,
                    "base_currency": "USD",
                    "source_record_id": "portfolio:PB_SG_GLOBAL_BAL_001",
                    "membership_source": "party_role_assignment",
                    "role_type": "ADVISOR",
                }
            ],
            "supportability": {
                "state": "READY",
                "reason": "PM_BOOK_MEMBERSHIP_READY",
                "returned_portfolio_count": 1,
                "filters_applied": ["portfolio_manager_id", "as_of_date"],
            },
            "lineage": {"source_system": "lotus-core"},
        }

    async def _mock_get_batch(self, *, batch_id, caller_headers, correlation_id):
        calls.append(("get", batch_id, caller_headers))
        assert correlation_id == "corr-gateway-batch"
        return 200, _batch_status_payload()

    async def _mock_get_capabilities(self, *, consumer_system, tenant_id, correlation_id):
        calls.append(("capabilities", tenant_id, {"consumer_system": consumer_system}))
        assert correlation_id == "corr-gateway-batch"
        return 200, {
            "sourceService": "lotus-report",
            "supportability": {
                "state": "ready",
                "reason": "evidence_surface_ready",
                "freshness_bucket": "current",
                "evidence_feature_count": 14,
                "ready_evidence_feature_count": 14,
                "degraded_evidence_feature_count": 0,
                "workflow_count": 4,
                "ready_workflow_count": 4,
            },
        }

    async def _mock_get_render_metadata(self, *, correlation_id):
        calls.append(("render-metadata", correlation_id, {}))
        assert correlation_id == "corr-gateway-batch"
        return 200, {
            "service": "lotus-render",
            "supportability": {
                "featureKey": "render.observability.render_supportability",
                "state": "ready",
                "reason": "render_supportability_ready",
                "freshnessBucket": "current",
                "deterministicOutputSupported": True,
                "renderStoreReady": True,
                "templateRegistryReady": True,
                "defaultOutputFormat": "pdf",
                "supportedOutputFormats": ["pdf"],
            },
        }

    async def _mock_control_batch(
        self,
        *,
        batch_id,
        action,
        caller_headers,
        correlation_id,
        payload=None,
    ):
        calls.append((action, batch_id, caller_headers))
        assert correlation_id == "corr-gateway-batch"
        if action == "recover-expired-leases":
            return 200, {
                "batch_id": batch_id,
                "status": "running",
                "recovered_count": 1,
                "recovery_pending_item_ids": ["rbci_1"],
                "status_url": "/reports/batches/rbch_1",
            }
        if action == "run-once":
            assert payload == {"worker_id": "worker-1", "recover_expired_leases": True}
            return 200, {
                "batch_id": batch_id,
                "status": "completed",
                "batch_status_before": "materialized",
                "batch_status_after": "completed",
                "recovered_count": 0,
                "leased_count": 1,
                "dispatched_count": 1,
                "executed_count": 1,
                "report_job_ids": ["rjob_1"],
                "back_pressure_reasons": [],
                "skipped_reason": None,
                "execution_results": [
                    {
                        "batch_item_id": "rbci_1",
                        "report_job_id": "rjob_1",
                        "item_status": "succeeded",
                        "report_job_status": "archived",
                        "failure_category": None,
                        "retry_eligible": False,
                    }
                ],
                "status_url": "/reports/batches/rbch_1",
            }
        status_by_action = {
            "pause": "paused",
            "resume": "running",
            "cancel": "cancelled",
            "retry-failed": "running",
        }
        return 200, {
            "batch_id": batch_id,
            "status": status_by_action[action],
            "affected_count": 1,
            "status_url": "/reports/batches/rbch_1",
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.create_report_batch",
        _mock_create_batch,
    )
    monkeypatch.setattr(
        "app.clients.lotus_core_query_client.LotusCoreQueryClient.get_portfolio_manager_book_memberships",
        _mock_get_book_memberships,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_batch",
        _mock_get_batch,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.control_report_batch",
        _mock_control_batch,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_capabilities",
        _mock_get_capabilities,
    )
    monkeypatch.setattr(
        "app.clients.render_client.RenderClient.get_metadata",
        _mock_get_render_metadata,
    )

    client = TestClient(app)
    create_response = client.post(
        "/api/v1/report-batches",
        json=_batch_payload(),
        headers={**_batch_headers(), "Idempotency-Key": "idem-batch-1"},
    )
    status_response = client.get("/api/v1/report-batches/rbch_1", headers=_batch_headers())
    pause_response = client.post("/api/v1/report-batches/rbch_1:pause", headers=_batch_headers())
    resume_response = client.post("/api/v1/report-batches/rbch_1:resume", headers=_batch_headers())
    cancel_response = client.post("/api/v1/report-batches/rbch_1:cancel", headers=_batch_headers())
    retry_response = client.post(
        "/api/v1/report-batches/rbch_1:retry-failed",
        headers=_batch_headers(),
    )
    recovery_response = client.post(
        "/api/v1/report-batches/rbch_1:recover-expired-leases",
        headers=_batch_headers(),
    )
    run_response = client.post(
        "/api/v1/report-batches/rbch_1:run-once",
        json={"worker_id": "worker-1", "recover_expired_leases": True},
        headers=_batch_headers(),
    )

    assert create_response.status_code == 202
    assert create_response.json()["status_url"] == "/api/v1/report-batches/rbch_1"
    assert create_response.json()["supportability"] == {
        "feature_key": "report.observability.evidence_surface_supportability",
        "state": "ready",
        "reason": "evidence_surface_ready",
        "freshness_bucket": "current",
        "evidence_feature_count": 14,
        "ready_evidence_feature_count": 14,
        "degraded_evidence_feature_count": 0,
        "workflow_count": 4,
        "ready_workflow_count": 4,
    }
    assert create_response.json()["render_supportability"] == {
        "feature_key": "render.observability.render_supportability",
        "state": "ready",
        "reason": "render_supportability_ready",
        "freshness_bucket": "current",
        "deterministic_output_supported": True,
        "render_store_ready": True,
        "template_registry_ready": True,
        "default_output_format": "pdf",
        "supported_output_formats": ["pdf"],
    }
    assert status_response.status_code == 200
    assert status_response.json()["items"][0]["portfolio_id"] == "PB_SG_GLOBAL_BAL_001"
    assert status_response.json()["supportability"]["state"] == "ready"
    assert status_response.json()["render_supportability"]["state"] == "ready"
    assert pause_response.json()["status"] == "paused"
    assert resume_response.json()["status"] == "running"
    assert cancel_response.json()["status"] == "cancelled"
    assert retry_response.json()["status"] == "running"
    assert recovery_response.json()["status_url"] == "/api/v1/report-batches/rbch_1"
    assert recovery_response.json()["recovered_count"] == 1
    assert run_response.json()["status_url"] == "/api/v1/report-batches/rbch_1"
    assert run_response.json()["report_job_ids"] == ["rjob_1"]
    assert run_response.json()["supportability"]["feature_key"] == (
        "report.observability.evidence_surface_supportability"
    )
    assert run_response.json()["render_supportability"]["feature_key"] == (
        "render.observability.render_supportability"
    )
    batch_calls = [call for call in calls if call[0] not in {"capabilities", "render-metadata"}]
    assert batch_calls[0][0:2] == ("create", "idem-batch-1")
    assert batch_calls[0][2]["X-Caller-Application"] == "lotus-gateway"
    assert batch_calls[0][2]["X-Actor-Id"] == "operator-123"
    assert batch_calls[1][0:2] == ("get", "rbch_1")
    assert [call[0] for call in batch_calls[2:]] == [
        "pause",
        "resume",
        "cancel",
        "retry-failed",
        "recover-expired-leases",
        "run-once",
    ]
    assert [call for call in calls if call[0] == "capabilities"] == [
        ("capabilities", "tenant-sg", {"consumer_system": "lotus-gateway"}),
        ("capabilities", "tenant-sg", {"consumer_system": "lotus-gateway"}),
        ("capabilities", "tenant-sg", {"consumer_system": "lotus-gateway"}),
    ]
    assert [call[0] for call in calls if call[0] == "render-metadata"] == [
        "render-metadata",
        "render-metadata",
        "render-metadata",
    ]


def test_report_batch_schedule_gateway_routes_forward_context(monkeypatch):
    calls: list[tuple[str, dict[str, str], str | None]] = []

    async def _mock_list_schedules(self, *, caller_headers, correlation_id):
        calls.append(("list", caller_headers, correlation_id))
        return 200, {
            "scheduler_id": "scheduler-gateway-unit",
            "interval_seconds": 60.0,
            "tenant_id": "tenant-sg",
            "region": "APAC",
            "booking_center_code": "SG",
            "schedule_count": 1,
            "enabled_schedule_count": 1,
            "schedules": [
                {
                    "schedule_id": "monthly-sg-global-bal",
                    "enabled": True,
                    "selector_mode": "explicit_portfolio_list",
                    "frequency": "monthly",
                    "as_of_date": "2026-04-22",
                    "portfolio_count": 1,
                    "manifest_entry_count": 0,
                    "requested_output_formats": ["pdf"],
                    "reporting_currency": "USD",
                    "max_batch_size": 250,
                    "template_id": "portfolio-review",
                    "template_version": "v1",
                    "render_package_version": "portfolio-review.v1",
                    "manifest_source": None,
                    "manifest_version": None,
                    "manifest_hash": None,
                    "option_keys": ["sections"],
                }
            ],
        }

    async def _mock_run_due_schedules(self, *, payload, caller_headers, correlation_id):
        calls.append(("run-due", caller_headers, correlation_id))
        assert payload == {"pass_sequence": 4}
        return 200, {
            "scheduler_id": "scheduler-gateway-unit",
            "attempted_count": 1,
            "materialized_count": 1,
            "skipped_schedule_ids": [],
            "materialized": [
                {
                    "schedule_id": "monthly-sg-global-bal",
                    "batch_id": "rbch_sched_1",
                    "idempotency_key": "scheduled-batch-1",
                    "item_count": 1,
                    "status": "materialized",
                }
            ],
            "correlation_id": "corr-batch-scheduler-4-unit",
            "trace_id": "trace-scheduler-unit",
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.list_report_batch_schedules",
        _mock_list_schedules,
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.run_due_report_batch_schedules",
        _mock_run_due_schedules,
    )

    client = TestClient(app)
    list_response = client.get("/api/v1/report-batch-schedules", headers=_batch_headers())
    run_response = client.post(
        "/api/v1/report-batch-schedules:run-due",
        json={"pass_sequence": 4},
        headers=_batch_headers(),
    )

    assert list_response.status_code == 200
    assert list_response.json()["schedule_count"] == 1
    assert list_response.json()["schedules"][0]["schedule_id"] == "monthly-sg-global-bal"
    assert run_response.status_code == 200
    assert run_response.json()["materialized"][0]["batch_id"] == "rbch_sched_1"
    assert [call[0] for call in calls] == ["list", "run-due"]
    assert calls[0][1]["X-Caller-Application"] == "lotus-gateway"
    assert calls[1][1]["X-Actor-Id"] == "operator-123"
    assert calls[0][2] == "corr-gateway-batch"


def test_report_batch_gateway_requires_idempotency_and_caller_context():
    client = TestClient(app)
    missing_idempotency = client.post(
        "/api/v1/report-batches",
        json=_batch_payload(),
        headers=_batch_headers(),
    )
    missing_context = client.post(
        "/api/v1/report-batches",
        json=_batch_payload(),
        headers={"Idempotency-Key": "idem-batch-1"},
    )

    assert missing_idempotency.status_code == 400
    assert missing_idempotency.json()["detail"]["code"] == "missing_idempotency_key"
    assert missing_context.status_code == 400
    detail = missing_context.json()["detail"]
    assert detail["code"] == "missing_caller_context"
    assert detail["missing_headers"] == ["X-Actor-Id", "X-Tenant-Id", "X-Region"]


def test_report_batch_gateway_rejects_browser_candidate_authority() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/report-batches",
        json={
            **_batch_payload(),
            "source_candidates": [
                {
                    "portfolio_id": "PB_GUESSED_001",
                    "tenant_id": "tenant-sg",
                    "region": "APAC",
                    "active": True,
                    "selected": True,
                    "source_system": "lotus-core",
                    "source_object": "PortfolioScope",
                }
            ],
        },
        headers={**_batch_headers(), "Idempotency-Key": "idem-forged-candidate"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "source_candidates"]
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_report_batch_gateway_errors_are_product_safe(monkeypatch):
    async def _mock_get_batch(self, *, batch_id, caller_headers, correlation_id):  # noqa: ARG001
        return 500, {"detail": "postgres traceback internal-host report.dev.lotus"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_report_batch",
        _mock_get_batch,
    )

    client = TestClient(app)
    response = client.get("/api/v1/report-batches/rbch_500", headers=_batch_headers())

    assert response.status_code == 502
    body = response.json()
    assert body["detail"]["code"] == "report_batch_upstream_unavailable"
    assert "postgres" not in str(body).lower()
    assert "report.dev.lotus" not in str(body)
