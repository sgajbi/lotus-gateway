from typing import Any, Protocol


class ArchiveDocumentClient(Protocol):
    async def get_document_metadata(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        current: bool = False,
    ) -> tuple[int, dict[str, Any]]: ...

    async def download_document(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, bytes, dict[str, str], dict[str, Any]]: ...


class CompositePerformanceClient(Protocol):
    async def post_composite_twr(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_composite_inspection(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class SourceProductExecutionClient(Protocol):
    async def get_external_order_execution_acknowledgement(
        self,
        *,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class IntakeIngestionClient(Protocol):
    async def ingest_portfolio_bundle(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_upload(
        self,
        *,
        entity_type: str,
        filename: str,
        content: bytes,
        sample_size: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def commit_upload(
        self,
        *,
        entity_type: str,
        filename: str,
        content: bytes,
        allow_partial: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class IntakeLookupClient(Protocol):
    async def get_portfolio_lookups(
        self,
        *,
        correlation_id: str,
        cif_id: str | None = None,
        booking_center: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_instrument_lookups(
        self,
        *,
        limit: int,
        correlation_id: str,
        product_type: str | None = None,
        q: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_currency_lookups(
        self,
        *,
        correlation_id: str,
        instrument_page_limit: int | None = None,
        source: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> tuple[int, dict[str, Any]]: ...


class RiskWorkspaceClient(Protocol):
    async def post_risk_calculate(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_concentration(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_drawdown(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_rolling_metrics(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_historical_attribution(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

