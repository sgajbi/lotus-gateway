from fastapi import APIRouter, File, Form, Header, Query, UploadFile

from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.intake import EnvelopeResponse, IntakeBundleRequest, LookupResponse
from app.middleware.correlation import correlation_id_var
from app.services.intake_service import IntakeService

router = APIRouter(tags=["intake", "lookups"])


def _intake_service() -> IntakeService:
    return IntakeService(
        lotus_core_ingestion_client=LotusCoreIngestionClient(
            base_url=settings.portfolio_data_ingestion_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        lotus_core_query_client=LotusCoreQueryClient(
            base_url=settings.portfolio_data_query_base_url,
            control_plane_base_url=settings.portfolio_data_control_plane_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


@router.post(
    "/api/v1/intake/portfolio-bundle",
    response_model=EnvelopeResponse,
    summary="Ingest Portfolio Bundle via lotus-core",
    description=(
        "Submits a canonical portfolio bundle to lotus-core for asynchronous ingestion. Use this "
        "route when the caller already has a fully assembled bundle payload and wants one "
        "write-ingress handoff instead of file-based preview/commit. Accepts an optional "
        "idempotency header when callers need safe retry semantics for bundle submission."
    ),
)
async def ingest_portfolio_bundle(
    request: IntakeBundleRequest,
    idempotency_key: str | None = Header(
        default=None,
        alias="X-Idempotency-Key",
        description=(
            "Optional caller-supplied idempotency key forwarded unchanged to lotus-core so "
            "duplicate bundle submissions can replay the original ingestion job safely."
        ),
        examples=["bundle-idem-1001"],
    ),
) -> EnvelopeResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.ingest_portfolio_bundle(
        body=request.body,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/api/v1/intake/uploads/preview",
    response_model=EnvelopeResponse,
    summary="Preview lotus-core Upload",
    description=(
        "Validates a CSV upload through lotus-core without publishing records. Use this before "
        "commit to inspect normalized sample rows and row-level validation errors. Gateway "
        "accepts camelCase form aliases for UI callers and maps them to lotus-core's canonical "
        "snake_case multipart contract (`entity_type`, `file`, `sample_size`)."
    ),
)
async def preview_upload(
    entity_type: str = Form(
        ...,
        alias="entityType",
        description="Upload entity family expected in the file.",
        examples=["transactions"],
    ),
    file: UploadFile = File(
        ...,
        description="CSV file uploaded for preview validation.",
        examples=["transactions.csv"],
    ),
    sample_size: int = Form(
        20,
        alias="sampleSize",
        ge=1,
        le=100,
        description="Maximum number of normalized sample rows returned from lotus-core preview.",
        examples=[20],
    ),
) -> EnvelopeResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.preview_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        sample_size=sample_size,
        correlation_id=correlation_id,
    )


@router.post(
    "/api/v1/intake/uploads/commit",
    response_model=EnvelopeResponse,
    summary="Commit lotus-core Upload",
    description=(
        "Validates and commits a CSV upload through lotus-core. Use this only after preview "
        "results are acceptable. Gateway accepts camelCase form aliases for UI callers and maps "
        "them to lotus-core's canonical snake_case multipart contract (`entity_type`, `file`, "
        "`allow_partial`)."
    ),
)
async def commit_upload(
    entity_type: str = Form(
        ...,
        alias="entityType",
        description="Upload entity family expected in the file.",
        examples=["transactions"],
    ),
    file: UploadFile = File(
        ...,
        description="CSV file uploaded for commit after preview validation.",
        examples=["transactions.csv"],
    ),
    allow_partial: bool = Form(
        False,
        alias="allowPartial",
        description="Whether lotus-core may publish valid rows when some rows fail validation.",
        examples=[False],
    ),
) -> EnvelopeResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.commit_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        allow_partial=allow_partial,
        correlation_id=correlation_id,
    )


@router.get(
    "/api/v1/lookups/portfolios",
    response_model=LookupResponse,
    summary="Portfolio Lookup Catalog",
    description=(
        "Returns selector-only portfolio lookup options backed by lotus-core. Use this route for "
        "intake and picker population, not canonical portfolio detail or workspace composition."
    ),
)
async def get_portfolio_lookups(
    cif_id: str | None = Query(
        default=None,
        alias="cif_id",
        description=(
            "Optional CIF/client identifier filter for the portfolio selector catalog. Gateway "
            "maps this to lotus-core `client_id` when querying the canonical lookup route."
        ),
        examples=["CIF_1001"],
    ),
    booking_center: str | None = Query(
        default=None,
        alias="booking_center",
        description=(
            "Optional booking-center filter for the portfolio selector catalog. Gateway maps "
            "this to lotus-core `booking_center_code` when querying the canonical lookup route."
        ),
        examples=["SG"],
    ),
    q: str | None = Query(
        default=None,
        description="Optional search string applied to portfolio lookup labels.",
        examples=["Alpha"],
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional maximum number of portfolio lookup rows to return.",
        examples=[100],
    ),
) -> LookupResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_lookups(
        correlation_id=correlation_id,
        cif_id=cif_id,
        booking_center=booking_center,
        q=q,
        limit=limit,
    )


@router.get(
    "/api/v1/lookups/instruments",
    response_model=LookupResponse,
    summary="Instrument Lookup Catalog",
    description=(
        "Returns selector-only instrument lookup options backed by lotus-core. Use this route for "
        "intake and trade-form selector population, not canonical instrument reference detail or "
        "enrichment reads."
    ),
)
async def get_instrument_lookups(
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="Maximum number of instrument lookup rows to return.",
        examples=[200],
    ),
    product_type: str | None = Query(
        default=None,
        alias="product_type",
        description="Optional product-type filter for the instrument lookup catalog.",
        examples=["EQUITY"],
    ),
    q: str | None = Query(
        default=None,
        description="Optional search string applied to instrument lookup labels.",
        examples=["Apple"],
    ),
) -> LookupResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_instrument_lookups(
        limit=limit,
        correlation_id=correlation_id,
        product_type=product_type,
        q=q,
    )


@router.get(
    "/api/v1/lookups/currencies",
    response_model=LookupResponse,
    summary="Currency Lookup Catalog",
    description=(
        "Returns selector-only currency codes derived by lotus-core from portfolio base currencies "
        "and instrument reference data. Use `source` to scope the catalog to ALL, PORTFOLIOS, or "
        "INSTRUMENTS when the UI wants a narrower selector."
    ),
)
async def get_currency_lookups(
    instrument_page_limit: int | None = Query(
        default=None,
        alias="instrument_page_limit",
        ge=1,
        le=5000,
        description=(
            "Optional instrument catalog page size used by lotus-core while deriving "
            "currency lookups."
        ),
        examples=[500],
    ),
    source: str | None = Query(
        default=None,
        description="Optional lookup source filter such as ALL, PORTFOLIOS, or INSTRUMENTS.",
        examples=["ALL"],
    ),
    q: str | None = Query(
        default=None,
        description="Optional search string applied to currency lookup labels.",
        examples=["USD"],
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional maximum number of currency lookup rows to return.",
        examples=[50],
    ),
) -> LookupResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_currency_lookups(
        correlation_id=correlation_id,
        instrument_page_limit=instrument_page_limit,
        source=source,
        q=q,
        limit=limit,
    )
