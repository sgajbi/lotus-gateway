from typing import Any

REPORT_JOB_ERROR_EXAMPLES: dict[str, dict[str, Any]] = {
    "missing_idempotency_key": {
        "detail": {
            "code": "missing_idempotency_key",
            "message": "Idempotency-Key is required.",
        }
    },
    "missing_caller_context": {
        "detail": {
            "code": "missing_caller_context",
            "message": "Required caller context headers are missing.",
            "missing_headers": ["X-Actor-Id", "X-Tenant-Id", "X-Region"],
        }
    },
    "report_job_not_found": {
        "detail": {
            "code": "report_job_not_found",
            "message": "Report job was not found.",
        }
    },
    "report_snapshot_not_found": {
        "detail": {
            "code": "report_snapshot_not_found",
            "message": "Report snapshot was not found.",
        }
    },
    "idempotency_conflict": {
        "detail": {
            "code": "idempotency_conflict",
            "message": "Idempotency-Key was reused with a different report request.",
        }
    },
    "report_job_cannot_be_cancelled": {
        "detail": {
            "code": "report_job_cannot_be_cancelled",
            "message": "Report job can no longer be cancelled.",
        }
    },
    "report_job_upstream_unavailable": {
        "detail": {
            "code": "report_job_upstream_unavailable",
            "message": "Report job service is unavailable.",
        }
    },
    "invalid_report_job_filters": {
        "detail": {
            "code": "invalid_report_job_filters",
            "message": "At least one supported job-search filter is required.",
        }
    },
}

REPORT_BATCH_ERROR_EXAMPLES: dict[str, dict[str, Any]] = {
    "missing_idempotency_key": REPORT_JOB_ERROR_EXAMPLES["missing_idempotency_key"],
    "missing_caller_context": REPORT_JOB_ERROR_EXAMPLES["missing_caller_context"],
    "idempotency_conflict": {
        "detail": {
            "code": "idempotency_conflict",
            "message": "Idempotency-Key was reused with a different batch request.",
        }
    },
    "invalid_batch_selector": {
        "detail": {
            "code": "invalid_batch_selector",
            "message": "Batch selector could not be materialized from eligible portfolios.",
        }
    },
    "report_batch_caller_context_missing": {
        "detail": {
            "code": "report_batch_caller_context_missing",
            "message": "Required trusted report-batch caller context is missing or invalid.",
        }
    },
    "report_batch_caller_context_invalid": {
        "detail": {
            "code": "report_batch_caller_context_invalid",
            "message": "Required trusted report-batch caller context is missing or invalid.",
        }
    },
    "report_batch_access_denied": {
        "detail": {
            "code": "report_batch_access_denied",
            "message": "Report batch creation is not available for this caller.",
        }
    },
    "report_batch_portfolio_not_entitled": {
        "detail": {
            "code": "report_batch_portfolio_not_entitled",
            "message": (
                "One or more selected portfolios are not available in the authenticated book."
            ),
        }
    },
    "report_batch_portfolio_inactive": {
        "detail": {
            "code": "report_batch_portfolio_inactive",
            "message": "One or more selected portfolios are not active for reporting.",
        }
    },
    "report_batch_scope_unavailable": {
        "detail": {
            "code": "report_batch_scope_unavailable",
            "message": "Report batch portfolio eligibility is temporarily unavailable.",
        }
    },
    "report_batch_scope_unverified": {
        "detail": {
            "code": "report_batch_scope_unverified",
            "message": "The selected portfolio scope could not be safely verified.",
        }
    },
    "report_batch_not_found": {
        "detail": {
            "code": "report_batch_not_found",
            "message": "Report batch was not found.",
        }
    },
    "batch_worker_run_failed": {
        "detail": {
            "code": "batch_worker_run_failed",
            "message": "Report batch run could not be completed.",
        }
    },
    "batch_scheduler_run_failed": {
        "detail": {
            "code": "batch_scheduler_run_failed",
            "message": "Report batch scheduler pass could not be completed.",
        }
    },
    "report_batch_upstream_unavailable": {
        "detail": {
            "code": "report_batch_upstream_unavailable",
            "message": "Report batch service is unavailable.",
        }
    },
}
