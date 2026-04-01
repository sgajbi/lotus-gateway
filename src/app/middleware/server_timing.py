from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from time import perf_counter

_server_timing_metrics_var: ContextVar[list[tuple[str, float]]] = ContextVar(
    "server_timing_metrics",
    default=[],
)


def reset_server_timing_metrics() -> Token[list[tuple[str, float]]]:
    return _server_timing_metrics_var.set([])


def restore_server_timing_metrics(
    token: Token[list[tuple[str, float]]],
) -> None:
    _server_timing_metrics_var.reset(token)


def append_server_timing_metric(name: str, duration_ms: float) -> None:
    _server_timing_metrics_var.get().append((name, round(duration_ms, 2)))


def format_server_timing_header(total_duration_ms: float) -> str:
    parts = [f"app;dur={round(total_duration_ms, 2)}"]
    for name, duration_ms in _server_timing_metrics_var.get():
        parts.append(f"{name};dur={duration_ms}")
    return ", ".join(parts)


@asynccontextmanager
async def server_timing_span(name: str):
    started = perf_counter()
    try:
        yield
    finally:
        append_server_timing_metric(name, (perf_counter() - started) * 1000)
