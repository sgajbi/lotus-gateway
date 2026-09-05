from fastapi import APIRouter, File, Form, UploadFile

from app.contracts.intake import EnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.trusted_caller_context import TrustedCallerContext
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/intake/uploads", tags=["intake"])


async def _preview_upload(
    *,
    entity_type: str,
    file: UploadFile,
    sample_size: int,
    caller_headers: dict[str, str],
) -> EnvelopeResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.preview_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        sample_size=sample_size,
        correlation_id=correlation_id,
        caller_headers=caller_headers,
    )


@router.post(
    "/preview",
    response_model=EnvelopeResponse,
    summary="Preview lotus-core Upload",
    description=(
        "Validates a CSV upload through lotus-core without publishing records. Use this before "
        "commit to inspect normalized sample rows and row-level validation errors. Gateway "
        "accepts camelCase form aliases for UI callers and maps them to lotus-core's canonical "
        "snake_case multipart contract (`entity_type`, `file`, `sample_size`). Requires the "
        "trusted caller context headers (X-Actor-Id, X-Tenant-Id, X-Region); the admitted "
        "tenant scopes the lotus-core write, which Core's fail-closed tenant ingress would "
        "otherwise refuse."
    ),
)
async def preview_upload(
    caller_headers: TrustedCallerContext,
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
    return await _preview_upload(
        entity_type=entity_type,
        file=file,
        sample_size=sample_size,
        caller_headers=caller_headers,
    )
