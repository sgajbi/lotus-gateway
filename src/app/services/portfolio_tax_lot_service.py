from typing import Any, Protocol, cast

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.config import settings
from app.contracts.portfolio_tax_lots import PortfolioTaxLot, PortfolioTaxLotResponse
from app.services.portfolio_upstream_payloads import raise_on_upstream_client_error, require_payload


class _PortfolioTaxLotUpstream(Protocol):
    async def _get_portfolio_position_lots_result(
        self,
        *,
        portfolio_id: str,
        security_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PortfolioTaxLotServiceMixin:
    async def get_portfolio_tax_lots(
        self,
        *,
        portfolio_id: str,
        security_id: str,
        correlation_id: str,
    ) -> PortfolioTaxLotResponse:
        upstream = cast(_PortfolioTaxLotUpstream, self)
        result = await upstream._get_portfolio_position_lots_result(
            portfolio_id=portfolio_id,
            security_id=security_id,
            correlation_id=correlation_id,
        )
        raise_on_upstream_client_error(
            result,
            detail_prefix="lotus-core portfolio tax-lot lookup rejected the request",
        )
        payload = require_payload(
            result,
            unavailable_detail_prefix="lotus-core portfolio tax-lot lookup unavailable",
        )
        try:
            return _build_portfolio_tax_lot_response(
                correlation_id=correlation_id,
                contract_version=settings.contract_version,
                portfolio_id=portfolio_id,
                security_id=security_id,
                payload=payload,
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="lotus-core portfolio tax-lot lookup returned an invalid payload",
            ) from exc


def _build_portfolio_tax_lot_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    security_id: str,
    payload: dict[str, Any],
) -> PortfolioTaxLotResponse:
    source_portfolio_id = payload.get("portfolio_id")
    if source_portfolio_id is not None and source_portfolio_id != portfolio_id:
        raise ValueError("source portfolio identity does not match the requested portfolio")
    source_security_id = payload.get("security_id")
    if source_security_id is not None and source_security_id != security_id:
        raise ValueError("source security identity does not match the requested security")

    raw_lots = payload.get("lots")
    if not isinstance(raw_lots, list):
        raise ValueError("source lots must be a list")

    lots = []
    for raw_lot in raw_lots:
        if not isinstance(raw_lot, dict):
            raise ValueError("source lot records must be objects")
        lot = {
            **raw_lot,
            "portfolio_id": raw_lot.get("portfolio_id", portfolio_id),
            "security_id": raw_lot.get("security_id", security_id),
        }
        parsed_lot = _validate_lot_identity(lot, portfolio_id=portfolio_id, security_id=security_id)
        lots.append(parsed_lot)

    return PortfolioTaxLotResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        security_id=security_id,
        lots=lots,
    )


def _validate_lot_identity(raw_lot: dict[str, Any], *, portfolio_id: str, security_id: str):
    projected_lot = {
        field_name: raw_lot[field_name]
        for field_name in PortfolioTaxLot.model_fields
        if field_name in raw_lot
    }
    lot = PortfolioTaxLot.model_validate(projected_lot)
    if lot.portfolio_id != portfolio_id or lot.security_id != security_id:
        raise ValueError("source lot identity does not match the requested portfolio/security")
    return lot
