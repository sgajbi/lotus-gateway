from typing import Any

from app.contracts.reporting import ReportJobErrorResponse
from app.contracts.reporting_errors import (
    REPORT_BATCH_ERROR_EXAMPLES,
    REPORT_JOB_ERROR_EXAMPLES,
)


def report_job_error_response(
    status_code: int,
    *,
    example_key: str,
    description: str,
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ReportJobErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": REPORT_JOB_ERROR_EXAMPLES[example_key],
                }
            },
        }
    }


def report_batch_error_response(
    status_code: int,
    *,
    example_key: str,
    description: str,
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ReportJobErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": REPORT_BATCH_ERROR_EXAMPLES[example_key],
                }
            },
        }
    }
