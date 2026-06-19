from typing import Any

from fastapi import HTTPException, status

from app.contracts.foundation import FoundationPortfolioCatalogItem


def parse_foundation_catalog_items(
    items_payload: list[Any],
) -> list[FoundationPortfolioCatalogItem]:
    items = [
        parse_foundation_catalog_item(item) for item in items_payload if isinstance(item, dict)
    ]
    items.sort(key=lambda item: item.portfolio_id)
    return items


def parse_foundation_catalog_item(item: dict[str, Any]) -> FoundationPortfolioCatalogItem:
    portfolio_id = str(item.get("portfolio_id", item.get("id", ""))).strip()
    if not portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid lotus-core portfolio catalog item without portfolio_id.",
        )
    display_name = str(
        item.get("portfolio_name")
        or item.get("name")
        or item.get("label")
        or item.get("display_name")
        or portfolio_id
    )
    return FoundationPortfolioCatalogItem(
        portfolio_id=portfolio_id,
        display_name=display_name,
        base_currency=str(item.get("base_currency", "USD")),
        client_id=_optional_str(item.get("cif_id", item.get("client_id"))),
        booking_center_code=_optional_str(
            item.get("booking_center", item.get("booking_center_code"))
        ),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
