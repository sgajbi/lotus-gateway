from typing import Any

__all__ = [
    "REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE",
    "REPORT_JOB_LIST_FILTERS_EXAMPLE",
    "REPORT_JOB_LIST_RESPONSE_EXAMPLE",
    "REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE",
    "REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE",
]

REPORT_JOB_LIST_FILTERS_EXAMPLE: dict[str, Any] = {
    "tenantId": "tenant-sg",
    "region": "APAC",
    "status": "accepted",
    "reportType": "portfolio_review",
    "portfolioId": "PB_SG_GLOBAL_BAL_001",
    "asOfDate": "2026-04-22",
    "idempotencyKey": "portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22",
    "correlationId": "corr-portfolio-review-1",
    "createdFrom": "2026-04-22T00:00:00Z",
    "createdTo": "2026-04-23T00:00:00Z",
    "limit": 25,
}

REPORT_JOB_LIST_RESPONSE_EXAMPLE: dict[str, Any] = {
    "count": 1,
    "appliedFilters": REPORT_JOB_LIST_FILTERS_EXAMPLE,
    "items": [
        {
            "reportJobId": "rjob_83ca965c50334c40a17d2b8cc94873a5",
            "reportRequestId": "rrq_4f7c85b39f7d4e7b8d0bb420d34a1d2c",
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
            "idempotencyKey": "portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22",
            "correlationId": "corr-portfolio-review-1",
            "createdAt": "2026-04-22T09:00:00Z",
            "updatedAt": "2026-04-22T09:00:00Z",
        }
    ],
}

REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE: dict[str, Any] = {
    "snapshotId": "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf",
    "reportJobId": "rjob_83ca965c50334c40a17d2b8cc94873a5",
    "reportType": "portfolio_review",
    "reportDataContractVersion": "v1",
    "portfolioScope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
    "asOfDate": "2026-04-22",
    "snapshotPayload": {
        "report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "as_of_date": "2026-04-22",
    },
    "snapshotHash": ("sha256:7a5486f4a7ef1962f27fe67c6ef392fd0da0dfc7c98a84e426238637f4a5b7dd"),
    "snapshotStorageRef": None,
    "supportabilityStatus": "complete",
    "completenessStatus": "complete",
    "lineageSummary": {
        "sourceServices": ["lotus-core", "lotus-performance", "lotus-risk"],
        "callCount": 8,
        "supportability_status": "complete",
        "partialCallCount": 0,
        "unavailableCallCount": 0,
        "notSupportedCallCount": 0,
        "redactedCallCount": 0,
    },
    "capturedAt": "2026-04-22T09:00:03Z",
    "createdAt": "2026-04-22T09:00:03Z",
    "correlationId": "corr-portfolio-review-1",
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
}

REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE: dict[str, Any] = {
    "upstreamCallId": "ruc_7c5d4f1e4cb6455fa11c06821c57b88f",
    "snapshotId": "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf",
    "serviceName": "lotus-core",
    "endpoint": "/reporting/portfolio-summary/query",
    "method": "POST",
    "contractVersion": "v1",
    "requestHash": ("sha256:0f5de8ef5cf305bf2e38ed33139e1df8f06fdf531f80903c123c25f6d8c09780"),
    "responseHash": ("sha256:9de9c193650baf615ff8dca094d10ff18bdaabf0915963c4b3d74a3a07844f52"),
    "responseRef": None,
    "statusCode": 200,
    "latencyMs": 184,
    "supportabilityStatus": "complete",
    "completenessStatus": "complete",
    "failureCategory": "none",
    "failureMessage": None,
    "capturedAt": "2026-04-22T09:00:02Z",
    "createdAt": "2026-04-22T09:00:02Z",
    "correlationId": "corr-portfolio-review-1",
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
}

REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE: dict[str, Any] = {
    "snapshot": REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE,
    "upstreamCalls": [REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE],
}
