from typing import Any

from fastapi import status

from app.middleware.correlation import correlation_id_var

BANK_DEMO_PROOF_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "description": (
            "lotus-advise rejected proof capture because material evidence does not match the "
            "canonical RFC-0028 scenario."
        )
    },
    422: {"description": "lotus-advise rejected the proof contract request shape."},
}


def bank_demo_correlation_id(x_correlation_id: str | None) -> str:
    return x_correlation_id or correlation_id_var.get() or ""
