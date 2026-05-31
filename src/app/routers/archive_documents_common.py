from typing import Any

from app.contracts.archive_documents import (
    ARCHIVE_DOCUMENT_ERROR_EXAMPLES,
    ArchivedDocumentErrorResponse,
)
from app.services.caller_context import caller_context_headers


def archive_error_response(
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


def archive_caller_headers(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    return caller_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
