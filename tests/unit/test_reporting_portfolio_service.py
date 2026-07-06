import pytest
from fastapi import HTTPException

from app.contracts.reporting import ReportingPortfolioRequest
from app.services.reporting_portfolio_service import ReportingPortfolioService


class _ReportingClient:
    def __init__(self) -> None:
        self.snapshot_response: tuple[int, dict[str, object]] = (
            200,
            {
                "generatedAt": "2026-02-24T07:00:00Z",
                "rows": [{"bucket": "TOTAL", "metric": "market_value_base", "value": 1.0}],
            },
        )
        self.summary_response: tuple[int, dict[str, object]] = (
            200,
            {"scope": {"portfolio_id": "P1"}, "wealth": {"total_market_value": 123.0}},
        )
        self.review_response: tuple[int, dict[str, object]] = (
            200,
            {"overview": {"total_market_value": 1000.0}},
        )
        self.calls: list[dict[str, object]] = []

    async def get_portfolio_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "snapshot",
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date,
                "correlation_id": correlation_id,
            }
        )
        return self.snapshot_response

    async def post_portfolio_summary(
        self,
        portfolio_id: str,
        payload: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "summary",
                "portfolio_id": portfolio_id,
                "payload": payload,
                "correlation_id": correlation_id,
            }
        )
        return self.summary_response

    async def post_portfolio_review(
        self,
        portfolio_id: str,
        payload: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "review",
                "portfolio_id": portfolio_id,
                "payload": payload,
                "correlation_id": correlation_id,
            }
        )
        return self.review_response


@pytest.mark.asyncio
async def test_reporting_portfolio_service_returns_snapshot_envelope() -> None:
    reporting_client = _ReportingClient()
    service = ReportingPortfolioService(
        reporting_client=reporting_client,
        contract_version="contract-test",
    )

    response = await service.get_snapshot(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        correlation_id="corr-reporting",
    )

    assert response.portfolio_id == "P1"
    assert response.source_service == "lotus-report"
    assert response.contract_version == "contract-test"
    assert response.generated_at.isoformat().startswith("2026-02-24T07:00:00")
    assert response.rows == [{"bucket": "TOTAL", "metric": "market_value_base", "value": 1.0}]
    assert reporting_client.calls == [
        {
            "operation": "snapshot",
            "portfolio_id": "P1",
            "as_of_date": "2026-02-24",
            "correlation_id": "corr-reporting",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_portfolio_service_falls_back_when_generated_at_is_invalid() -> None:
    reporting_client = _ReportingClient()
    reporting_client.snapshot_response = (
        200,
        {"generatedAt": "invalid", "rows": []},
    )
    service = ReportingPortfolioService(
        reporting_client=reporting_client,
        contract_version="contract-test",
    )

    response = await service.get_snapshot(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        correlation_id="corr-reporting",
    )

    assert response.generated_at is not None


@pytest.mark.asyncio
async def test_reporting_portfolio_service_forwards_summary_payload() -> None:
    reporting_client = _ReportingClient()
    service = ReportingPortfolioService(
        reporting_client=reporting_client,
        contract_version="contract-test",
    )
    request = ReportingPortfolioRequest.model_validate(
        {
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": ["WEALTH"],
            "allocationDimensions": ["asset_class"],
        }
    )

    response = await service.get_summary(
        portfolio_id="P1",
        request=request,
        correlation_id="corr-summary",
    )

    assert response.as_of_date == "2026-02-24"
    assert response.contract_version == "contract-test"
    assert response.data["wealth"]["total_market_value"] == 123.0
    assert reporting_client.calls == [
        {
            "operation": "summary",
            "portfolio_id": "P1",
            "payload": {
                "as_of_date": "2026-02-24",
                "reporting_currency": "USD",
                "sections": ["WEALTH"],
                "allocation_dimensions": ["asset_class"],
            },
            "correlation_id": "corr-summary",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_portfolio_service_forwards_review_payload() -> None:
    reporting_client = _ReportingClient()
    service = ReportingPortfolioService(
        reporting_client=reporting_client,
        contract_version="contract-test",
    )
    request = ReportingPortfolioRequest.model_validate(
        {
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": ["OVERVIEW"],
            "lookThroughMode": "full",
        }
    )

    response = await service.get_review(
        portfolio_id="P1",
        request=request,
        correlation_id="corr-review",
    )

    assert response.as_of_date == "2026-02-24"
    assert response.contract_version == "contract-test"
    assert response.data["overview"]["total_market_value"] == 1000.0
    assert reporting_client.calls == [
        {
            "operation": "review",
            "portfolio_id": "P1",
            "payload": {
                "as_of_date": "2026-02-24",
                "reporting_currency": "USD",
                "sections": ["OVERVIEW"],
                "look_through_mode": "full",
            },
            "correlation_id": "corr-review",
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("snapshot", "Reporting snapshot unavailable"),
        ("summary", "Reporting summary unavailable"),
        ("review", "Reporting review unavailable"),
    ],
)
async def test_reporting_portfolio_service_maps_upstream_errors(
    operation: str,
    message: str,
) -> None:
    reporting_client = _ReportingClient()
    reporting_client.snapshot_response = (
        503,
        {
            "detail": "snapshot unavailable",
            "client_name": "Private Client",
            "token": "secret-token",
        },
    )
    reporting_client.summary_response = (
        503,
        {
            "detail": {
                "code": "SUMMARY_UNAVAILABLE",
                "message": "summary unavailable",
                "debug_payload": {
                    "client_name": "Private Client",
                    "token": "secret-token",
                },
            }
        },
    )
    reporting_client.review_response = (
        503,
        {
            "message": "review unavailable",
            "client_name": "Private Client",
            "token": "secret-token",
        },
    )
    service = ReportingPortfolioService(
        reporting_client=reporting_client,
        contract_version="contract-test",
    )
    request = ReportingPortfolioRequest.model_validate({"asOfDate": "2026-02-24"})

    with pytest.raises(HTTPException) as exc_info:
        if operation == "snapshot":
            await service.get_snapshot(
                portfolio_id="P1",
                as_of_date="2026-02-24",
                correlation_id="corr-error",
            )
        elif operation == "summary":
            await service.get_summary(
                portfolio_id="P1",
                request=request,
                correlation_id="corr-error",
            )
        else:
            await service.get_review(
                portfolio_id="P1",
                request=request,
                correlation_id="corr-error",
            )

    assert exc_info.value.status_code == 502
    assert str(exc_info.value.detail).startswith(message)
    assert "Private Client" not in str(exc_info.value.detail)
    assert "secret-token" not in str(exc_info.value.detail)
    if operation == "summary":
        assert str(exc_info.value.detail).endswith("SUMMARY_UNAVAILABLE")
