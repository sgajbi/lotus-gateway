import json
from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "domain-data-products"
    / "lotus-gateway-consumers.v1.json"
)


def _consumer_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_gateway_declares_the_implemented_advisor_book_dependency() -> None:
    contract = _consumer_contract()

    assert contract["contract_id"] == "domain-data-product-consumers"
    assert contract["contract_version"] == "1.0.0"
    assert contract["governed_by_rfc"] == "RFC-0084"
    assert contract["consumer_repository"] == "lotus-gateway"
    assert len(contract["dependencies"]) == 1

    dependency = contract["dependencies"][0]
    assert dependency == {
        "product_name": "PortfolioManagerBookMembership",
        "producer_repository": "lotus-core",
        "required_product_version": "v1",
        "consumption_mode": "api_read",
        "business_purpose": (
            "Resolve the trusted caller's effective own-book portfolio memberships for the "
            "product-facing advisor-book facade without moving assignment ownership into Gateway."
        ),
        "validation_lanes": ["feature", "pr-merge", "platform-end-to-end"],
        "failure_posture": "fail_closed",
        "required_trust_metadata": [
            "product_name",
            "product_version",
            "portfolio_manager_id",
            "booking_center_code",
            "generated_at",
            "as_of_date",
            "data_quality_status",
            "source_evidence_current",
            "freshness_status",
            "content_hash",
        ],
        "migration_posture": {"status": "current"},
    }
