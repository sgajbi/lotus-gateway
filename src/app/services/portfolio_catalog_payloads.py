from typing import Any

from app.config import settings
from app.contracts.portfolio import PortfolioCatalogItem, PortfolioCatalogResponse
from app.services.portfolio_client_protocols import PortfolioCoreClient
from app.services.portfolio_upstream_payloads import require_payload
from app.services.portfolio_workspace_payloads import resolve_portfolio_display_name


async def load_portfolio_catalog_response(
    *,
    lotus_core_query_client: PortfolioCoreClient,
    correlation_id: str,
) -> PortfolioCatalogResponse:
    status_code, payload = await lotus_core_query_client.list_portfolios(
        correlation_id=correlation_id
    )
    items_payload = require_payload(
        result=(status_code, payload),
        unavailable_detail_prefix="lotus-core portfolio catalog unavailable",
    ).get("portfolios", [])
    return PortfolioCatalogResponse(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        items=parse_catalog_items(items_payload),
    )


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
