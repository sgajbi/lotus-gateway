from app.contracts.advisor_book_action_items import AdvisorBookActionItemsResponse

ADVISOR_BOOK_ACTION_ITEMS_RESPONSE_EXAMPLE = AdvisorBookActionItemsResponse.model_validate(
    {
        "correlation_id": "corr-advisor-book-action-items-001",
        "contract_version": "v1",
        "scope": {
            "kind": "own_book",
            "label": "My book",
            "as_of_date": "2026-04-10",
            "booking_center_code": "Singapore",
        },
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
        "items": [
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "action_item_count": 2,
                "reason_codes": ["PROPOSAL_READY_FOR_REVIEW", "POLICY_EXCEPTION_REVIEW"],
            },
            {
                "portfolio_id": "PB_SG_GLOBAL_INC_002",
                "action_item_count": 0,
                "reason_codes": [],
            },
        ],
        "source": {
            "source_service": "lotus-advise",
            "source_route": "/advisory/cockpit/actions",
            "scope_basis": "advise_authorized_advisor_scope",
            "membership_as_of_date": "2026-04-10",
            "action_evidence_basis": "current_state",
        },
    }
).model_dump(mode="json")
