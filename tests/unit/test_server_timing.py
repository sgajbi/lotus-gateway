import pytest

from app.middleware.server_timing import (
    append_server_timing_metric,
    format_server_timing_header,
    reset_server_timing_metrics,
    restore_server_timing_metrics,
    server_timing_span,
)


def test_server_timing_header_formats_total_and_phase_metrics():
    token = reset_server_timing_metrics()
    try:
        append_server_timing_metric("perf-summary", 12.345)
        append_server_timing_metric("perf-benchmark", 4.321)
        header = format_server_timing_header(25.678)
    finally:
        restore_server_timing_metrics(token)

    assert header.startswith("app;dur=25.68")
    assert "perf-summary;dur=12.35" in header
    assert "perf-benchmark;dur=4.32" in header


@pytest.mark.asyncio
async def test_server_timing_span_records_duration():
    token = reset_server_timing_metrics()
    try:
        async with server_timing_span("perf-overview"):
            pass
        header = format_server_timing_header(1.0)
    finally:
        restore_server_timing_metrics(token)

    assert "perf-overview;dur=" in header
