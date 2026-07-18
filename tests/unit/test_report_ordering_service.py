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
