from app.contracts.advisor_book import AdvisorBookResponse
from app.contracts.advisor_book_examples import ADVISOR_BOOK_RESPONSE_EXAMPLE


def test_advisor_book_openapi_example_is_executable_contract_truth() -> None:
    response = AdvisorBookResponse.model_validate(ADVISOR_BOOK_RESPONSE_EXAMPLE)

    assert response.scope.kind == "own_book"
    assert response.scope.label == "My book"
    assert response.page.total_count == 1
    assert response.items[0].membership_source == "PortfolioManagerBookMembership:v1"
    assert response.supportability.state == "degraded"
    assert response.supportability.tenant_scope == "trusted_context_only"
    assert response.provenance is not None
    assert response.provenance.product_name == "PortfolioManagerBookMembership"


def test_advisor_book_contract_keeps_empty_scope_explicit() -> None:
    response = AdvisorBookResponse.model_validate(
        {
            "correlation_id": "corr-empty-book",
            "scope": {
                "kind": "own_book",
                "label": "My book",
                "as_of_date": "2026-04-10",
                "booking_center_code": "Singapore",
            },
            "page": {
                "total_count": 0,
                "offset": 0,
                "limit": 25,
                "returned_count": 0,
                "sort_by": "portfolio_id",
                "sort_order": "asc",
            },
            "items": [],
            "supportability": {
                "state": "empty",
                "reason_code": "advisor_book_empty",
                "tenant_scope": "trusted_context_only",
                "limitations": [
                    "tenant_scope_not_reported",
                    "delegated_scope_not_supported",
                ],
            },
        }
    )

    assert response.items == []
    assert response.page.total_count == 0
    assert response.supportability.reason_code == "advisor_book_empty"
    assert response.provenance is None
