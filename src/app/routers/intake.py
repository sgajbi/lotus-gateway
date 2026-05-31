from fastapi import APIRouter, Header

from app.contracts.intake import EnvelopeResponse, IntakeBundleRequest
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])


async def _ingest_portfolio_bundle(
    *,
    request: IntakeBundleRequest,
    idempotency_key: str | None,
) -> EnvelopeResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.ingest_portfolio_bundle(
        body=request.body,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/portfolio-bundle",
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
    return await _ingest_portfolio_bundle(
        request=request,
        idempotency_key=idempotency_key,
    )
