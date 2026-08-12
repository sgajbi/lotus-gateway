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
    additional_example_keys: tuple[str, ...] = (),
    description: str,
) -> dict[int | str, dict[str, Any]]:
    content: dict[str, Any]
    if additional_example_keys:
        keys = (example_key, *additional_example_keys)
        content = {
            "examples": {
                key: {
                    "summary": key.replace("_", " ").title(),
                    "value": REPORT_BATCH_ERROR_EXAMPLES[key],
                }
                for key in keys
            }
        }
    else:
        content = {"example": REPORT_BATCH_ERROR_EXAMPLES[example_key]}
    return {
        status_code: {
            "model": ReportJobErrorResponse,
            "description": description,
            "content": {"application/json": content},
        }
    }
