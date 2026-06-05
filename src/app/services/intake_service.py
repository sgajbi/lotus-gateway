from typing import Any

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.config import settings
from app.contracts.intake import EnvelopeResponse, LookupResponse
from app.services.domain_client_protocols import IntakeIngestionClient, IntakeLookupClient
from app.services.upstream_envelope import raise_product_safe_service_error


class IntakeService:
    def __init__(
        self,
        lotus_core_ingestion_client: IntakeIngestionClient,
        lotus_core_query_client: IntakeLookupClient,
    ):
        self._lotus_core_ingestion_client = lotus_core_ingestion_client
        self._lotus_core_query_client = lotus_core_query_client

    async def ingest_portfolio_bundle(
        self,
        body: dict[str, Any],
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> EnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._lotus_core_ingestion_client.ingest_portfolio_bundle(
            body=body,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, data=upstream_payload)

    async def preview_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        sample_size: int,
        correlation_id: str,
    ) -> EnvelopeResponse:
        upstream_status, upstream_payload = await self._lotus_core_ingestion_client.preview_upload(
            entity_type=entity_type,
            filename=filename,
            content=content,
            sample_size=sample_size,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, data=upstream_payload)

    async def commit_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        allow_partial: bool,
        correlation_id: str,
    ) -> EnvelopeResponse:
        upstream_status, upstream_payload = await self._lotus_core_ingestion_client.commit_upload(
            entity_type=entity_type,
            filename=filename,
            content=content,
            allow_partial=allow_partial,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id=correlation_id, data=upstream_payload)

    async def get_portfolio_lookups(
        self,
        correlation_id: str,
        *,
        cif_id: str | None = None,
        booking_center: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> LookupResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._lotus_core_query_client.get_portfolio_lookups(
            correlation_id=correlation_id,
            cif_id=cif_id,
            booking_center=booking_center,
            q=q,
            limit=limit,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._lookup_response(
            correlation_id=correlation_id, upstream_payload=upstream_payload
        )

    async def get_instrument_lookups(
        self,
        limit: int,
        correlation_id: str,
        *,
        product_type: str | None = None,
        q: str | None = None,
    ) -> LookupResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._lotus_core_query_client.get_instrument_lookups(
            limit=limit,
            correlation_id=correlation_id,
            product_type=product_type,
            q=q,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._lookup_response(
            correlation_id=correlation_id, upstream_payload=upstream_payload
        )

    async def get_currency_lookups(
        self,
        correlation_id: str,
        *,
        instrument_page_limit: int | None = None,
        source: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> LookupResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._lotus_core_query_client.get_currency_lookups(
            correlation_id=correlation_id,
            instrument_page_limit=instrument_page_limit,
            source=source,
            q=q,
            limit=limit,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._lookup_response(
            correlation_id=correlation_id, upstream_payload=upstream_payload
        )

    def _envelope(self, correlation_id: str, data: dict[str, Any]) -> EnvelopeResponse:
        return EnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=data,
        )

    def _lookup_response(
        self, correlation_id: str, upstream_payload: dict[str, Any]
    ) -> LookupResponse:
        try:
            return LookupResponse(
                correlation_id=correlation_id,
                contract_version=settings.contract_version,
                items=upstream_payload.get("items", []),
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid lotus-core lookup contract payload: {exc}",
            ) from exc

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise_product_safe_service_error(
            upstream_status,
            upstream_payload,
            source_service="lotus-core",
            error_code="LOTUS_CORE_INTAKE_UPSTREAM_ERROR",
            default_detail="lotus-core intake request failed.",
        )
