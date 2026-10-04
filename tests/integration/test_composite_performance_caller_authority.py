"""Composite Gateway -> Performance caller-authority transport proof."""

import asyncio
import csv
import io
import json
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.main import app
from app.services.composite_performance_service import CompositePerformanceService

SOURCE_RECEIPT = json.loads(
    (
        Path(__file__).resolve().parents[1] / "fixtures/composite-selector-source-responses.json"
    ).read_text(encoding="utf-8")
)


def _caller_context(tenant: str) -> dict[str, str | None]:
    return {
        "actor_id": f"advisor-{tenant}",
        "caller_application": "lotus-workbench",
        "tenant_id": tenant,
        "region": "APAC",
        "booking_center_code": "SG",
        "role": "ADVISOR",
    }


def _analytics_client() -> LotusAnalyticsClient:
    return LotusAnalyticsClient(
        base_url="https://performance.test",
        timeout_seconds=2.0,
        max_retries=0,
        retry_backoff_seconds=0.0,
    )


@pytest.fixture
def registered_composite_transport(monkeypatch):
    """Actual registered routes/client; controlled wires, not producer financial proof."""
    # TestClient shutdown drains the shared app; restore the incoming lifecycle state.
    monkeypatch.setattr(
        app.state, "is_draining", getattr(app.state, "is_draining", False), raising=False
    )
    requests = []
    upstream = {"status": 200, "payload": {"status": "READY", "periods": []}}

    def respond(request):
        requests.append(request)
        if "respond" in upstream:
            return upstream["respond"](request)
        return httpx.Response(upstream["status"], json=upstream["payload"])

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(**{"transport": httpx.MockTransport(respond), **kwargs}),
    )
    service = CompositePerformanceService(_analytics_client())
    for module in ("composite_performance", "composite_performance_inspection"):
        monkeypatch.setattr(f"app.routers.{module}.composite_performance_service", lambda: service)
    return requests, upstream


def _registered_request(client, operation, selectors, tenant="tenant-a"):
    return client.post(
        f"/api/v1/performance/composites/{operation}",
        headers={
            "X-Actor-Id": f"advisor-{tenant}",
            "X-Tenant-Id": tenant,
            "X-Region": "APAC",
            "X-Correlation-Id": "corr-selector",
        },
        json={
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            **selectors,
        },
    )


@pytest.mark.parametrize(
    "source_case",
    SOURCE_RECEIPT["cases"],
    ids=lambda case: f"{case['operation']}-{case['case']}",
)
def test_registered_composite_replays_complete_persisted_producer_selection(
    registered_composite_transport, source_case
):
    """Replay actual pinned producer output; source capture is not performed by this test."""
    requests, upstream = registered_composite_transport
    upstream.update(status=source_case["status_code"], payload=source_case["response"])
    with TestClient(app) as client:
        response = _registered_request(
            client, source_case["operation"], source_case["request"], source_case["tenant_id"]
        )
    assert response.status_code == 200
    assert response.json()["data"] == source_case["response"]
    expected_request = {
        key: value for key, value in source_case["request"].items() if value is not None
    }
    if "reporting_currency" in expected_request:
        expected_request["reporting_currency"] = expected_request["reporting_currency"].upper()
    assert len(requests) == 1
    assert json.loads(requests[0].content) == expected_request
    assert requests[0].headers["X-Tenant-Id"] == source_case["tenant_id"]
    expected_return = {
        "original": "0.010000000000",
        "latest": "0.090000000000",
        "null-defaults": "0.090000000000",
        "net-usd": "0.010000000000",
        "gross-usd": "0.030000000000",
        "net-eur": "0.050000000000",
    }[source_case["case"]]
    assert source_case["expected_return"] == expected_return
    data = response.json()["data"]
    if source_case["operation"] == "twr":
        assert data["cumulative_return"] == expected_return
        assert data["periods"][0]["return_value"] == expected_return
    else:
        artifacts = {item["artifact_name"]: item for item in data["artifacts"]}
        rows = list(
            csv.DictReader(io.StringIO(artifacts["composite_returns.csv"]["artifact_content"]))
        )
        assert rows[0]["return_value"] == expected_return
        assert rows[0]["cumulative_return"] == expected_return
        lineage = json.loads(artifacts["lineage_manifest.json"]["artifact_content"])
        assert lineage["tenant_id"] == source_case["tenant_id"]
        assert lineage["restatement_sequences"] == [
            2 if source_case["case"] in {"latest", "null-defaults"} else 1
        ]


def test_composite_source_fixture_provenance_and_worked_examples():
    assert SOURCE_RECEIPT["source_revision"] == "4ffad93e7c57789d3521ace5205bf682a6513995"
    assert SOURCE_RECEIPT["evidence_class"] == (
        "registered-API isolated SQLite persisted synthetic fact reader"
    )
    assert len(SOURCE_RECEIPT["cases"]) == 12
    repo = Path(__file__).resolve().parents[2]
    architecture = (repo / "docs/architecture.md").read_text(encoding="utf-8")
    for phrase in (
        "sequence 1 returns 1%",
        "latest returns 9%",
        "gross USD returns 3%",
        "net EUR returns 5%",
    ):
        assert phrase in architecture


@pytest.mark.parametrize("operation", ["twr", "inspect"])
@pytest.mark.parametrize("view", ["GROSS", "NET_ACTUAL", "NET_MODEL_FEE"])
def test_registered_composite_selectors_reach_concrete_http_client(
    registered_composite_transport, operation, view
):
    requests, upstream = registered_composite_transport
    # NET_MODEL_FEE here is transport selection, not a model-fee producer claim.
    upstream["payload"] = {
        "status": "READY",
        "source_fingerprints": ["sha256:retained-selection"],
        "restatement_sequence": 1,
        "artifacts": [
            {"artifact_content": "source-owned", "access_classification": "operator_only"}
        ],
    }
    with TestClient(app) as client:
        response = _registered_request(
            client,
            operation,
            {"restatement_sequence": 1, "return_view": view, "reporting_currency": "usd"},
        )
    assert response.status_code == 200
    assert response.json()["data"] == upstream["payload"]
    assert response.json()["upstream_status"] == 200
    assert len(requests) == 1
    sent = json.loads(requests[0].content)
    assert sent == {
        "composite_id": "PB_GLOBAL_BALANCED_USD",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "restatement_sequence": 1,
        "return_view": view,
        "reporting_currency": "USD",
    }
    assert requests[0].url.path == f"/performance/composites/{operation}"
    assert requests[0].headers["X-Tenant-Id"] == "tenant-a"
    assert requests[0].headers["X-Actor-Id"] == "advisor-tenant-a"
    assert requests[0].headers["X-Correlation-Id"] == "corr-selector"


@pytest.mark.parametrize("operation", ["twr", "inspect"])
@pytest.mark.parametrize(
    "selectors",
    [{}, {"restatement_sequence": None, "reporting_currency": None}],
)
def test_registered_composite_omission_delegates_source_defaults(
    registered_composite_transport, operation, selectors
):
    requests, _ = registered_composite_transport
    with TestClient(app) as client:
        response = _registered_request(client, operation, selectors)
    assert response.status_code == 200
    assert json.loads(requests[0].content) == {
        "composite_id": "PB_GLOBAL_BALANCED_USD",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
    }


@pytest.mark.parametrize("operation", ["twr", "inspect"])
@pytest.mark.parametrize(
    "selectors",
    [
        {"restatement_sequence": 0},
        {"restatement_sequence": -1},
        {"restatement_sequence": 1.5},
        {"restatement_sequence": "latest"},
        {"return_view": None},
        {"return_view": "net_actual"},
        {"return_view": "UNKNOWN"},
        {"reporting_currency": " USD"},
        {"reporting_currency": "USD "},
        {"reporting_currency": "US"},
        {"reporting_currency": "USDD"},
        {"reporting_currency": "U1D"},
        {"reporting_currency": "ÜSD"},
        {"reporting_currency": 123},
        {"restatement_version": "v1"},
        {"return_value": "0.99"},
        {"fee_rate": "0.01"},
        {"report_currency": "EUR"},
    ],
)
def test_registered_composite_invalid_or_unknown_inputs_refused_before_io(
    registered_composite_transport, operation, selectors
):
    requests, _ = registered_composite_transport
    with TestClient(app) as client:
        response = _registered_request(client, operation, selectors)
    assert response.status_code == 422
    assert requests == []


@pytest.mark.parametrize("operation", ["twr", "inspect"])
def test_registered_composite_source_selection_conflict_remains_typed(
    registered_composite_transport, operation
):
    requests, upstream = registered_composite_transport
    upstream.update(
        status=409,
        payload={
            "detail": {
                "code": "COMPOSITE_FACT_SELECTION_INCOMPLETE",
                "message": "Unavailable selection",
            }
        },
    )
    with TestClient(app) as client:
        response = _registered_request(client, operation, {"restatement_sequence": 9})
    # Preserve the existing Gateway mapping; the producer conflict remains explicit.
    assert response.status_code == 502
    assert response.json()["detail"]["upstream_status"] == 409
    assert response.json()["detail"]["source_service"] == "lotus-performance"
    assert response.json()["detail"]["detail"] == "COMPOSITE_FACT_SELECTION_INCOMPLETE"
    assert len(requests) == 1


@pytest.mark.parametrize("operation", ["twr", "inspect"])
@pytest.mark.parametrize("authority", ["missing", "blank", "repeated"])
def test_registered_composite_selectors_do_not_bypass_authority(
    registered_composite_transport, operation, authority
):
    requests, _ = registered_composite_transport
    headers = [("X-Actor-Id", "advisor"), ("X-Region", "APAC")]
    if authority == "blank":
        headers.append(("X-Tenant-Id", " "))
    elif authority == "repeated":
        headers.extend([("X-Tenant-Id", "tenant-a"), ("X-Tenant-Id", "tenant-b")])
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/performance/composites/{operation}",
            headers=headers,
            json={
                "composite_id": "PB_GLOBAL_BALANCED_USD",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
                "return_view": "GROSS",
                "reporting_currency": "EUR",
                "restatement_sequence": 1,
            },
        )
    assert response.status_code == 400
    assert requests == []


@pytest.mark.asyncio
async def test_registered_composite_concurrent_selection_and_poll_scope(
    registered_composite_transport,
):
    requests, upstream = registered_composite_transport
    selected = {}

    def respond(request):
        tenant = request.headers["X-Tenant-Id"]
        assert request.headers["X-Actor-Id"] == f"advisor-{tenant}"
        if request.method == "POST":
            operation = request.url.path.rsplit("/", 1)[-1]
            key = f"{operation}-{tenant}"
            selected[key] = json.loads(request.content)
            return httpx.Response(
                202,
                json={
                    "calculation_id": key,
                    "result_path": f"/performance/composites/results/{key}",
                    "recommended_poll_after_seconds": 0.001,
                },
            )
        key = request.url.path.rsplit("/", 1)[-1]
        assert key.endswith(tenant)
        return httpx.Response(200, json={"status": "READY", "selection": selected[key]})

    upstream["respond"] = respond
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
    ) as client:
        responses = await asyncio.gather(
            *[
                client.post(
                    f"/api/v1/performance/composites/{operation}",
                    headers={
                        "X-Tenant-Id": tenant,
                        "X-Actor-Id": f"advisor-{tenant}",
                        "X-Region": "APAC",
                    },
                    json={
                        "composite_id": "PB_GLOBAL_BALANCED_USD",
                        "period_start": "2026-01-01",
                        "period_end": "2026-03-31",
                        "return_view": view,
                        "reporting_currency": currency,
                        "restatement_sequence": sequence,
                    },
                )
                for operation in ("twr", "inspect")
                for tenant, view, currency, sequence in (
                    ("tenant-a", "GROSS", "USD", 1),
                    ("tenant-b", "NET_ACTUAL", "EUR", 2),
                )
            ]
        )
    assert len(requests) == 8
    for response, expected in zip(
        responses,
        [("GROSS", "USD", 1), ("NET_ACTUAL", "EUR", 2)] * 2,
        strict=True,
    ):
        assert response.status_code == 200
        selection = response.json()["data"]["selection"]
        assert (
            selection["return_view"],
            selection["reporting_currency"],
            selection["restatement_sequence"],
        ) == expected


@pytest.mark.asyncio
async def test_concurrent_composite_calls_preserve_authority_through_submission_and_poll(
    monkeypatch,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        tenant = request.headers.get("X-Tenant-Id")
        if tenant not in {"tenant-a", "tenant-b"}:
            return httpx.Response(401, json={"detail": "tenant required"})
        if request.method == "POST":
            submitted = json.loads(request.content)
            assert submitted == {
                "composite_id": "PB_GLOBAL_BALANCED_USD",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
            }
            operation = "inspect" if request.url.path.endswith("/inspect") else "twr"
            return httpx.Response(
                202,
                json={
                    "calculation_id": f"{operation}-{tenant}",
                    "result_path": f"/performance/composites/results/{operation}/{tenant}",
                    "recommended_poll_after_seconds": 0.001,
                },
            )
        operation, result_tenant = request.url.path.rsplit("/", 2)[-2:]
        assert result_tenant == tenant
        return httpx.Response(
            200,
            json={
                "status": "READY",
                "operation": operation,
                "tenant_marker": tenant,
            },
        )

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    service = CompositePerformanceService(analytics_client=_analytics_client())
    payload = {
        "composite_id": "PB_GLOBAL_BALANCED_USD",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
    }

    twr_a, twr_b, inspect_a, inspect_b = await asyncio.gather(
        service.calculate_twr(
            payload=payload,
            correlation_id="corr-twr-a",
            caller_context=_caller_context("tenant-a"),
        ),
        service.calculate_twr(
            payload=payload,
            correlation_id="corr-twr-b",
            caller_context=_caller_context("tenant-b"),
        ),
        service.inspect(
            payload=payload,
            correlation_id="corr-inspect-a",
            caller_context=_caller_context("tenant-a"),
        ),
        service.inspect(
            payload=payload,
            correlation_id="corr-inspect-b",
            caller_context=_caller_context("tenant-b"),
        ),
    )

    assert [result.data["tenant_marker"] for result in (twr_a, twr_b)] == [
        "tenant-a",
        "tenant-b",
    ]
    assert [result.data["tenant_marker"] for result in (inspect_a, inspect_b)] == [
        "tenant-a",
        "tenant-b",
    ]
    assert len(requests) == 8
    for request in requests:
        tenant = request.headers["X-Tenant-Id"]
        assert request.headers["X-Actor-Id"] == f"advisor-{tenant}"
        assert request.headers["X-Caller-Application"] == "lotus-workbench"
        assert request.headers["X-Region"] == "APAC"
        assert request.headers["X-Booking-Center-Code"] == "SG"
        assert request.headers["X-Role"] == "ADVISOR"


@pytest.mark.asyncio
async def test_composite_bound_authority_never_follows_foreign_result_target(
    monkeypatch,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(
                202,
                json={
                    "calculation_id": "calc-foreign",
                    "result_path": "https://foreign.test/performance/results/calc-foreign",
                    "recommended_poll_after_seconds": 0.001,
                },
            )
        return httpx.Response(200, json={"status": "READY"})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    service = CompositePerformanceService(analytics_client=_analytics_client())

    with pytest.raises(HTTPException) as exc_info:
        await service.calculate_twr(
            payload={
                "composite_id": "PB_GLOBAL_BALANCED_USD",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
            },
            correlation_id="corr-foreign",
            caller_context=_caller_context("tenant-a"),
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["source_service"] == "lotus-performance"
    assert exc_info.value.detail["upstream_status"] == 502
    assert len(requests) == 1
