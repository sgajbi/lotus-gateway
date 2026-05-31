from typing import Annotated

from fastapi import APIRouter, Header, Path, Response

from app.middleware.correlation import correlation_id_var
from app.routers.archive_documents_common import (
    archive_caller_headers,
    archive_error_response,
)
from app.services.gateway_service_provider import archive_document_service

router = APIRouter(prefix="/api/v1/documents", tags=["Archived Documents"])


@router.get(
    "/{document_id}/download",
    summary="Download archived document",
    description=(
        "Download an archived document binary through the gateway boundary. Use this endpoint "
        "only after metadata retrieval has returned a gateway-controlled download URL. The "
        "gateway preserves content type and integrity headers while keeping archive storage "
        "locations hidden."
    ),
    responses={
        200: {
            "description": "Archived document binary.",
            "content": {
                "application/pdf": {
                    "schema": {"type": "string", "format": "binary"},
                }
            },
        },
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
            example_key="document_download_failed",
            description="Returned when the archived binary is unavailable or fails validation.",
        ),
    },
)
async def download_archived_document(
    document_id: Annotated[
        str,
        Path(
            description="Stable archived document identifier.",
            examples=["doc_7d5f1f1e4d0d4d0f9b7f1a2a6b8c9d10"],
        ),
    ],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> Response:
    download = await archive_document_service().download_document(
        document_id=document_id,
        caller_headers=archive_caller_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )

    return Response(
        content=download.content,
        media_type=download.media_type,
        headers=download.headers,
    )
