from typing import Any

import pytest

from app.contracts.reporting_batches import BatchCreateRequest
from app.services.advisor_book_service_errors import source_unavailable
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse
from app.services.reporting_batch_preflight_service import ReportingBatchPreflightService
from app.services.reporting_batch_scope import ReportingBatchScopeError


class _MembershipService:
    def __init__(self, source: dict[str, Any] | None = None, error: Exception | None = None):
        self.source = SourceAdvisorBookResponse.model_validate(source) if source else None
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def load_membership_source(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.source


class _ReportingCatalogueClient:
    def __init__(self, payload: dict[str, Any] | None = None, status_code: int = 200):
        self.payload = payload or _catalogue_payload()
        self.status_code = status_code
        self.calls: list[str] = []

    async def get_report_ordering_catalogue(self, *, correlation_id: str):
        self.calls.append(correlation_id)
        return self.status_code, self.payload


def _request(*portfolio_ids: str) -> BatchCreateRequest:
    return BatchCreateRequest(
        selector_mode="explicit_portfolio_list",
        portfolio_ids=list(portfolio_ids),
        as_of_date="2026-04-22",
        requested_output_formats=["pdf"],
        reporting_currency="USD",
        options={"sections": ["OVERVIEW"]},
    )


def _headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor-1",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
        "X-Caller-Portfolio-Ids": "browser-supplied-id-must-not-authorize",
    }


def _source_payload(
    members: list[dict[str, Any]],
    *,
    supportability: str = "READY",
    tenant_id: str | None = "tenant-sg",
) -> dict[str, Any]:
    return {
        "product_name": "PortfolioManagerBookMembership",
        "product_version": "v1",
        "portfolio_manager_id": "advisor-1",
        "tenant_id": tenant_id,
        "generated_at": "2026-04-22T09:00:00Z",
        "as_of_date": "2026-04-22",
        "latest_evidence_timestamp": "2026-04-22T08:59:00Z",
        "snapshot_id": "snapshot-1",
        "content_hash": "sha256:membership",
        "data_quality_status": "ACCEPTED",
        "source_evidence_current": True,
        "freshness_status": "CURRENT",
        "booking_center_code": "SG",
        "members": members,
        "supportability": {
            "state": supportability,
            "reason": "membership_source",
            "returned_portfolio_count": len(members),
            "filters_applied": ["portfolio_manager_id", "as_of_date"],
        },
        "lineage": {"source_system": "lotus-core"},
    }


def _member(portfolio_id: str, *, status: str = "ACTIVE") -> dict[str, Any]:
    return {
        "portfolio_id": portfolio_id,
        "client_id": "CIF_SG_001",
        "booking_center_code": "SG",
        "portfolio_type": "ADVISORY",
        "status": status,
        "open_date": "2025-01-01",
        "close_date": None,
        "base_currency": "SGD",
        "source_record_id": f"membership:{portfolio_id}",
        "membership_source": "party_role_assignment",
        "role_type": "ADVISOR",
    }


def _catalogue_payload(
    *,
    output_state: str = "ready",
    status: str = "ready",
) -> dict[str, Any]:
    return {
        "source_service": "lotus-report",
        "contract_version": "report-ordering-catalogue.v1",
        "report_families": [
            {
                "report_family_id": "portfolio_review",
                "business_label": "Portfolio review",
                "description": "Review report.",
                "intended_use": "advisor_client_portfolio_review",
                "audience_roles": ["client_advisor", "portfolio_manager"],
                "client_release_posture": "advisor_review_required_distribution_not_supported",
                "ordering_modes": [
                    {
                        "mode_id": "explicit_portfolio_batch",
                        "business_label": "Portfolio batch",
                        "description": "Create a bounded portfolio batch.",
                        "default_output_format": "pdf",
                        "interactive": True,
                    }
                ],
                "output_formats": [
                    {
                        "format_id": "pdf",
                        "business_label": "PDF",
                        "use_posture": "governed_document",
                        "state": output_state,
                        "reason_code": "output_posture",
                    }
                ],
                "supportability": {
                    "state": status,
                    "reason_code": "catalogue_posture",
                    "message": "Catalogue posture.",
                },
            }
        ],
        "supportability": {
            "state": status,
            "reason_code": "catalogue_posture",
            "message": "Catalogue posture.",
        },
    }


@pytest.mark.asyncio
async def test_preflight_maps_ordered_membership_postures_without_browser_authority() -> None:
    membership = _MembershipService(
        _source_payload(
            [
                _member("PB_READY"),
                _member("PB_INACTIVE", status="CLOSED"),
            ]
        )
    )
    catalogue = _ReportingCatalogueClient()
    service = ReportingBatchPreflightService(
        membership_service=membership,
        reporting_client=catalogue,
    )

    response = await service.preflight(
        request=_request("PB_READY", "PB_MISSING", "PB_INACTIVE"),
        caller_headers=_headers(),
        correlation_id="corr-preflight",
    )

    assert [item.portfolio_id for item in response.candidates] == [
        "PB_READY",
        "PB_MISSING",
        "PB_INACTIVE",
    ]
    assert [item.state for item in response.candidates] == [
        "ready",
        "permission_blocked",
        "stale",
    ]
    assert response.state == "partial"
    assert response.ready_count == 1
    assert response.permission_blocked_count == 1
    assert response.stale_count == 1
    assert response.partial_count == 0
    assert response.unavailable_count == 0
    assert response.candidates[0].source_evidence.membership_reference == "membership:PB_READY"
    assert membership.calls[0]["include_inactive"] is True
    assert len(membership.calls) == 1
    assert catalogue.calls == ["corr-preflight"]


@pytest.mark.asyncio
async def test_preflight_fails_closed_when_membership_source_is_unavailable() -> None:
    service = ReportingBatchPreflightService(
        membership_service=_MembershipService(error=source_unavailable()),
        reporting_client=_ReportingCatalogueClient(),
    )

    response = await service.preflight(
        request=_request("PB_READY", "PB_OTHER"),
        caller_headers=_headers(),
        correlation_id="corr-preflight-unavailable",
    )

    assert response.state == "unavailable"
    assert response.source_posture.state == "unavailable"
    assert [item.reason_code for item in response.candidates] == [
        "membership_source_unavailable",
        "membership_source_unavailable",
    ]
    assert response.candidates[0].source_evidence is None


@pytest.mark.asyncio
async def test_preflight_does_not_claim_ready_when_requested_output_is_unavailable() -> None:
    membership = _MembershipService(_source_payload([_member("PB_READY")]))
    catalogue = _ReportingCatalogueClient(_catalogue_payload(output_state="unavailable"))
    service = ReportingBatchPreflightService(
        membership_service=membership,
        reporting_client=catalogue,
    )

    response = await service.preflight(
        request=_request("PB_READY"),
        caller_headers=_headers(),
        correlation_id="corr-preflight-config",
    )

    assert response.state == "unavailable"
    assert response.configuration_posture.state == "unavailable"
    assert response.configuration_posture.reason_code == "report_output_format_unavailable"
    assert response.candidates[0].state == "unavailable"
    assert response.candidates[0].reason_code == "report_output_format_unavailable"


@pytest.mark.asyncio
async def test_preflight_surfaces_degraded_report_configuration_as_partial() -> None:
    membership = _MembershipService(_source_payload([_member("PB_READY")]))
    catalogue = _ReportingCatalogueClient(_catalogue_payload(output_state="partial"))
    service = ReportingBatchPreflightService(
        membership_service=membership,
        reporting_client=catalogue,
    )

    response = await service.preflight(
        request=_request("PB_READY"),
        caller_headers=_headers(),
        correlation_id="corr-preflight-config-partial",
    )

    assert response.state == "partial"
    assert response.configuration_posture.state == "partial"
    assert response.candidates[0].state == "partial"
    assert response.partial_count == 1


@pytest.mark.asyncio
async def test_preflight_rejects_missing_trusted_caller_context_before_source_call() -> None:
    membership = _MembershipService(_source_payload([_member("PB_READY")]))
    service = ReportingBatchPreflightService(
        membership_service=membership,
        reporting_client=_ReportingCatalogueClient(),
    )

    with pytest.raises(ReportingBatchScopeError) as exc_info:
        await service.preflight(
            request=_request("PB_READY"),
            caller_headers={"X-Role": "ADVISOR"},
            correlation_id="corr-preflight-context",
        )

    assert exc_info.value.code == "report_batch_caller_context_missing"
    assert membership.calls == []
