from __future__ import annotations

import logging
import os

from app.observability.analytics_ui_fields import (
    validate_gateway_analytics_ui_audit_log_fields,
)


def emit_gateway_analytics_read_audit_log(
    *,
    logger: logging.Logger,
    operation: str,
    status_code: int,
) -> None:
    fields = gateway_analytics_read_audit_fields(
        operation=operation,
        status_code=status_code,
    )
    if not fields:
        return
    logger.info(str(fields["event"]), extra={"extra_fields": fields})


def emit_gateway_protected_diagnostics_audit_log(
    *,
    logger: logging.Logger,
    status_code: int,
    reason: str,
) -> None:
    fields = {
        "event": "gateway.analytics.audit.protected_diagnostics_lookup",
        "route": "workbench-analytics",
        "panel": "protected-diagnostics",
        "operation": "analytics-ui.protected-diagnostics.lookup",
        "state": "ready" if 0 < status_code < 400 else "permission_blocked",
        "reason": reason,
        "status_class": _status_class(status_code),
        "region": _safe_dimension(os.getenv("LOTUS_REGION"), default="unknown"),
        "environment": _safe_dimension(os.getenv("LOTUS_ENVIRONMENT"), default="local"),
    }
    logger.info(
        "gateway.analytics.audit.protected_diagnostics_lookup",
        extra={"extra_fields": validate_gateway_analytics_ui_audit_log_fields(fields)},
    )


def gateway_analytics_read_audit_fields(
    *,
    operation: str,
    status_code: int,
) -> dict[str, object] | None:
    if status_code in {401, 403}:
        event = "gateway.analytics.audit.analytics_read_denied"
        state = "permission_blocked"
        reason = "upstream_authorization_denied"
    elif 0 < status_code < 400:
        event = "gateway.analytics.audit.analytics_read_allowed"
        state = "ready"
        reason = "upstream_read_succeeded"
    else:
        return None

    fields = {
        "event": event,
        "route": "workbench-analytics",
        "panel": _panel_for_operation(operation),
        "operation": operation,
        "state": state,
        "reason": reason,
        "status_class": _status_class(status_code),
        "region": _safe_dimension(os.getenv("LOTUS_REGION"), default="unknown"),
        "environment": _safe_dimension(os.getenv("LOTUS_ENVIRONMENT"), default="local"),
    }
    return validate_gateway_analytics_ui_audit_log_fields(fields)


def _status_class(status_code: int) -> str:
    if status_code <= 0:
        return "unknown"
    return f"{status_code // 100}xx"


def _panel_for_operation(operation: str) -> str:
    if operation.startswith("advisor_brief."):
        return "advisor-brief"
    if operation.startswith("analytics.risk."):
        return "risk-summary"
    if "workspace-summary" in operation:
        return "performance-summary"
    if operation.startswith("performance."):
        return "performance-details"
    return "unknown"


def _safe_dimension(value: str | None, *, default: str) -> str:
    if not value:
        return default
    previous_was_separator = False
    characters: list[str] = []
    for character in value.strip().lower():
        if character.isalnum() or character in {"_", "."}:
            characters.append(character)
            previous_was_separator = False
            continue
        if character in {"-", " ", "/"} and not previous_was_separator:
            characters.append("-")
            previous_was_separator = True
    cleaned = "".join(characters).strip("-")
    return cleaned[:64] or default
