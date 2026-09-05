"""The correlation middleware captures the caller-presented identity for the
request's lifetime so every upstream call built during it propagates that
identity verbatim — and releases it afterwards so nothing leaks across
requests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.clients.upstream_headers import build_upstream_headers
from app.middleware.correlation import correlation_middleware

app = FastAPI()
app.middleware("http")(correlation_middleware)


@app.get("/probe-upstream-headers")
def probe_upstream_headers() -> dict[str, str]:
    return build_upstream_headers("corr-probe")


client = TestClient(app)


def test_identity_presented_to_the_request_reaches_upstream_headers() -> None:
    response = client.get(
        "/probe-upstream-headers",
        headers={
            "X-Tenant-Id": "tenant-sg",
            "X-Actor-Id": "PM_SG_001",
            "X-Role": "ADVISOR",
            "Authorization": "Bearer secret",
        },
    )

    payload = response.json()
    assert payload["X-Tenant-Id"] == "tenant-sg"
    assert payload["X-Actor-Id"] == "PM_SG_001"
    assert payload["X-Role"] == "ADVISOR"
    assert "Authorization" not in payload


def test_identity_does_not_leak_into_the_next_request() -> None:
    first = client.get(
        "/probe-upstream-headers",
        headers={"X-Tenant-Id": "tenant-sg"},
    )
    assert first.json()["X-Tenant-Id"] == "tenant-sg"

    second = client.get("/probe-upstream-headers")

    assert "X-Tenant-Id" not in second.json()


def test_blank_identity_headers_are_not_propagated() -> None:
    response = client.get(
        "/probe-upstream-headers",
        headers={"X-Tenant-Id": "   ", "X-Actor-Id": "PM_SG_001"},
    )

    payload = response.json()
    assert "X-Tenant-Id" not in payload
    assert payload["X-Actor-Id"] == "PM_SG_001"
