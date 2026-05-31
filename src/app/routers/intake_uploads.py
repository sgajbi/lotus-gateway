from fastapi import APIRouter, File, Form, UploadFile

from app.contracts.intake import EnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/intake/uploads", tags=["intake"])


@router.post(
    "/preview",
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
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.preview_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        sample_size=sample_size,
        correlation_id=correlation_id,
    )
