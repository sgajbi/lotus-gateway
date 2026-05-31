from fastapi import APIRouter, File, Form, UploadFile

from app.contracts.intake import EnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/intake/uploads", tags=["intake"])


async def _commit_upload(
    *,
    entity_type: str,
    file: UploadFile,
    allow_partial: bool,
) -> EnvelopeResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.commit_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        allow_partial=allow_partial,
        correlation_id=correlation_id,
    )


@router.post(
    "/commit",
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
    return await _commit_upload(
        entity_type=entity_type,
        file=file,
        allow_partial=allow_partial,
    )
