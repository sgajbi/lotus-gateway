import pytest
from fastapi import HTTPException, status

from app.routers.reporting_errors import (
    report_batch_error_response,
    report_job_error_response,
)
from app.services.reporting_error_mapping import (
    REPORT_BATCH_ERROR_RULES,
    REPORT_JOB_ERROR_RULES,
    REPORT_ORDERING_VALIDATION_ERROR_CODES,
    raise_report_batch_error,
    raise_report_job_error,
)


def test_reporting_error_rule_tables_are_explicit() -> None:
    assert [rule.fallback_code for rule in REPORT_JOB_ERROR_RULES] == [
        "missing_idempotency_key",
        "invalid_report_job_filters",
        "invalid_report_order_configuration",
        "report_job_not_found",
        "report_snapshot_not_found",
        "report_job_conflict",
    ]
    assert [rule.fallback_code for rule in REPORT_BATCH_ERROR_RULES] == [
        "invalid_batch_selector",
        "invalid_report_order_configuration",
        "report_batch_not_found",
        "report_batch_conflict",
    ]


def test_raise_report_job_error_preserves_validation_detail() -> None:
    detail = {"code": "invalid_report_job_filters", "message": "Invalid filters."}

    with pytest.raises(HTTPException) as exc:
        raise_report_job_error(status.HTTP_400_BAD_REQUEST, {"detail": detail})

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == detail


@pytest.mark.parametrize("raise_error", [raise_report_job_error, raise_report_batch_error])
@pytest.mark.parametrize("error_code", sorted(REPORT_ORDERING_VALIDATION_ERROR_CODES))
def test_reporting_errors_preserve_governed_ordering_validation_detail(
    raise_error,
    error_code: str,
) -> None:
    detail = {"code": error_code, "message": "Correct the report configuration."}

    with pytest.raises(HTTPException) as exc:
        raise_error(status.HTTP_422_UNPROCESSABLE_CONTENT, {"detail": detail})

    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert exc.value.detail == detail


@pytest.mark.parametrize("raise_error", [raise_report_job_error, raise_report_batch_error])
def test_reporting_errors_reject_unknown_ordering_validation_detail(raise_error) -> None:
    with pytest.raises(HTTPException) as exc:
        raise_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            {"detail": {"code": "raw_validation_failure", "message": "raw failure"}},
        )

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc.value.detail["message"].endswith("service is unavailable.")


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


def test_raise_report_job_error_preserves_any_conflict_with_safe_fallback_code() -> None:
    with pytest.raises(HTTPException) as exc:
        raise_report_job_error(
            status.HTTP_409_CONFLICT,
            {"detail": {"message": "Report job is already being cancelled."}},
        )

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == {
        "code": "report_job_conflict",
        "message": "Report job is already being cancelled.",
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


def test_raise_report_batch_error_maps_unknown_conflict_to_safe_gateway_error() -> None:
    with pytest.raises(HTTPException) as exc:
        raise_report_batch_error(
            status.HTTP_409_CONFLICT,
            {
                "detail": {
                    "code": "raw_scheduler_conflict",
                    "message": "internal conflict",
                    "portfolio_id": "PB_SENSITIVE",
                }
            },
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
