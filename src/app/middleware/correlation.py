import json
import logging
import os
import re
import time
from contextvars import ContextVar
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request

from app.middleware.server_timing import (
    format_server_timing_header,
    reset_server_timing_metrics,
    restore_server_timing_metrics,
)

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

_W3C_TRACE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": os.getenv("SERVICE_NAME", "lotus-gateway"),
            "environment": os.getenv("ENVIRONMENT", "local"),
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get() or None,
            "request_id": request_id_var.get() or None,
            "trace_id": trace_id_var.get() or None,
        }
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            payload.update(record.extra_fields)
        return json.dumps({k: v for k, v in payload.items() if v is not None})


def setup_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)


def resolve_correlation_id(request: Request) -> str:
    incoming = request.headers.get("X-Correlation-Id")
    return incoming if incoming else f"corr_{uuid4().hex[:12]}"


def resolve_request_id(request: Request) -> str:
    incoming = request.headers.get("X-Request-Id")
    return incoming if incoming else f"req_{uuid4().hex[:12]}"


def resolve_trace_id(request: Request) -> str:
    traceparent = request.headers.get("traceparent")
    if traceparent:
        parts = traceparent.split("-")
        if len(parts) >= 4 and _is_w3c_trace_id(parts[1]):
            return parts[1]
    incoming = request.headers.get("X-Trace-Id")
    return incoming if incoming else uuid4().hex


def _is_w3c_trace_id(trace_id: str) -> bool:
    return bool(_W3C_TRACE_ID_PATTERN.fullmatch(trace_id))


def _traceparent_header(trace_id: str) -> str | None:
    if not _is_w3c_trace_id(trace_id):
        return None
    return f"00-{trace_id}-0000000000000001-01"


def propagation_headers(correlation_id: str | None = None) -> dict[str, str]:
    resolved_correlation_id = (
        correlation_id or correlation_id_var.get() or f"corr_{uuid4().hex[:12]}"
    )
    resolved_trace_id = trace_id_var.get() or uuid4().hex
    headers = {
        "X-Correlation-Id": resolved_correlation_id,
        "X-Request-Id": request_id_var.get() or f"req_{uuid4().hex[:12]}",
        "X-Trace-Id": resolved_trace_id,
    }
    traceparent = _traceparent_header(resolved_trace_id)
    if traceparent:
        headers["traceparent"] = traceparent
    return headers


async def correlation_middleware(request: Request, call_next):
    logger = logging.getLogger("http.access")
    started = time.perf_counter()

    correlation_id = resolve_correlation_id(request)
    request_id = resolve_request_id(request)
    trace_id = resolve_trace_id(request)

    correlation_token = correlation_id_var.set(correlation_id)
    request_token = request_id_var.set(request_id)
    trace_token = trace_id_var.set(trace_id)
    server_timing_token = reset_server_timing_metrics()
    try:
        response = await call_next(request)
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "request.completed",
            extra={
                "extra_fields": {
                    "http_method": request.method,
                    "endpoint": request.url.path,
                    "latency_ms": duration_ms,
                }
            },
        )
        correlation_id_var.reset(correlation_token)
        request_id_var.reset(request_token)
        trace_id_var.reset(trace_token)

    response.headers["X-Correlation-Id"] = correlation_id
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Trace-Id"] = trace_id
    traceparent = _traceparent_header(trace_id)
    if traceparent:
        response.headers["traceparent"] = traceparent
    response.headers["Server-Timing"] = format_server_timing_header(duration_ms)
    restore_server_timing_metrics(server_timing_token)
    return response
