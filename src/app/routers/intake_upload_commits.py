from fastapi import APIRouter, File, Form, UploadFile

from app.contracts.intake import EnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.trusted_caller_context import IntakeWriteCallerContext
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/intake/uploads", tags=["intake"])


async def _commit_upload(
    *,
    entity_type: str,
    file: UploadFile,
    allow_partial: bool,
    caller_headers: dict[str, str],
) -> EnvelopeResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.commit_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        allow_partial=allow_partial,
        correlation_id=correlation_id,
        caller_headers=caller_headers,
    )


@router.post(
    "/commit",
    response_model=EnvelopeResponse,
    summary="Commit lotus-core Upload",
    description=(
        "Validates and commits a CSV upload through lotus-core. Use this only after preview "
        "results are acceptable. Gateway accepts camelCase form aliases for UI callers and maps "
        "them to lotus-core's canonical snake_case multipart contract (`entity_type`, `file`, "
        "`allow_partial`). Requires the trusted caller context headers (X-Actor-Id, "
        "X-Tenant-Id, X-Region); the admitted tenant scopes the lotus-core write, which "
        "Core's fail-closed tenant ingress would otherwise refuse."
    ),
)
async def commit_upload(
    caller_headers: IntakeWriteCallerContext,
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
        caller_headers=caller_headers,
    )
