from decimal import Decimal

from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse
from app.contracts.advisor_book_summary_examples import ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE
from app.main import app


def test_advisor_book_summary_example_is_executable_contract_truth() -> None:
    response = AdvisorBookSummaryResponse.model_validate(ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE)

    assert response.contract_version == "v1"
    assert response.summary.total_value == Decimal("2500000.75")
    assert response.summary.covered_portfolio_count == 2
    assert response.source.source_service == "lotus-core"
    assert response.source.source_route == "/reporting/assets-under-management/query"


def test_advisor_book_summary_openapi_exposes_source_and_coverage_fields() -> None:
    spec = app.openapi()
    operation = spec["paths"]["/api/v1/advisor-book/summary"]["get"]
    summary_schema = spec["components"]["schemas"]["AdvisorBookValueSummary"]
    item_schema = spec["components"]["schemas"]["AdvisorBookValueItem"]

    assert operation["parameters"]
    assert "total_value" in summary_schema["properties"]
    assert "covered_portfolio_count" in summary_schema["properties"]
    assert item_schema["properties"]["state"]["enum"] == ["supported", "unavailable"]
    assert operation["responses"]["200"]["content"]["application/json"]["example"]
