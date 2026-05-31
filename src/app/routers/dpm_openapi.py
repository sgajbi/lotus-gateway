"""OpenAPI helpers for DPM Gateway route families."""

from typing import Any


def manage_upstream_error_responses(
    *,
    error_model: type[Any],
    conflict_description: str,
    invalid_payload_description: str,
    unavailable_description: str,
    not_found_description: str | None = None,
) -> dict[int | str, dict[str, Any]]:
    responses: dict[int | str, dict[str, Any]] = {}
    if not_found_description is not None:
        responses[404] = {
            "model": error_model,
            "description": not_found_description,
        }
    responses[409] = {
        "model": error_model,
        "description": conflict_description,
    }
    responses[422] = {
        "model": error_model,
        "description": invalid_payload_description,
    }
    responses[503] = {
        "model": error_model,
        "description": unavailable_description,
    }
    return responses
