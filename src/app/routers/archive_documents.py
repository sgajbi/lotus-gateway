from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Path, Query, Response, status

from app.clients.archive_client import ArchiveClient
from app.config import settings
from app.contracts.archive_documents import (
    ARCHIVE_DOCUMENT_ERROR_EXAMPLES,
    ARCHIVE_DOCUMENT_EXAMPLE,
    ArchivedDocumentErrorResponse,
    ArchivedDocumentMetadataResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.archive_client_factory import build_archive_client
from app.services.caller_context import caller_context_headers

router = APIRouter(prefix="/api/v1/documents", tags=["Archived Documents"])


def _archive_client() -> ArchiveClient:
    return build_archive_client()


def _archive_error_response(
    status_code: int,
    *,
    example_key: str,
    description: str,
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ArchivedDocumentErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": ARCHIVE_DOCUMENT_ERROR_EXAMPLES[example_key],
                }
            },
        }
    }


def _archive_error_code(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        return str(code) if code else None
    detail = payload.get("detail")
    if isinstance(detail, dict):
        code = detail.get("code")
        return str(code) if code else None
    return None


def _raise_archive_error(status_code: int, payload: dict[str, Any], *, downloading: bool) -> None:
    error_code = _archive_error_code(payload)

    if status_code == status.HTTP_403_FORBIDDEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "document_access_unauthorized",
                "message": "Caller is not authorized to access this archived document.",
            },
        )
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "document_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "archived_document_not_found",
                "message": "Archived document was not found.",
            },
        )
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "document_binary_missing":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "document_download_failed",
                "message": "Archived document download is unavailable.",
            },
        )
    if status_code == status.HTTP_409_CONFLICT and error_code == "document_checksum_mismatch":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "document_download_failed",
                "message": "Archived document failed integrity verification.",
            },
        )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        fallback_code = (
            "document_download_failed" if downloading else "archive_upstream_unavailable"
        )
        fallback_message = (
            "Archived document download is unavailable."
            if downloading
            else "Archived document service is unavailable."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": fallback_code, "message": fallback_message},
        )


@router.get(
    "/{document_id}",
    response_model=ArchivedDocumentMetadataResponse,
    summary="Get archived document metadata",
    description=(
        "Return product-safe archived document metadata through the gateway boundary. Use this "
        "endpoint when Workbench or support tooling needs document identity, lifecycle summary, "
        "retention summary, and a gateway-controlled download link without exposing archive "
        "storage internals."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": ARCHIVE_DOCUMENT_EXAMPLE}},
            }
        }
    },
    responses={
        **_archive_error_response(
            400,
            example_key="missing_caller_context",
            description="Returned when required caller context is missing.",
        ),
        **_archive_error_response(
            403,
            example_key="document_access_unauthorized",
            description="Returned when the caller is not authorized for document retrieval.",
        ),
        **_archive_error_response(
            404,
            example_key="archived_document_not_found",
            description="Returned when the archived document does not exist.",
        ),
        **_archive_error_response(
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
    correlation_id = correlation_id_var.get()
    status_code, payload = await _archive_client().get_document_metadata(
        document_id=document_id,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
        current=current,
    )
    _raise_archive_error(status_code, payload, downloading=False)
    return ArchivedDocumentMetadataResponse.from_archive_payload(
        payload,
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
    )


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
        **_archive_error_response(
            400,
            example_key="missing_caller_context",
            description="Returned when required caller context is missing.",
        ),
        **_archive_error_response(
            403,
            example_key="document_access_unauthorized",
            description="Returned when the caller is not authorized for document retrieval.",
        ),
        **_archive_error_response(
            404,
            example_key="archived_document_not_found",
            description="Returned when the archived document does not exist.",
        ),
        **_archive_error_response(
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
    (
        status_code,
        content,
        response_headers,
        error_payload,
    ) = await _archive_client().download_document(
        document_id=document_id,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_archive_error(status_code, error_payload, downloading=True)

    headers = {}
    for header in (
        "content-disposition",
        "x-document-checksum-algorithm",
        "x-document-checksum",
    ):
        if value := response_headers.get(header):
            headers[header] = value

    return Response(
        content=content,
        media_type=response_headers.get("content-type", "application/octet-stream"),
        headers=headers,
    )
