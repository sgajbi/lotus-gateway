import pytest
from fastapi import HTTPException

from app.contracts.reporting import BatchSchedulerRunRequest
from app.services.reporting_batch_scheduler_service import ReportingBatchSchedulerService


class _ReportingClient:
    def __init__(self) -> None:
        self.list_response: tuple[int, dict[str, object]] = (200, _schedule_list_payload())
        self.run_due_response: tuple[int, dict[str, object]] = (200, _scheduler_run_payload())
        self.calls: list[dict[str, object]] = []

    async def list_report_batch_schedules(
        self,
        *,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "list",
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.list_response

    async def run_due_report_batch_schedules(
        self,
        *,
        payload: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "run_due",
                "payload": payload,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.run_due_response


def _caller_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "operator-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
    }


def _schedule_list_payload() -> dict[str, object]:
    return {
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


def _scheduler_run_payload() -> dict[str, object]:
    return {
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


@pytest.mark.asyncio
async def test_reporting_batch_scheduler_service_lists_schedules() -> None:
    reporting_client = _ReportingClient()
    service = ReportingBatchSchedulerService(reporting_client=reporting_client)

    response = await service.list_schedules(
        caller_headers=_caller_headers(),
        correlation_id="corr-scheduler",
    )

    assert response.schedule_count == 1
    assert response.schedules[0].schedule_id == "monthly-sg-global-bal"
    assert reporting_client.calls == [
        {
            "operation": "list",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-scheduler",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_batch_scheduler_service_runs_due_schedules() -> None:
    reporting_client = _ReportingClient()
    service = ReportingBatchSchedulerService(reporting_client=reporting_client)

    response = await service.run_due_schedules(
        request=BatchSchedulerRunRequest.model_validate({"pass_sequence": 4}),
        caller_headers=_caller_headers(),
        correlation_id="corr-scheduler",
    )

    assert response.materialized[0].batch_id == "rbch_sched_1"
    assert reporting_client.calls == [
        {
            "operation": "run_due",
            "payload": {"pass_sequence": 4},
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-scheduler",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_batch_scheduler_service_maps_scheduler_errors() -> None:
    reporting_client = _ReportingClient()
    reporting_client.run_due_response = (
        409,
        {
            "detail": {
                "code": "batch_scheduler_run_failed",
                "message": "Scheduler pass could not materialize configured schedules.",
            }
        },
    )
    service = ReportingBatchSchedulerService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.run_due_schedules(
            request=BatchSchedulerRunRequest.model_validate({"pass_sequence": 4}),
            caller_headers=_caller_headers(),
            correlation_id="corr-scheduler",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "code": "batch_scheduler_run_failed",
        "message": "Scheduler pass could not materialize configured schedules.",
    }
