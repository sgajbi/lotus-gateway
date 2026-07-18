import pytest
from pydantic import ValidationError

from app.services.advisor_book_source_contract import SourceAdvisorBookResponse


def _source_payload() -> dict[str, object]:
    return {
        "product_name": "PortfolioManagerBookMembership",
        "product_version": "v1",
        "portfolio_manager_id": "PM_SG_001",
        "tenant_id": None,
        "generated_at": "2026-04-10T02:00:00Z",
        "as_of_date": "2026-04-10",
        "latest_evidence_timestamp": "2026-04-10T01:59:00Z",
        "snapshot_id": "pm_book_membership:2e7dfe0c",
        "content_hash": "sha256:0123456789abcdef",
        "data_quality_status": "COMPLETE",
        "source_evidence_current": True,
        "freshness_status": "CURRENT",
        "booking_center_code": "Singapore",
        "members": [
            {
                "portfolio_id": "PB_SG_001",
                "client_id": "CIF_SG_001",
                "booking_center_code": "Singapore",
                "portfolio_type": "ADVISORY",
                "status": "ACTIVE",
                "open_date": "2025-03-31",
                "close_date": None,
                "base_currency": "SGD",
                "source_record_id": "portfolio:PB_SG_001",
                "membership_source": "party_role_assignment",
                "role_type": "ADVISOR",
            }
        ],
        "supportability": {
            "state": "READY",
            "reason": "PORTFOLIO_MANAGER_BOOK_READY",
            "returned_portfolio_count": 1,
            "filters_applied": ["booking_center_code"],
        },
        "lineage": {"source_owner": "lotus-core"},
        "restatement_version": "restatement-v1",
    }


def test_source_advisor_book_contract_accepts_current_core_shape() -> None:
    source = SourceAdvisorBookResponse.model_validate(_source_payload())

    assert source.portfolio_manager_id == "PM_SG_001"
    assert source.members[0].membership_source == "party_role_assignment"
    assert source.tenant_id is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product_name", "PortfolioCatalogue"),
        ("product_version", "v2"),
        ("members.0.membership_source", "derived_guess"),
    ],
)
def test_source_advisor_book_contract_rejects_unsupported_source_identity(
    field: str, value: str
) -> None:
    payload = _source_payload()
    if field.startswith("members"):
        members = payload["members"]
        assert isinstance(members, list)
        members[0]["membership_source"] = value
    else:
        payload[field] = value

    with pytest.raises(ValidationError):
        SourceAdvisorBookResponse.model_validate(payload)
