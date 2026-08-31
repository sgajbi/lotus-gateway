from typing import Any

import pytest

from app.contracts.report_ordering import ReportScopeSelection
from app.services.report_ordering_service import ReportOrderingService


class StubReportingCatalogueClient:
    def __init__(
        self,
        status_code: int = 200,
        payload: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.payload = payload or _source_payload()
        self.error = error
        self.calls: list[str] = []

    async def get_report_ordering_catalogue(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(correlation_id)
        if self.error is not None:
            raise self.error
        return self.status_code, self.payload


def _source_payload() -> dict[str, Any]:
    return {
        "source_service": "lotus-report",
        "contract_version": "report-ordering-catalogue.v1",
        "report_families": [
            {
                "report_family_id": "portfolio_review",
                "business_label": "Portfolio review report",
                "description": "Advisor portfolio review evidence.",
                "intended_use": "advisor_client_portfolio_review",
                "audience_roles": ["client_advisor", "portfolio_manager"],
                "client_release_posture": ("advisor_review_required_distribution_not_supported"),
                "ordering_modes": [
                    {
                        "mode_id": "single_portfolio",
                        "business_label": "Single portfolio",
                        "description": "Create one report.",
                        "default_output_format": "json",
                        "interactive": True,
                    }
                ],
                "output_formats": [
                    {
                        "format_id": "json",
                        "business_label": "Structured data package",
                        "use_posture": "system_integration",
                        "state": "ready",
                        "reason_code": "report_data_ready",
                    }
                ],
                "supportability": {
                    "state": "ready",
                    "reason_code": "report_family_ready",
                    "message": "Ready.",
                },
            }
        ],
        "supportability": {
            "state": "ready",
            "reason_code": "report_catalogue_ready",
            "message": "Ready.",
        },
    }


def _caller_headers() -> dict[str, str]:
    return {
        "X-Role": "client_advisor",
        "X-Caller-Portfolio-Ids": "portfolio-1",
    }


@pytest.mark.asyncio
async def test_service_projects_valid_source_catalogue() -> None:
    client = StubReportingCatalogueClient()
    service = ReportOrderingService(reporting_client=client)

    response = await service.get_ordering_options(
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        caller_headers=_caller_headers(),
        correlation_id="corr-ordering",
    )

    assert response.catalogue_availability.state == "ready"
    assert response.scope_eligibility.state == "ready"
    assert response.report_families[0].report_family_id == "portfolio_review"
    assert client.calls == ["corr-ordering"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [400, 404, 503])
async def test_service_maps_source_http_failures_to_typed_unavailable(status_code: int) -> None:
    service = ReportOrderingService(
        reporting_client=StubReportingCatalogueClient(
            status_code=status_code,
            payload={"detail": "raw upstream failure must not escape"},
        )
    )

    response = await service.get_ordering_options(
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        caller_headers=_caller_headers(),
        correlation_id="corr-ordering",
    )

    serialized = response.model_dump(by_alias=True, mode="json")
    assert response.catalogue_availability.reason_code == "report_catalogue_unavailable"
    assert response.report_families == []
    assert "raw upstream failure" not in str(serialized)


@pytest.mark.asyncio
async def test_service_maps_invalid_source_contract_to_typed_unavailable() -> None:
    service = ReportOrderingService(
        reporting_client=StubReportingCatalogueClient(
            payload={**_source_payload(), "unexpected": "unsafe"},
        )
    )

    response = await service.get_ordering_options(
        selection=None,
        caller_headers=_caller_headers(),
        correlation_id="corr-ordering",
    )

    assert response.catalogue_availability.reason_code == "report_catalogue_contract_invalid"
    assert response.scope_eligibility.reason_code == "scope_selection_required"


@pytest.mark.asyncio
async def test_service_maps_transport_exception_without_exposing_exception_text() -> None:
    service = ReportOrderingService(
        reporting_client=StubReportingCatalogueClient(
            error=RuntimeError("secret-shaped connection detail"),
        )
    )

    response = await service.get_ordering_options(
        selection=None,
        caller_headers=_caller_headers(),
        correlation_id="corr-ordering",
    )

    serialized = response.model_dump(by_alias=True, mode="json")
    assert response.catalogue_availability.reason_code == "report_catalogue_unavailable"
    assert "secret-shaped" not in str(serialized)


class StubAvailabilityReportingClient(StubReportingCatalogueClient):
    def __init__(
        self,
        *,
        availability_status: int = 200,
        availability_payload: dict[str, Any] | None = None,
        availability_error: Exception | None = None,
    ) -> None:
        super().__init__(payload=_source_payload_with_commentary_section())
        self.availability_status = availability_status
        self.availability_payload = availability_payload or {}
        self.availability_error = availability_error
        self.availability_calls: list[dict[str, Any]] = []

    async def get_advisor_commentary_availability(
        self,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        self.availability_calls.append(kwargs)
        if self.availability_error is not None:
            raise self.availability_error
        return self.availability_status, self.availability_payload


def _source_payload_with_commentary_section() -> dict[str, Any]:
    payload = _source_payload()
    payload["report_families"][0]["sections"] = [
        {
            "section_id": "OVERVIEW",
            "business_label": "Overview",
            "description": "Portfolio overview.",
            "display_order": 20,
            "selection_posture": "optional",
            "default_selected": True,
        },
        {
            "section_id": "ADVISOR_COMMENTARY",
            "business_label": "Advisor commentary",
            "description": "Reviewed advisor narrative.",
            "display_order": 25,
            "selection_posture": "optional",
            "default_selected": False,
            "dependency_field_ids": ["advisor_brief_run_id"],
        },
    ]
    return payload


def _ready_availability_payload() -> dict[str, Any]:
    return {
        "source_service": "lotus-report",
        "contract_version": "advisor-commentary-availability.v1",
        "section_id": "ADVISOR_COMMENTARY",
        "state": "ready",
        "reason_code": "advisor_brief_accepted",
        "message": "An accepted brief exists.",
        "accepted_brief": {
            "run_id": "wfr-accepted-001",
            "reviewed_by": "banker.sg.301",
            "reviewed_at": "2026-08-30T09:05:00Z",
            "content_hash": "c" * 64,
            "as_of_date": "2026-04-22",
            "reporting_currency": "USD",
        },
    }


def _tenant_caller_headers() -> dict[str, str]:
    return {**_caller_headers(), "X-Tenant-Id": "tenant-sg-001"}


def _commentary_section(response: Any) -> Any:
    family = response.report_families[0]
    return next(
        section for section in family.sections if section.section_id == "ADVISOR_COMMENTARY"
    )


@pytest.mark.asyncio
async def test_portfolio_scope_composes_ready_section_availability() -> None:
    """Issue #688 (rescoped): a portfolio scope with an accepted brief marks
    the ADVISOR_COMMENTARY section ready and hands Workbench the run id the
    order must carry; other sections are untouched."""

    client = StubAvailabilityReportingClient(availability_payload=_ready_availability_payload())
    service = ReportOrderingService(reporting_client=client)

    response = await service.get_ordering_options(
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        caller_headers=_tenant_caller_headers(),
        correlation_id="corr-availability",
        as_of_date="2026-04-22",
        reporting_currency="USD",
    )

    section = _commentary_section(response)
    assert section.availability is not None
    assert section.availability.state == "ready"
    assert section.availability.reason_code == "advisor_brief_accepted"
    assert section.availability.accepted_brief is not None
    assert section.availability.accepted_brief.run_id == "wfr-accepted-001"
    assert section.availability.accepted_brief.reviewed_by == "banker.sg.301"
    overview = next(
        item for item in response.report_families[0].sections if item.section_id == "OVERVIEW"
    )
    assert overview.availability is None
    assert client.availability_calls == [
        {
            "portfolio_id": "portfolio-1",
            "tenant_id": "tenant-sg-001",
            "correlation_id": "corr-availability",
            "as_of_date": "2026-04-22",
            "reporting_currency": "USD",
        }
    ]


@pytest.mark.asyncio
async def test_portfolio_scope_passes_unavailable_reasons_through_untranslated() -> None:
    for reason in ("advisor_brief_not_reviewed", "advisor_brief_context_mismatch"):
        client = StubAvailabilityReportingClient(
            availability_payload={
                "source_service": "lotus-report",
                "contract_version": "advisor-commentary-availability.v1",
                "section_id": "ADVISOR_COMMENTARY",
                "state": "unavailable",
                "reason_code": reason,
                "message": "Not orderable yet.",
                "accepted_brief": None,
            }
        )
        service = ReportOrderingService(reporting_client=client)

        response = await service.get_ordering_options(
            selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
            caller_headers=_tenant_caller_headers(),
            correlation_id="corr-availability",
        )

        section = _commentary_section(response)
        assert section.availability is not None
        assert section.availability.state == "unavailable"
        assert section.availability.reason_code == reason
        assert section.availability.accepted_brief is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_kwargs",
    [
        {"availability_error": RuntimeError("connection reset")},
        {"availability_status": 503, "availability_payload": {"detail": "down"}},
        {"availability_status": 200, "availability_payload": {"unexpected": "shape"}},
    ],
)
async def test_unanswerable_lookups_become_availability_unknown_not_not_reviewed(
    client_kwargs: dict[str, Any],
) -> None:
    """A failed or unrecognisable lookup proves nothing: it must surface as
    advisor_brief_availability_unknown, never as not_reviewed, and must not
    fail the whole options response."""

    client = StubAvailabilityReportingClient(**client_kwargs)
    service = ReportOrderingService(reporting_client=client)

    response = await service.get_ordering_options(
        selection=ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
        caller_headers=_tenant_caller_headers(),
        correlation_id="corr-availability",
    )

    assert response.catalogue_availability.state == "ready"
    section = _commentary_section(response)
    assert section.availability is not None
    assert section.availability.state == "unavailable"
    assert section.availability.reason_code == "advisor_brief_availability_unknown"
    assert "does not mean no accepted brief exists" in section.availability.message


@pytest.mark.asyncio
async def test_non_portfolio_scopes_do_not_evaluate_section_availability() -> None:
    """Client/book scopes and tenantless callers leave availability absent
    (not evaluated) and never call the lookup - absent is distinct from
    unavailable."""

    for selection, headers in [
        (ReportScopeSelection(scope_type="client", scope_id="client-1"), _tenant_caller_headers()),
        (None, _tenant_caller_headers()),
        (
            ReportScopeSelection(scope_type="portfolio", scope_id="portfolio-1"),
            _caller_headers(),
        ),
    ]:
        client = StubAvailabilityReportingClient(availability_payload=_ready_availability_payload())
        service = ReportOrderingService(reporting_client=client)

        response = await service.get_ordering_options(
            selection=selection,
            caller_headers=headers,
            correlation_id="corr-availability",
        )

        section = _commentary_section(response)
        assert section.availability is None
        assert client.availability_calls == []
