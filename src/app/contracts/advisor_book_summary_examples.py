from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse

ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE = AdvisorBookSummaryResponse.model_validate(
    {
        "correlation_id": "corr-advisor-book-summary-001",
        "contract_version": "v1",
        "scope": {
            "kind": "own_book",
            "label": "My book",
            "as_of_date": "2026-04-10",
            "booking_center_code": "Singapore",
        },
        "summary": {
            "resolved_as_of_date": "2026-04-10",
            "reporting_currency": "USD",
            "requested_portfolio_count": 2,
            "covered_portfolio_count": 2,
            "total_value": "2500000.75",
            "cash_value": "200000.00",
            "invested_value": "2300000.75",
            "coverage_state": "COMPLETE",
            "coverage_reason": "all_members_covered",
            "state": "supported",
            "reason_code": "advisor_book_value_ready",
        },
        "items": [
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "total_value": "1250000.50",
                "cash_value": "100000.00",
                "invested_value": "1150000.50",
                "valuation_as_of": "2026-04-10",
                "snapshot_date": "2026-04-10",
                "coverage_state": "COMPLETE",
                "coverage_reason": "snapshot_rows_complete",
                "state": "supported",
            },
            {
                "portfolio_id": "PB_SG_GLOBAL_INC_002",
                "total_value": "1250250.25",
                "cash_value": "100000.00",
                "invested_value": "1150250.25",
                "valuation_as_of": "2026-04-10",
                "snapshot_date": "2026-04-09",
                "coverage_state": "CARRY_FORWARD",
                "coverage_reason": "carried_forward_from_latest_snapshot",
                "state": "supported",
            },
        ],
        "source": {
            "source_service": "lotus-core",
            "source_route": "/reporting/portfolio-summary/bulk-query",
            "source_contract_version": "portfolio-summary-bulk-v1",
            "resolved_as_of_date": "2026-04-10",
            "reporting_currency": "USD",
        },
        "membership_provenance": None,
    }
).model_dump(mode="json")
