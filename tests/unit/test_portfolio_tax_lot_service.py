from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.services.portfolio_tax_lot_service import (
    PortfolioTaxLotServiceMixin,
    _build_portfolio_tax_lot_response,
)


def _lot_payload(**overrides):
    lot = {
        "lot_id": "LOT-001",
        "source_transaction_id": "TXN-001",
        "portfolio_id": "PF_1001",
        "instrument_id": "AAPL",
        "security_id": "SEC_AAPL",
        "acquisition_date": "2026-02-28",
        "original_quantity": 100.0,
        "open_quantity": 75.0,
        "lot_cost_local": "15005.5000000000",
        "lot_cost_base": "15005.5000000000",
        "accrued_interest_paid_local": "0",
        "economic_event_id": "EVT-001",
        "linked_transaction_group_id": "LTG-001",
        "calculation_policy_id": "BUY_DEFAULT_POLICY",
        "calculation_policy_version": "1.0.0",
        "source_system": "OMS_PRIMARY",
    }
    lot.update(overrides)
    return lot


def test_tax_lot_builder_preserves_source_fields_and_ignores_future_source_fields():
    response = _build_portfolio_tax_lot_response(
        correlation_id="corr-lots",
        contract_version="v1",
        portfolio_id="PF_1001",
        security_id="SEC_AAPL",
        payload={
            "portfolio_id": "PF_1001",
            "security_id": "SEC_AAPL",
            "lots": [_lot_payload(future_source_field="ignored")],
        },
    )

    lot = response.lots[0]
    assert lot.acquisition_date == date(2026, 2, 28)
    assert lot.original_quantity == Decimal("100")
    assert lot.open_quantity == Decimal("75")
    assert lot.lot_cost_base == Decimal("15005.5000000000")
    assert lot.source_transaction_id == "TXN-001"
    assert response.correlation_id == "corr-lots"


def test_tax_lot_builder_rejects_cross_portfolio_source_identity():
    with pytest.raises(ValueError, match="identity"):
        _build_portfolio_tax_lot_response(
            correlation_id="corr-lots",
            contract_version="v1",
            portfolio_id="PF_1001",
            security_id="SEC_AAPL",
            payload={
                "portfolio_id": "PF_1001",
                "security_id": "SEC_AAPL",
                "lots": [_lot_payload(portfolio_id="PF_OTHER")],
            },
        )


def test_tax_lot_builder_rejects_missing_envelope_identity():
    with pytest.raises(ValueError, match="identity"):
        _build_portfolio_tax_lot_response(
            correlation_id="corr-lots",
            contract_version="v1",
            portfolio_id="PF_1001",
            security_id="SEC_AAPL",
            payload={"lots": [_lot_payload()]},
        )


def test_tax_lot_builder_rejects_missing_lot_identity_instead_of_stamping_request_ids():
    lot = _lot_payload()
    lot.pop("portfolio_id")
    with pytest.raises(ValueError, match="portfolio_id"):
        _build_portfolio_tax_lot_response(
            correlation_id="corr-lots",
            contract_version="v1",
            portfolio_id="PF_1001",
            security_id="SEC_AAPL",
            payload={
                "portfolio_id": "PF_1001",
                "security_id": "SEC_AAPL",
                "lots": [lot],
            },
        )


class _StubTaxLotService(PortfolioTaxLotServiceMixin):
    def __init__(self, result):
        self.result = result

    async def _get_portfolio_position_lots_result(self, **kwargs):
        self.kwargs = kwargs
        return self.result


@pytest.mark.asyncio
async def test_tax_lot_service_maps_source_not_found_without_turning_it_into_success():
    service = _StubTaxLotService((404, {"detail": "BUY state not found"}))

    with pytest.raises(HTTPException) as error:
        await service.get_portfolio_tax_lots(
            portfolio_id="PF_1001",
            security_id="SEC_AAPL",
            correlation_id="corr-lots",
        )

    assert error.value.status_code == 404
    assert service.kwargs == {
        "portfolio_id": "PF_1001",
        "security_id": "SEC_AAPL",
        "correlation_id": "corr-lots",
    }
