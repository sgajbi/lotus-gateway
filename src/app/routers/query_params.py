"""Router helpers for preserving product query parameter semantics."""

from typing import Any

from starlette.datastructures import QueryParams


def query_params_with_repeated_values(query_params: QueryParams) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, value in query_params.multi_items():
        existing = params.get(key)
        if existing is None:
            params[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            params[key] = [existing, value]
    return params
