from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.contracts.reporting import (
    ReportingPortfolioRequest,
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
)
from app.services.reporting_client_protocols import ReportingPortfolioClient


class ReportingPortfolioService:
    def __init__(
        self,
        *,
        reporting_client: ReportingPortfolioClient,
        contract_version: str,
    ) -> None:
        self._reporting_client = reporting_client
        self._contract_version = contract_version

    async def get_snapshot(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> ReportingSnapshotResponse:
        status_code, payload = await self._reporting_client.get_portfolio_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        self._raise_reporting_error(
            status_code=status_code,
            payload=payload,
            unavailable_message="Reporting snapshot unavailable",
        )

        return ReportingSnapshotResponse(
            correlationId=correlation_id,
            contractVersion=self._contract_version,
            sourceService="lotus-report",
            portfolioId=portfolio_id,
            asOfDate=as_of_date,
            generatedAt=self._generated_at(payload),
            rows=payload.get("rows", []),
        )

    async def get_summary(
        self,
        *,
        portfolio_id: str,
        request: ReportingPortfolioRequest,
        correlation_id: str,
    ) -> ReportingSummaryResponse:
        status_code, payload = await self._reporting_client.post_portfolio_summary(
            portfolio_id=portfolio_id,
            payload=request.to_upstream_payload(),
            correlation_id=correlation_id,
        )
        self._raise_reporting_error(
            status_code=status_code,
            payload=payload,
            unavailable_message="Reporting summary unavailable",
        )
        return ReportingSummaryResponse(
            correlationId=correlation_id,
            contractVersion=self._contract_version,
            sourceService="lotus-report",
            portfolioId=portfolio_id,
            asOfDate=request.as_of_date,
            data=payload,
        )

    async def get_review(
        self,
        *,
        portfolio_id: str,
        request: ReportingPortfolioRequest,
        correlation_id: str,
    ) -> ReportingReviewResponse:
        status_code, payload = await self._reporting_client.post_portfolio_review(
            portfolio_id=portfolio_id,
            payload=request.to_upstream_payload(),
            correlation_id=correlation_id,
        )
        self._raise_reporting_error(
            status_code=status_code,
            payload=payload,
            unavailable_message="Reporting review unavailable",
        )
        return ReportingReviewResponse(
            correlationId=correlation_id,
            contractVersion=self._contract_version,
            sourceService="lotus-report",
            portfolioId=portfolio_id,
            asOfDate=request.as_of_date,
            data=payload,
        )

    def _generated_at(self, payload: dict[str, Any]) -> datetime:
        generated_at_raw = payload.get("generatedAt")
        if isinstance(generated_at_raw, str):
            try:
                return datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now(UTC)

    def _raise_reporting_error(
        self,
        *,
        status_code: int,
        payload: dict[str, Any],
        unavailable_message: str,
    ) -> None:
        if status_code < status.HTTP_400_BAD_REQUEST:
            return
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{unavailable_message}: {payload}",
        )
