"""Workbench-facing trusted caller-context admission.

Routes that forward caller authority use the request-aware dependency so repeated
wire headers cannot be collapsed into an ambiguous identity by the framework.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.routers.trusted_caller_context import (
    TrustedCallerContext as WorkbenchCallerContext,
)
from app.routers.trusted_caller_context import (
    require_trusted_caller_context as require_workbench_caller_context,
)
from app.routers.trusted_caller_context import (
    trusted_caller_context_dependency as workbench_caller_context_dependency,
)

WORKBENCH_CALLER_OPENAPI = {
    "parameters": [
        {
            "name": name,
            "in": "header",
            "required": name in {"X-Actor-Id", "X-Tenant-Id", "X-Region"},
            "description": "Admitted trusted caller context; not a production IAM grant.",
            "schema": {"type": "string", "minLength": 1, "pattern": r".*\S.*"},
        }
        for name in (
            "X-Actor-Id",
            "X-Tenant-Id",
            "X-Region",
            "X-Caller-Application",
            "X-Booking-Center-Code",
            "X-Role",
        )
    ]
}


def require_unambiguous_workbench_caller_context(request: Request) -> dict[str, str]:
    """Admit one caller identity and reject repeated authority headers."""
    for parameter in WORKBENCH_CALLER_OPENAPI["parameters"]:
        if len(request.headers.getlist(str(parameter["name"]))) > 1:
            raise HTTPException(400, detail={"code": "ambiguous_caller_context"})
    return require_workbench_caller_context(
        actor_id=request.headers.get("X-Actor-Id"),
        tenant_id=request.headers.get("X-Tenant-Id"),
        region=request.headers.get("X-Region"),
        caller_application=request.headers.get("X-Caller-Application"),
        booking_center_code=request.headers.get("X-Booking-Center-Code"),
        role=request.headers.get("X-Role"),
    )


UnambiguousWorkbenchCallerContext = Annotated[
    dict[str, str], Depends(require_unambiguous_workbench_caller_context)
]

__all__ = [
    "WorkbenchCallerContext",
    "UnambiguousWorkbenchCallerContext",
    "WORKBENCH_CALLER_OPENAPI",
    "require_workbench_caller_context",
    "require_unambiguous_workbench_caller_context",
    "workbench_caller_context_dependency",
]
