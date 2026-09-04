from app.contracts.advisor_book_workspace import AdvisorBookWorkspaceResponse

ADVISOR_BOOK_WORKSPACE_RESPONSE_EXAMPLE = AdvisorBookWorkspaceResponse.model_validate(
    {
        "correlation_id": "corr-advisor-book-workspace-001",
        "contract_version": "v1",
        "scope": {
            "kind": "own_book",
            "label": "My book",
            "as_of_date": "2026-04-10",
            "booking_center_code": "Singapore",
        },
        "rows": [
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "value": {
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
                "action_items": {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "action_item_count": 2,
                    "reason_codes": [
                        "PROPOSAL_READY_FOR_REVIEW",
                        "POLICY_EXCEPTION_REVIEW",
                    ],
                },
            },
            {
                "portfolio_id": "PB_SG_GLOBAL_INC_002",
                "value": {
                    "portfolio_id": "PB_SG_GLOBAL_INC_002",
                    "total_value": "1250000.25",
                    "cash_value": "100000.00",
                    "invested_value": "1150000.25",
                    "valuation_as_of": "2026-04-10",
                    "snapshot_date": "2026-04-09",
                    "coverage_state": "CARRY_FORWARD",
                    "coverage_reason": "carry_forward_within_tolerance",
                    "state": "supported",
                },
                "action_items": {
                    "portfolio_id": "PB_SG_GLOBAL_INC_002",
                    "action_item_count": 0,
                    "reason_codes": [],
                },
            },
        ],
        "value_facts": {
            "state": "stated",
            "reason_code": "value_facts_stated",
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
            "source": {
                "source_service": "lotus-core",
                "source_route": "/reporting/portfolio-summary/bulk-query",
                "source_contract_version": "portfolio-summary-bulk-v1",
                "resolved_as_of_date": "2026-04-10",
                "reporting_currency": "USD",
            },
        },
        "action_facts": {
            "state": "stated",
            "reason_code": "action_facts_stated",
            "summary": {
                "portfolio_count": 2,
                "portfolios_with_action_items": 1,
                "action_item_count": 2,
                "unassigned_action_item_count": 1,
                "outside_book_action_item_count": 0,
                "source_stated_total": 3,
                "coverage_state": "complete",
                "coverage_reason": "action_feed_fully_read",
                "state": "supported",
            },
            "source": {
                "source_service": "lotus-advise",
                "source_route": "/advisory/cockpit/actions",
                "scope_basis": "advise_authorized_advisor_scope",
                "membership_as_of_date": "2026-04-10",
                "action_evidence_basis": "current_state",
            },
        },
    }
).model_dump(mode="json")
