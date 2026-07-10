from fastapi import HTTPException

from app.services.foundation_core_market_value import extract_core_market_value
from app.services.foundation_core_snapshot import FoundationCoreSnapshotMapper


def test_foundation_core_snapshot_mapper_parses_defensive_snapshot_branches() -> None:
    mapper = FoundationCoreSnapshotMapper()

    portfolio, summary, allocations, top_positions, as_of_date = mapper.parse_core_snapshot(
        fallback_portfolio_id="PF_FALLBACK",
        fallback_as_of_date="2026-03-31",
        portfolio_payload={"name": "Fallback Name"},
        payload={
            "portfolio_id": "PF_FALLBACK",
            "as_of_date": "2026-03-30",
            "valuation_context": {"portfolio_currency": "EUR"},
            "sections": {
                "positions_baseline": [
                    "skip-me",
                    {"security_id": None, "asset_class": "Alternatives", "value_base": "125.55"},
                    {"security_id": "EQ_1", "valuation": {"market_value_base": "374.45"}},
                ],
                "portfolio_totals": [],
                "instrument_enrichment": [
                    "skip-me",
                    {"security_id": "EQ_1", "asset_class_name": "Equity"},
                ],
            },
        },
    )

    assert portfolio.portfolio_id == "PF_FALLBACK"
    assert portfolio.display_name == "Fallback Name"
    assert portfolio.base_currency == "EUR"
    assert summary.market_value_base == 0.0
    assert len(top_positions) == 2
    assert summary.position_count == 2
    assert [bucket.asset_class for bucket in allocations] == ["Alternatives", "Equity"]
    assert allocations[0].weight_pct is None
    assert allocations[1].market_value_base == 374.45
    assert as_of_date == "2026-03-30"


def test_foundation_core_snapshot_mapper_ignores_legacy_nested_portfolio_and_metadata() -> None:
    mapper = FoundationCoreSnapshotMapper()

    portfolio, _summary, _allocations, _top_positions, as_of_date = mapper.parse_core_snapshot(
        fallback_portfolio_id="PF_IGNORED",
        fallback_as_of_date="2026-03-31",
        portfolio_payload={
            "portfolio_id": "PF_IDENTITY",
            "portfolio_name": "Identity Name",
            "base_currency": "USD",
        },
        payload={
            "portfolio_id": "PF_SNAPSHOT",
            "as_of_date": "2026-03-30",
            "portfolio": {"portfolio_id": "PF_LEGACY", "portfolio_name": "Legacy Name"},
            "metadata": {"business_date": "1999-01-01"},
            "sections": {
                "positions_baseline": [],
                "portfolio_totals": {},
                "instrument_enrichment": [],
            },
        },
    )

    assert portfolio.portfolio_id == "PF_SNAPSHOT"
    assert portfolio.display_name == "Identity Name"
    assert as_of_date == "2026-03-30"


def test_foundation_core_snapshot_mapper_rejects_invalid_snapshot_payload() -> None:
    mapper = FoundationCoreSnapshotMapper()

    try:
        mapper.parse_core_snapshot(
            fallback_portfolio_id="PF_BAD",
            fallback_as_of_date="2026-03-31",
            portfolio_payload={},
            payload={"sections": []},
        )
    except HTTPException as exc:
        assert exc.status_code == 502
        assert exc.detail == "Invalid lotus-core foundation snapshot payload structure."
    else:
        raise AssertionError("expected invalid snapshot payload to raise HTTPException")


def test_foundation_core_snapshot_mapper_extracts_market_value() -> None:
    mapper = FoundationCoreSnapshotMapper()

    assert str(extract_core_market_value({"valuation": {"market_value": "88.10"}})) == "88.10"
    assert mapper.extract_market_value({"valuation": {"market_value": "88.10"}}) == 88.1
    assert (
        mapper.extract_market_value(
            {"valuation": {"market_value_base": "bad"}, "current_value": "45.25"}
        )
        == 45.25
    )
    assert mapper.extract_market_value({"market_value_base": "bad", "value_base": "17.75"}) == 17.75
    assert mapper.extract_market_value({"valuation": {"market_value_base": "bad"}}) is None
