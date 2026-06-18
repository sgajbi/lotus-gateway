from typing import Any

__all__ = [
    "BATCH_CONTROL_RESPONSE_EXAMPLE",
    "BATCH_CREATE_REQUEST_EXAMPLE",
    "BATCH_HANDLE_RESPONSE_EXAMPLE",
    "BATCH_RECOVERY_RESPONSE_EXAMPLE",
    "BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE",
    "BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE",
    "BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE",
    "BATCH_STATUS_RESPONSE_EXAMPLE",
    "BATCH_WORKER_RUN_REQUEST_EXAMPLE",
    "BATCH_WORKER_RUN_RESPONSE_EXAMPLE",
]

BATCH_CREATE_REQUEST_EXAMPLE: dict[str, Any] = {
    "selector_mode": "explicit_portfolio_list",
    "portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
    "source_candidates": [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "tenant_id": "tenant-sg",
            "region": "APAC",
            "active": True,
            "selected": True,
            "source_system": "lotus-core",
            "source_object": "PortfolioScope",
        }
    ],
    "as_of_date": "2026-04-22",
    "requested_output_formats": ["pdf"],
    "reporting_currency": "USD",
    "options": {"sections": ["OVERVIEW", "PERFORMANCE"]},
    "max_batch_size": 250,
}

BATCH_HANDLE_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "materialized",
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "idempotency_key": "batch-portfolio-review-2026-04-22",
    "item_count": 1,
    "supportability": {
        "feature_key": "report.observability.evidence_surface_supportability",
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

BATCH_STATUS_RESPONSE_EXAMPLE: dict[str, Any] = {
    **BATCH_HANDLE_RESPONSE_EXAMPLE,
    "selector_mode": "explicit_portfolio_list",
    "tenant_id": "tenant-sg",
    "region": "APAC",
    "materialized_portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
    "as_of_date": "2026-04-22",
    "requested_output_formats": ["pdf"],
    "reporting_currency": "USD",
    "status_counts": {"materialized": 1},
    "items": [
        {
            "batch_item_id": "rbci_1a3b5c7d9e0f4a12a45f7a8d00bd129c",
            "item_position": 1,
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "status": "materialized",
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
    "correlation_id": "corr-batch-1",
    "trace_id": "trace-batch-1",
}

BATCH_CONTROL_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "paused",
    "affected_count": 1,
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
}

BATCH_RECOVERY_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "running",
    "recovered_count": 1,
    "recovery_pending_item_ids": ["rbci_1a3b5c7d9e0f4a12a45f7a8d00bd129c"],
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
}

BATCH_WORKER_RUN_REQUEST_EXAMPLE: dict[str, Any] = {
    "worker_id": "lotus-report-batch-worker-1",
    "recover_expired_leases": True,
    "dispatch_policy": {
        "max_active_batches": 1,
        "max_active_items": 5,
        "max_active_upstream_jobs": 3,
        "max_active_render_jobs": 2,
        "max_active_archive_jobs": 2,
        "lease_seconds": 300,
    },
    "runtime_load": {
        "active_batches": 0,
        "active_items": 0,
        "active_upstream_jobs": 0,
        "active_render_jobs": 0,
        "active_archive_jobs": 0,
    },
}

BATCH_WORKER_RUN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "completed",
    "batch_status_before": "materialized",
    "batch_status_after": "completed",
    "recovered_count": 0,
    "leased_count": 1,
    "dispatched_count": 1,
    "executed_count": 1,
    "report_job_ids": ["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    "back_pressure_reasons": [],
    "skipped_reason": None,
    "execution_results": [
        {
            "batch_item_id": "rbci_1a3b5c7d9e0f4a12a45f7a8d00bd129c",
            "report_job_id": "rjob_83ca965c50334c40a17d2b8cc94873a5",
            "item_status": "succeeded",
            "report_job_status": "archived",
            "failure_category": None,
            "retry_eligible": False,
        }
    ],
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "supportability": BATCH_HANDLE_RESPONSE_EXAMPLE["supportability"],
}

BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE: dict[str, Any] = {
    "scheduler_id": "lotus-report-batch-scheduler-1",
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

BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE: dict[str, Any] = {"pass_sequence": 1}

BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "scheduler_id": "lotus-report-batch-scheduler-1",
    "attempted_count": 1,
    "materialized_count": 1,
    "skipped_schedule_ids": [],
    "materialized": [
        {
            "schedule_id": "monthly-sg-global-bal",
            "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
            "idempotency_key": "scheduled-batch-2f6d1a8f2ef24f019e7d7f37507f352c",
            "item_count": 1,
            "status": "materialized",
        }
    ],
    "correlation_id": "corr-batch-scheduler-1-abc123def456",
    "trace_id": "trace1234567890abcdef1234567890ab",
}
