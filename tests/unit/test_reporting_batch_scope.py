from datetime import date

import pytest

from app.contracts.advisor_book import AdvisorBookPortfolio
from app.contracts.reporting_batches import BatchCreateRequest
from app.services.advisor_book_service import (
    AdvisorBookServiceError,
    ResolvedAdvisorBookSelection,
)
from app.services.reporting_batch_scope import (
    ReportingBatchScopeError,
    ReportingBatchScopeResolver,
)


class _PortfolioResolver:
    def __init__(
        self,
        *,
        tenant_id: str = "tenant-sg",
        error: AdvisorBookServiceError | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def resolve_portfolios(self, **kwargs) -> ResolvedAdvisorBookSelection:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return ResolvedAdvisorBookSelection(
            tenant_id=self.tenant_id,
            portfolios=tuple(_portfolio(portfolio_id) for portfolio_id in kwargs["portfolio_ids"]),
        )


def _portfolio(portfolio_id: str) -> AdvisorBookPortfolio:
    return AdvisorBookPortfolio(
        portfolio_id=portfolio_id,
        display_name=portfolio_id,
        client_id="CIF_SG_001",
        base_currency="USD",
        booking_center_code="SG",
        mandate_type="DISCRETIONARY",
        status="ACTIVE",
        opened_on=date(2025, 3, 31),
        closed_on=None,
        membership_source="PortfolioManagerBookMembership:v1",
        membership_reference=f"portfolio:{portfolio_id}",
        membership_basis="governed_role_assignment",
    )


def _request() -> BatchCreateRequest:
    return BatchCreateRequest(
        selector_mode="explicit_portfolio_list",
        portfolio_ids=["PB_002", "PB_001"],
        as_of_date=date(2026, 4, 22),
        requested_output_formats=["pdf"],
        reporting_currency="USD",
        options={"sections": ["OVERVIEW"]},
        max_batch_size=250,
    )


def _headers(**overrides: str) -> dict[str, str]:
    headers = {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
    }
    headers.update(overrides)
    return headers


@pytest.mark.asyncio
async def test_scope_resolver_builds_candidates_only_from_verified_membership() -> None:
    portfolio_resolver = _PortfolioResolver()
    resolver = ReportingBatchScopeResolver(portfolio_resolver=portfolio_resolver)

    materialized = await resolver.materialize_request(
        request=_request(),
        caller_headers=_headers(),
        correlation_id="corr-batch",
    )

    assert [candidate.portfolio_id for candidate in materialized.source_candidates] == [
        "PB_002",
        "PB_001",
    ]
    assert all(candidate.tenant_id == "tenant-sg" for candidate in materialized.source_candidates)
    assert all(candidate.region == "APAC" for candidate in materialized.source_candidates)
    assert all(
        candidate.source_object == "PortfolioManagerBookMembership:v1"
        for candidate in materialized.source_candidates
    )
    assert portfolio_resolver.calls[0]["portfolio_ids"] == ("PB_002", "PB_001")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("headers", "expected_code", "expected_status"),
    [
        (
            _headers(**{"X-Caller-Capabilities": ""}),
            "report_batch_caller_context_missing",
            400,
        ),
        (_headers(**{"X-Role": "CLIENT"}), "report_batch_access_denied", 403),
        (_headers(**{"X-Actor-Id": "not valid!"}), "report_batch_caller_context_invalid", 400),
    ],
)
async def test_scope_resolver_requires_trusted_own_book_authority(
    headers: dict[str, str],
    expected_code: str,
    expected_status: int,
) -> None:
    resolver = ReportingBatchScopeResolver(portfolio_resolver=_PortfolioResolver())

    with pytest.raises(ReportingBatchScopeError) as raised:
        await resolver.materialize_request(
            request=_request(),
            caller_headers=headers,
            correlation_id="corr-blocked",
        )

    assert raised.value.code == expected_code
    assert raised.value.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source_code", "expected_code", "expected_status"),
    [
        (
            "advisor_book_portfolio_not_available",
            "report_batch_portfolio_not_entitled",
            403,
        ),
        ("advisor_book_portfolio_inactive", "report_batch_portfolio_inactive", 409),
        ("advisor_book_tenant_scope_unverified", "report_batch_scope_unverified", 502),
        ("advisor_book_source_unavailable", "report_batch_scope_unavailable", 502),
    ],
)
async def test_scope_resolver_maps_source_failures_without_report_fan_out(
    source_code: str,
    expected_code: str,
    expected_status: int,
) -> None:
    source_error = AdvisorBookServiceError(
        code=source_code,
        message="unsafe source detail",
        status_code=502,
    )
    resolver = ReportingBatchScopeResolver(
        portfolio_resolver=_PortfolioResolver(error=source_error)
    )

    with pytest.raises(ReportingBatchScopeError) as raised:
        await resolver.materialize_request(
            request=_request(),
            caller_headers=_headers(),
            correlation_id="corr-source-blocked",
        )

    assert raised.value.code == expected_code
    assert raised.value.status_code == expected_status
    assert "unsafe source detail" not in raised.value.message


@pytest.mark.asyncio
async def test_scope_resolver_rejects_cross_tenant_resolution() -> None:
    resolver = ReportingBatchScopeResolver(
        portfolio_resolver=_PortfolioResolver(tenant_id="tenant-other")
    )

    with pytest.raises(ReportingBatchScopeError) as raised:
        await resolver.materialize_request(
            request=_request(),
            caller_headers=_headers(),
            correlation_id="corr-cross-tenant",
        )

    assert raised.value.code == "report_batch_scope_unverified"
    assert raised.value.status_code == 502
