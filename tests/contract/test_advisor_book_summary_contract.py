from decimal import Decimal

from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse
from app.contracts.advisor_book_summary_examples import ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE
from app.main import app


def test_advisor_book_summary_example_is_executable_contract_truth() -> None:
    response = AdvisorBookSummaryResponse.model_validate(ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE)

    assert response.contract_version == "v1"
    assert response.summary.total_value == Decimal("2500250.75")
    assert response.summary.cash_value == Decimal("200000.00")
    assert response.summary.invested_value == Decimal("2300250.75")
    assert response.summary.coverage_state == "COMPLETE"
    assert response.summary.covered_portfolio_count == 2
    # A fully covered example must be arithmetically coherent: Core's fail-closed
    # aggregate over an all-members-covered cohort is the sum of its member rows.
    for aggregate, member_values in (
        (response.summary.total_value, [item.total_value for item in response.items]),
        (response.summary.cash_value, [item.cash_value for item in response.items]),
        (response.summary.invested_value, [item.invested_value for item in response.items]),
    ):
        assert aggregate == sum(value for value in member_values if value is not None)
    assert response.source.source_service == "lotus-core"
    assert response.source.source_route == "/reporting/portfolio-summary/bulk-query"
    assert response.source.source_contract_version == "portfolio-summary-bulk-v1"


def test_advisor_book_summary_openapi_exposes_source_and_coverage_fields() -> None:
    spec = app.openapi()
    operation = spec["paths"]["/api/v1/advisor-book/summary"]["get"]
    summary_schema = spec["components"]["schemas"]["AdvisorBookValueSummary"]
    item_schema = spec["components"]["schemas"]["AdvisorBookValueItem"]

    assert operation["parameters"]
    for field in ("total_value", "cash_value", "invested_value", "covered_portfolio_count"):
        assert field in summary_schema["properties"]
    assert item_schema["properties"]["state"]["enum"] == ["supported", "unavailable"]
    assert item_schema["properties"]["coverage_state"]["enum"] == [
        "COMPLETE",
        "MEASURED_ZERO",
        "CARRY_FORWARD",
        "LOADED_EMPTY",
        "NO_SNAPSHOT",
        "PARTIAL",
        "FX_UNAVAILABLE",
        "INVALID_PORTFOLIO",
    ]
    for field in ("cash_value", "invested_value", "valuation_as_of", "snapshot_date"):
        assert field in item_schema["properties"]
    assert operation["responses"]["200"]["content"]["application/json"]["example"]
