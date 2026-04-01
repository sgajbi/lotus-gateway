from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.correlation import resolve_trace_id
from app.middleware.correlation import correlation_middleware
from app.middleware.server_timing import append_server_timing_metric


def test_correlation_header_is_returned():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-Id": "corr_test_1"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == "corr_test_1"
    assert response.headers.get("X-Request-Id")
    assert response.headers.get("X-Trace-Id")
    assert response.headers.get("Server-Timing")


def test_server_timing_header_exposes_app_duration():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    server_timing = response.headers.get("Server-Timing")
    assert server_timing is not None
    assert server_timing.startswith("app;dur=")
    duration_value = float(server_timing.removeprefix("app;dur="))
    assert duration_value >= 0.0


def test_server_timing_header_includes_phase_metrics_when_recorded():
    timing_app = FastAPI()
    timing_app.middleware("http")(correlation_middleware)

    @timing_app.get("/timed")
    async def _timed_health():
        append_server_timing_metric("perf-summary", 12.34)
        return {"status": "ok"}

    client = TestClient(timing_app)
    response = client.get("/timed")

    assert response.status_code == 200
    server_timing = response.headers.get("Server-Timing")
    assert server_timing is not None
    assert "app;dur=" in server_timing
    assert "perf-summary;dur=12.34" in server_timing


def test_correlation_header_casing_variants_are_equivalent():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-ID": "corr_test_legacy"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == "corr_test_legacy"


def test_trace_id_falls_back_to_x_trace_id_when_traceparent_invalid():
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={
            "traceparent": "invalid-traceparent",
            "X-Trace-Id": "trace-from-header",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id") == "trace-from-header"


def test_trace_id_generated_when_missing():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id")


def test_resolve_trace_id_uses_generated_value_for_invalid_traceparent_without_fallback():
    class _FakeHeaders:
        def __init__(self, values: dict[str, str]):
            self._values = values

        def get(self, key: str):
            return self._values.get(key)

    class _FakeRequest:
        headers = _FakeHeaders({"traceparent": "invalid"})

    resolved = resolve_trace_id(_FakeRequest())
    assert len(resolved) == 32


def test_resolve_trace_id_prefers_valid_traceparent():
    class _FakeHeaders:
        def __init__(self, values: dict[str, str]):
            self._values = values

        def get(self, key: str):
            return self._values.get(key)

    class _FakeRequest:
        headers = _FakeHeaders(
            {"traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"}
        )

    resolved = resolve_trace_id(_FakeRequest())
    assert resolved == "0123456789abcdef0123456789abcdef"
