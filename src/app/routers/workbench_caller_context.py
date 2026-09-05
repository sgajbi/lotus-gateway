"""Workbench-facing aliases for the shared trusted caller-context admission."""

from app.routers.trusted_caller_context import (
    TrustedCallerContext as WorkbenchCallerContext,
)
from app.routers.trusted_caller_context import (
    require_trusted_caller_context as require_workbench_caller_context,
)
from app.routers.trusted_caller_context import (
    trusted_caller_context_dependency as workbench_caller_context_dependency,
)

__all__ = [
    "WorkbenchCallerContext",
    "require_workbench_caller_context",
    "workbench_caller_context_dependency",
]
