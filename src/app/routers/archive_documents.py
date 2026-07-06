from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from app.contracts.archive_documents import (
    ARCHIVE_DOCUMENT_EXAMPLE,
    ArchivedDocumentMetadataResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.archive_documents_common import (
    ArchiveDocumentCallerHeaders,
    archive_error_response,
)
from app.services.gateway_service_provider import archive_document_service

router = APIRouter(prefix="/api/v1/documents", tags=["Archived Documents"])


async def _get_archived_document_metadata(
    *,
    document_id: str,
    current: bool,
    caller_headers: ArchiveDocumentCallerHeaders,
) -> ArchivedDocumentMetadataResponse:
    correlation_id = correlation_id_var.get()
    return await archive_document_service().get_document_metadata(
        document_id=document_id,
        caller_headers=caller_headers.as_archive_context(),
        correlation_id=correlation_id,
        current=current,
    )


@router.get(
    "/{document_id}",
    response_model=ArchivedDocumentMetadataResponse,
    summary="Get archived document metadata",
    description=(
        "Return product-safe archived document metadata through the gateway boundary. Use this "
        "endpoint when Workbench or support tooling needs document identity, lifecycle summary, "
        "retention summary, and a gateway-controlled download link without exposing archive "
        "storage internals. Gateway requires caller context and enforces tenant and region parity "
        "against archive metadata before returning the document contract; broader portfolio, "
        "client, or advisor entitlement remains owned by upstream authorization."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": ARCHIVE_DOCUMENT_EXAMPLE}},
            }
        }
    },
    responses={
        **archive_error_response(
            400,
            example_key="missing_caller_context",
            description="Returned when required caller context is missing.",
        ),
        **archive_error_response(
            403,
            example_key="document_access_unauthorized",
            description="Returned when the caller is not authorized for document retrieval.",
        ),
        **archive_error_response(
            404,
            example_key="archived_document_not_found",
            description="Returned when the archived document does not exist.",
        ),
        **archive_error_response(
            502,
            example_key="archive_upstream_unavailable",
            description="Returned when lotus-archive is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_archived_document_metadata(
    document_id: Annotated[
        str,
        Path(
            description="Stable archived document identifier.",
            examples=["doc_7d5f1f1e4d0d4d0f9b7f1a2a6b8c9d10"],
        ),
    ],
    current: Annotated[
        bool,
        Query(
            description=(
                "When true, resolve the current document after supersession, correction, or "
                "reissue history."
            ),
            examples=[False],
        ),
    ] = False,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ArchivedDocumentMetadataResponse:
    return await _get_archived_document_metadata(
        document_id=document_id,
        current=current,
        caller_headers=ArchiveDocumentCallerHeaders(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
    )
