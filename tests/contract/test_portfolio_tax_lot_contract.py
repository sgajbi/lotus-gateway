from app.main import app


def test_portfolio_tax_lot_route_has_closed_typed_openapi_contract():
    spec = app.openapi()
    path = "/api/v1/portfolio/portfolios/{portfolio_id}/positions/{security_id}/lots"
    operation = spec["paths"][path]["get"]
    schema = spec["components"]["schemas"]["PortfolioTaxLotResponse"]
    lot_schema = spec["components"]["schemas"]["PortfolioTaxLot"]

    assert operation["summary"] == "Get portfolio position tax lots"
    assert operation["operationId"]
    assert schema["additionalProperties"] is False
    assert lot_schema["additionalProperties"] is False
    assert schema["example"]["lots"][0]["lot_id"] == "LOT-TXN-2026-0001"
    assert set(lot_schema["required"]) >= {
        "lot_id",
        "source_transaction_id",
        "portfolio_id",
        "security_id",
        "acquisition_date",
        "lot_cost_local",
        "lot_cost_base",
    }


def test_portfolio_tax_lot_openapi_does_not_claim_deferred_valuation_semantics():
    spec = app.openapi()
    lot_description = spec["components"]["schemas"]["PortfolioTaxLotResponse"]["properties"][
        "lots"
    ]["description"]

    assert "does not calculate holding period" in lot_description
    assert "reporting-currency values" in lot_description
