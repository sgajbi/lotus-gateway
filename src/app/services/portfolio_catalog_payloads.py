from typing import Any

from app.contracts.portfolio import PortfolioCatalogItem
from app.services.portfolio_workspace_payloads import resolve_portfolio_display_name


def parse_catalog_items(items_payload: list[Any]) -> list[PortfolioCatalogItem]:
    items = [parse_catalog_item(item) for item in items_payload if isinstance(item, dict)]
    items.sort(key=lambda item: item.portfolio_id)
    return items


def parse_catalog_item(item: dict[str, Any]) -> PortfolioCatalogItem:
    portfolio_id = str(item.get("portfolio_id", "")).strip()
    return PortfolioCatalogItem(
        portfolio_id=portfolio_id,
        display_name=resolve_portfolio_display_name(item, fallback_portfolio_id=portfolio_id),
        base_currency=str(item.get("base_currency", "USD")),
        client_id=optional_str(item.get("client_id", item.get("cif_id"))),
        booking_center_code=optional_str(
            item.get("booking_center_code", item.get("booking_center"))
        ),
        portfolio_type=optional_str(item.get("portfolio_type")),
        status=optional_str(item.get("status")),
    )


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
