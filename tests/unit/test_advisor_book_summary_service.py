from datetime import date
from decimal import Decimal

import pytest

from app.services.advisor_book_service import AdvisorBookService, AdvisorBookServiceError
from app.services.advisor_book_summary_service import AdvisorBookSummaryService
from tests.support.advisor_book_fixtures import (
    MembershipClient,
    ValueClient,
    book_caller,
    bulk_payload,
    covered_member,
    membership_payload,
    uncovered_member,
)


def _service(
    membership_payload: dict[str, object],
    value_client: ValueClient,
) -> AdvisorBookSummaryService:
    return AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=MembershipClient(payload=membership_payload)
        ),
        value_client=value_client,
    )


@pytest.mark.asyncio
async def test_summary_uses_one_bulk_read_and_source_owned_aggregate() -> None:
    value_client = ValueClient(
        payload=bulk_payload(
            ["PB_001", "PB_002"],
            [
                covered_member("PB_001", "600.00", "100.00"),
                covered_member("PB_002", "399.99", "50.00"),
            ],
        )
    )
    service = _service(membership_payload("PB_001", "PB_002"), value_client)

    response = await service.get_value_summary(
        caller=book_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="usd",
        correlation_id="corr-summary",
    )

    assert response.summary.state == "supported"
    assert response.summary.total_value == Decimal("999.99")
    assert response.summary.cash_value == Decimal("150.00")
    assert response.summary.invested_value == Decimal("849.99")
    assert response.summary.coverage_state == "COMPLETE"
    assert response.summary.covered_portfolio_count == 2
    assert [item.portfolio_id for item in response.items] == ["PB_001", "PB_002"]
    assert response.items[0].cash_value == Decimal("100.00")
    assert response.items[0].valuation_as_of == date(2026, 4, 10)
    assert response.source.source_route == "/reporting/portfolio-summary/bulk-query"
    assert value_client.calls == [
        {
            "correlation_id": "corr-summary",
            "portfolio_ids": ["PB_001", "PB_002"],
            "as_of_date": "2026-04-10",
            "reporting_currency": "USD",
        }
    ]


@pytest.mark.asyncio
async def test_summary_preserves_source_partial_coverage_without_zero_substitution() -> None:
    value_client = ValueClient(
        payload=bulk_payload(
            ["PB_001", "PB_002"],
            [
                covered_member("PB_001", "600.00", "100.00"),
                uncovered_member("PB_002", "NO_SNAPSHOT"),
            ],
            aggregate_state="PARTIAL",
        )
    )
    service = _service(membership_payload("PB_001", "PB_002"), value_client)

    response = await service.get_value_summary(
        caller=book_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id="corr-partial-summary",
    )

    assert response.summary.state == "partial"
    assert response.summary.total_value is None
    assert response.summary.cash_value is None
    assert response.summary.coverage_state == "PARTIAL"
    assert response.summary.covered_portfolio_count == 1
    assert response.items[1].state == "unavailable"
    assert response.items[1].total_value is None
    assert response.items[1].coverage_state == "NO_SNAPSHOT"
    assert response.items[1].coverage_reason == "no_snapshot_rows_for_as_of_date"


@pytest.mark.asyncio
async def test_summary_reports_measured_zero_as_a_business_fact() -> None:
    empty_member = covered_member("PB_002", "0.00", "0.00")
    empty_member["coverage_state"] = "MEASURED_ZERO"
    empty_member["coverage_reason"] = "snapshot_measured_zero"
    value_client = ValueClient(
        payload=bulk_payload(
            ["PB_001", "PB_002"],
            [covered_member("PB_001", "600.00", "100.00"), empty_member],
        )
    )
    service = _service(membership_payload("PB_001", "PB_002"), value_client)

    response = await service.get_value_summary(
        caller=book_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id="corr-measured-zero-summary",
    )

    assert response.summary.state == "supported"
    assert response.summary.covered_portfolio_count == 2
    assert response.items[1].state == "supported"
    assert response.items[1].total_value == Decimal("0.00")
    assert response.items[1].coverage_state == "MEASURED_ZERO"


@pytest.mark.asyncio
async def test_summary_rejects_totals_that_contradict_source_coverage() -> None:
    contradiction = uncovered_member("PB_002", "NO_SNAPSHOT")
    contradiction["totals"] = covered_member("PB_002", "1.00", "1.00")["totals"]
    value_client = ValueClient(
        payload=bulk_payload(
            ["PB_001", "PB_002"],
            [covered_member("PB_001", "600.00", "100.00"), contradiction],
            aggregate_state="PARTIAL",
        )
    )
    service = _service(membership_payload("PB_001", "PB_002"), value_client)

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=book_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-contradiction-summary",
        )

    assert raised.value.code == "advisor_book_value_source_contract_invalid"


@pytest.mark.asyncio
async def test_summary_returns_empty_without_fabricating_a_value_read() -> None:
    value_client = ValueClient()
    service = _service(membership_payload(), value_client)

    response = await service.get_value_summary(
        caller=book_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="usd",
        correlation_id="corr-empty-summary",
    )

    assert response.summary.state == "empty"
    assert response.summary.reporting_currency == "USD"
    assert response.summary.total_value is None
    assert response.items == []
    assert value_client.calls == []


@pytest.mark.parametrize(
    "mutate",
    (
        pytest.param(
            lambda payload: payload.update({"requested_portfolio_ids": ["PB_002", "PB_001"]}),
            id="reordered-request-echo",
        ),
        pytest.param(
            lambda payload: payload["portfolios"].pop(),
            id="missing-member-item",
        ),
        pytest.param(
            lambda payload: payload.update({"resolved_as_of_date": "2026-04-11"}),
            id="different-as-of",
        ),
        pytest.param(
            lambda payload: payload.update({"reporting_currency": "SGD"}),
            id="different-currency",
        ),
    ),
)
@pytest.mark.asyncio
async def test_summary_rejects_source_identity_drift(mutate) -> None:
    payload = bulk_payload(
        ["PB_001", "PB_002"],
        [
            covered_member("PB_001", "600.00", "100.00"),
            covered_member("PB_002", "399.99", "50.00"),
        ],
    )
    mutate(payload)
    service = _service(membership_payload("PB_001", "PB_002"), ValueClient(payload=payload))

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=book_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-mismatch-summary",
        )

    assert raised.value.code == "advisor_book_value_source_contract_invalid"
    assert raised.value.status_code == 502


@pytest.mark.asyncio
async def test_summary_maps_core_failure_to_product_safe_error() -> None:
    service = _service(membership_payload("PB_001"), ValueClient(status_code=503))

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=book_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-unavailable-summary",
        )

    assert raised.value.code == "advisor_book_value_source_unavailable"
