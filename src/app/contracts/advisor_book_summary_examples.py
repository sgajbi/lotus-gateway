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
            "state": "supported",
            "reason_code": "advisor_book_value_ready",
        },
        "items": [
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "total_value": "1250000.50",
                "position_count": 12,
                "state": "supported",
                "reason_code": "advisor_book_value_ready",
            },
            {
                "portfolio_id": "PB_SG_GLOBAL_INC_002",
                "total_value": "1250250.25",
                "position_count": 9,
                "state": "supported",
                "reason_code": "advisor_book_value_ready",
            },
        ],
        "source": {
            "source_service": "lotus-core",
            "source_route": "/reporting/assets-under-management/query",
            "resolved_as_of_date": "2026-04-10",
            "reporting_currency": "USD",
        },
        "membership_provenance": None,
    }
).model_dump(mode="json")
