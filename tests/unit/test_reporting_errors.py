import pytest
from fastapi import HTTPException, status

from app.routers.reporting_errors import (
    raise_report_batch_error,
    raise_report_job_error,
    report_batch_error_response,
    report_job_error_response,
)


def test_raise_report_job_error_preserves_validation_detail() -> None:
    detail = {"code": "invalid_report_job_filters", "message": "Invalid filters."}

    with pytest.raises(HTTPException) as exc:
        raise_report_job_error(status.HTTP_400_BAD_REQUEST, {"detail": detail})

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == detail


def test_raise_report_job_error_maps_unknown_upstream_error_to_safe_gateway_error() -> None:
    with pytest.raises(HTTPException) as exc:
        raise_report_job_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"detail": {"code": "raw_source_failure", "message": "raw failure"}},
        )

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc.value.detail == {
        "code": "report_job_upstream_unavailable",
        "message": "Report job service is unavailable.",
    }


def test_raise_report_batch_error_preserves_report_batch_not_found() -> None:
    with pytest.raises(HTTPException) as exc:
        raise_report_batch_error(
            status.HTTP_404_NOT_FOUND,
            {"detail": {"code": "report_batch_not_found", "message": "Missing batch."}},
        )

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == {
        "code": "report_batch_not_found",
        "message": "Missing batch.",
    }


def test_raise_report_batch_error_maps_unknown_upstream_error_to_safe_gateway_error() -> None:
    with pytest.raises(HTTPException) as exc:
        raise_report_batch_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"detail": {"code": "raw_batch_failure", "message": "raw failure"}},
        )

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc.value.detail == {
        "code": "report_batch_upstream_unavailable",
        "message": "Report batch service is unavailable.",
    }


def test_raise_report_batch_error_preserves_scheduler_run_conflict() -> None:
    with pytest.raises(HTTPException) as exc:
        raise_report_batch_error(
            status.HTTP_409_CONFLICT,
            {
                "detail": {
                    "code": "batch_scheduler_run_failed",
                    "message": "Scheduler pass could not materialize configured schedules.",
                }
            },
        )

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == {
        "code": "batch_scheduler_run_failed",
        "message": "Scheduler pass could not materialize configured schedules.",
    }


def test_report_job_error_response_uses_governed_example() -> None:
    response = report_job_error_response(
        status.HTTP_404_NOT_FOUND,
        example_key="report_job_not_found",
        description="Missing job.",
    )

    assert response[status.HTTP_404_NOT_FOUND]["description"] == "Missing job."
    assert (
        response[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["example"]["detail"][
            "code"
        ]
        == "report_job_not_found"
    )


def test_report_batch_error_response_uses_governed_example() -> None:
    response = report_batch_error_response(
        status.HTTP_409_CONFLICT,
        example_key="idempotency_conflict",
        description="Conflicting batch.",
    )

    assert response[status.HTTP_409_CONFLICT]["description"] == "Conflicting batch."
    assert (
        response[status.HTTP_409_CONFLICT]["content"]["application/json"]["example"]["detail"][
            "code"
        ]
        == "idempotency_conflict"
    )
