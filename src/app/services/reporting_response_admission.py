"""Admission of reporting source responses.

A successful lotus-report response is published only when it is well-formed
for the requested operation and answers that operation's own identity. Each
consumer states just the identities its source contract actually exposes; a
well-shaped response for a different job, snapshot or submission key is
refused as a bounded upstream-contract failure instead of being published,
and a malformed success becomes the declared 502 rather than an internal
validation error. Scope fencing for the search operation stays with
``reporting_search_scope``.
"""

from typing import Any, NoReturn, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.services.reporting_error_mapping import raise_report_job_error

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


def admit_report_source_response(
    model_type: type[ResponseModel],
    status_code: int,
    payload: dict[str, Any],
) -> ResponseModel:
    raise_report_job_error(status_code, payload)
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        _raise_source_contract_invalid(exc)


def assert_report_response_identity(
    *,
    operation: str,
    expected: dict[str, str],
    actual: dict[str, str],
) -> None:
    mismatched = sorted(name for name in expected if actual.get(name) != expected[name])
    if mismatched:
        _raise_source_identity_mismatch(operation=operation, mismatched_fields=mismatched)


def _raise_source_contract_invalid(exc: ValidationError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "code": "report_job_source_contract_invalid",
            "message": (
                "lotus-report returned a successful response that does not match "
                "the governed reporting contract."
            ),
        },
    ) from exc


def _raise_source_identity_mismatch(*, operation: str, mismatched_fields: list[str]) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "code": "report_job_source_identity_mismatch",
            "message": (
                f"lotus-report answered {operation} with evidence for a different "
                "identity: " + ", ".join(mismatched_fields)
            ),
        },
    )
