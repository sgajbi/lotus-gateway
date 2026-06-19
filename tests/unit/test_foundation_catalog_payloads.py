from fastapi import HTTPException

from app.services.foundation_catalog_payloads import parse_foundation_catalog_items


def test_foundation_catalog_payloads_parse_aliases_and_sort_by_portfolio_id() -> None:
    items = parse_foundation_catalog_items(
        [
            {
                "portfolio_id": "PF_2002",
                "portfolio_name": "Income Reserve",
                "base_currency": "EUR",
                "cif_id": "CIF_2002",
                "booking_center": "CHPB",
            },
            {
                "id": "PF_1001",
                "label": "Alpha Growth",
                "base_currency": "USD",
                "client_id": "CIF_1001",
                "booking_center_code": "SGPB",
            },
            "skip non-dict rows",
        ]
    )

    assert [item.portfolio_id for item in items] == ["PF_1001", "PF_2002"]
    assert items[0].display_name == "Alpha Growth"
    assert items[0].client_id == "CIF_1001"
    assert items[0].booking_center_code == "SGPB"
    assert items[1].display_name == "Income Reserve"
    assert items[1].client_id == "CIF_2002"
    assert items[1].booking_center_code == "CHPB"


def test_foundation_catalog_payloads_reject_missing_portfolio_id() -> None:
    try:
        parse_foundation_catalog_items([{"portfolio_name": "Missing identifier"}])
    except HTTPException as exc:
        assert exc.status_code == 502
        assert exc.detail == "Invalid lotus-core portfolio catalog item without portfolio_id."
    else:
        raise AssertionError("expected missing portfolio_id to raise HTTPException")
