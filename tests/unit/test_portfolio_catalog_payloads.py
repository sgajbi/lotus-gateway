from app.services.portfolio_catalog_payloads import parse_catalog_item, parse_catalog_items


def test_parse_catalog_items_sorts_and_skips_non_object_payloads() -> None:
    items = parse_catalog_items(
        [
            {"portfolio_id": "PF_2002", "base_currency": "EUR"},
            "not-an-item",
            {"portfolio_id": "PF_1001", "base_currency": "USD"},
        ]
    )

    assert [item.portfolio_id for item in items] == ["PF_1001", "PF_2002"]
    assert [item.base_currency for item in items] == ["USD", "EUR"]


def test_parse_catalog_item_preserves_metadata_aliases_and_display_name_fallbacks() -> None:
    item = parse_catalog_item(
        {
            "portfolio_id": " PF_3003 ",
            "portfolio_name": None,
            "base_currency": "CHF",
            "cif_id": "CIF_3",
            "booking_center": "CHPB",
            "portfolio_type": "DISCRETIONARY",
            "status": "ACTIVE",
        }
    )

    assert item.portfolio_id == "PF_3003"
    assert item.display_name == "PF_3003"
    assert item.base_currency == "CHF"
    assert item.client_id == "CIF_3"
    assert item.booking_center_code == "CHPB"
    assert item.portfolio_type == "DISCRETIONARY"
    assert item.status == "ACTIVE"


def test_parse_catalog_item_prefers_canonical_metadata_fields() -> None:
    item = parse_catalog_item(
        {
            "portfolio_id": "PF_4004",
            "portfolio_name": "Core Growth",
            "base_currency": "USD",
            "client_id": "CIF_CANONICAL",
            "cif_id": "CIF_ALIAS",
            "booking_center_code": "SGPB",
            "booking_center": "CHPB",
        }
    )

    assert item.display_name == "Core Growth"
    assert item.client_id == "CIF_CANONICAL"
    assert item.booking_center_code == "SGPB"
