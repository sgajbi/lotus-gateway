SUMMARY_REQUEST_EXAMPLES = {
    "wealthSummary": {
        "summary": "Wealth summary in portfolio base currency",
        "description": "Resolve wealth and allocation sections for one reporting date.",
        "value": {
            "asOfDate": "2026-02-24",
            "sections": ["WEALTH", "ALLOCATION"],
            "allocationDimensions": ["asset_class", "currency"],
        },
    }
}

REVIEW_REQUEST_EXAMPLES = {
    "frontOfficeReview": {
        "summary": "Front-office review payload in USD",
        "description": (
            "Resolve a review payload with holdings, transactions, performance, and risk."
        ),
        "value": {
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": [
                "OVERVIEW",
                "ALLOCATION",
                "INCOME_AND_ACTIVITY",
                "HOLDINGS",
                "TRANSACTIONS",
                "PERFORMANCE",
                "RISK_ANALYTICS",
            ],
            "allocationDimensions": ["asset_class"],
            "lookThroughMode": "full",
            "benchmarkCode": "BMK_PB_GLOBAL_BALANCED_60_40",
        },
    }
}

PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES = {
    "portfolioReviewJob": {
        "summary": "Portfolio review job request",
        "description": "Create a durable job handle for asynchronous portfolio review generation.",
        "value": {
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "as_of_date": "2026-04-22",
            "requested_output_formats": ["json"],
            "reporting_currency": "USD",
            "options": {
                "sections": ["OVERVIEW", "PERFORMANCE", "RISK_ANALYTICS"],
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
            },
        },
    }
}

OUTCOME_REVIEW_REPORT_JOB_REQUEST_EXAMPLES = {
    "outcomeReviewReportJob": {
        "summary": "Outcome-review report job request",
        "description": (
            "Create a durable report job from manage-owned DpmOutcomeReportInput evidence."
        ),
        "value": {
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
        },
    }
}
