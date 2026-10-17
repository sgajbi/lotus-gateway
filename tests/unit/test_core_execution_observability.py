import asyncio
import hashlib
import hmac
import logging

import httpx
import pytest
from pydantic import SecretStr

from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.core_execution_authority import CoreExecutionAuthority
from app.middleware.caller_identity import admit_caller_tenant, release_caller_identity
from app.observability.analytics_ui import (
    GATEWAY_ANALYTICS_DEGRADED_TOTAL,
    GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS,
)

OPERATIONS = {
    "query": "core.instruments.list",
    "bundle": "core.ingest.portfolio-bundle.create",
    "preview": "core.ingest.uploads.preview",
    "commit": "core.ingest.uploads.commit",
}
URL_OPERATIONS = {**OPERATIONS, "control-plane": "core.integration.capabilities"}


def metric_counts(operation):
    counts = {status: 0 for status in ("2xx", "3xx", "4xx", "5xx")}
    counts["degraded"] = 0
    families = (
        *GATEWAY_ANALYTICS_FANOUT_DURATION_SECONDS.collect(),
        *GATEWAY_ANALYTICS_DEGRADED_TOTAL.collect(),
    )
    for family in families:
        for sample in family.samples:
            if sample.labels.get("service") != "lotus-core":
                continue
            if sample.labels.get("operation") != operation:
                continue
            if sample.name == "lotus_gateway_analytics_fanout_duration_seconds_count":
                counts[sample.labels["status_class"]] += sample.value
            elif sample.name == "lotus_gateway_analytics_degraded_total":
                counts["degraded"] += sample.value
    return counts


def install_transport(monkeypatch, receive):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.clients.http_json_resilience.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(receive), **kwargs),
    )


async def call_core(operation, enabled, backoff_seconds=0.001, base_url="https://core.invalid"):
    authority = (
        CoreExecutionAuthority(
            key_id="synthetic-key",
            secret=SecretStr(bytes(range(32)).hex()),
            service_identity="synthetic-service",
            actor_id="synthetic-actor",
            role="synthetic-role",
            allowed_tenants=frozenset({"tenant-a"}),
            capabilities=frozenset({"core.source.read", "ingestion.portfolio_bundle.write"}),
        )
        if enabled
        else None
    )
    options = {
        "execution_authority": authority,
        "max_retries": 1,
        "retry_backoff_seconds": backoff_seconds,
    }
    token = admit_caller_tenant("tenant-a")
    try:
        if operation == "control-plane":
            return await LotusCoreQueryClient(
                "https://query-only.invalid", 1, control_plane_base_url=base_url, **options
            ).get_capabilities("consumer", "tenant-a", "observability")
        if operation == "query":
            return await LotusCoreQueryClient(base_url, 1, **options).list_instruments(
                2, "observability"
            )
        client = LotusCoreIngestionClient(base_url, 1, **options)
        admitted = {"X-Tenant-Id": "tenant-a"}
        if operation == "bundle":
            return await client.ingest_portfolio_bundle({}, "observability", "replay", admitted)
        if operation == "preview":
            return await client.preview_upload(
                "portfolio", "synthetic.csv", b"", 1, "observability", admitted
            )
        return await client.commit_upload(
            "portfolio", "synthetic.csv", b"", False, "observability", admitted
        )
    finally:
        release_caller_identity(token)


def assert_final_observation(caplog, operation, before, status):
    records = [
        record.extra_fields
        for record in caplog.records
        if hasattr(record, "extra_fields")
        and record.extra_fields.get("operation") == URL_OPERATIONS[operation]
    ]
    assert len(records) == 1
    event = records[0]
    degraded = status >= 400
    assert event["event"] == (
        "gateway.analytics.fanout.degraded" if degraded else "gateway.analytics.fanout.completed"
    )
    assert event["state"] == ("degraded" if status >= 500 else "error" if degraded else "ready")
    status_class = f"{status // 100}xx"
    assert event["status_class"] == status_class
    assert event.get("reason") == (
        "upstream_unavailable" if status >= 500 else "upstream_error" if degraded else None
    )
    after = metric_counts(URL_OPERATIONS[operation])
    for key in ("2xx", "3xx", "4xx", "5xx"):
        assert after[key] - before[key] == int(key == status_class)
    assert after["degraded"] - before["degraded"] == int(degraded)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", list(URL_OPERATIONS))
@pytest.mark.parametrize(
    "base_url",
    [
        "https://url-user:url-password@core.invalid",
        "https://url-user@core.invalid",
        "https://:url-password@core.invalid",
        "https://url%40user:url%3Apassword@core.invalid",
        "https://@core.invalid",
        "core.invalid",
        "ftp://core.invalid",
        "https:///missing-host",
        "https://core.invalid:bad-port",
        "https://[invalid-ipv6",
        "https://core.invalid/line\nbreak",
        "https://core.invalid:65536",
        "https://core.invalid:999999",
    ],
)
async def test_signed_core_target_refused_before_signing_or_wire(
    monkeypatch, caplog, operation, base_url
):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    requests = []
    signs = []
    original = CoreExecutionAuthority.sign

    def sign(authority, headers):
        signs.append(True)
        return original(authority, headers)

    def receive(request):
        requests.append(request)
        return httpx.Response(200, json={"source": "ready"})

    monkeypatch.setattr(CoreExecutionAuthority, "sign", sign)
    install_transport(monkeypatch, receive)
    before = metric_counts(URL_OPERATIONS[operation])
    result = await call_core(operation, True, base_url=base_url)
    assert result[0] == 503
    assert_final_observation(caplog, operation, before, 503)
    assert requests == [] and signs == []
    assert "core execution target refused" in str(result[1])
    for sensitive in (base_url, "url-user", "url-password", "bad-port", "invalid-ipv6"):
        assert sensitive not in str(result) + caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", list(URL_OPERATIONS))
@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize(
    "base_url",
    [
        "https://core.invalid",
        "https://core.invalid:0",
        "https://core.invalid:65535",
        "http://core.invalid:8080/base",
        "https://[::1]:8443",
    ],
)
async def test_valid_core_targets_preserve_wire_context_and_final_observation(
    monkeypatch, caplog, operation, enabled, base_url
):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    requests = []

    def receive(request):
        requests.append(request)
        assert "authorization" not in request.headers
        assert request.headers["x-tenant-id"] == "tenant-a"
        assert ("x-enterprise-auth-signature" in request.headers) == enabled
        if enabled:
            canonical = "\n".join(
                (
                    "lotus-enterprise-auth-context-v1",
                    "synthetic-key",
                    "synthetic-service",
                    "synthetic-actor",
                    "tenant-a",
                    "synthetic-role",
                    "observability",
                    request.headers["x-enterprise-auth-timestamp"],
                    "core.source.read,ingestion.portfolio_bundle.write",
                )
            )
            expected = hmac.new(bytes(range(32)).hex().encode(), canonical.encode(), hashlib.sha256)
            assert hmac.compare_digest(
                request.headers["x-enterprise-auth-signature"], expected.hexdigest()
            )
        return httpx.Response(200, json={"source": "ready"})

    install_transport(monkeypatch, receive)
    before = metric_counts(URL_OPERATIONS[operation])
    assert (await call_core(operation, enabled, base_url=base_url))[0] == 200
    assert len(requests) == 1
    assert_final_observation(caplog, operation, before, 200)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", list(URL_OPERATIONS))
@pytest.mark.parametrize(
    "base_url",
    [
        "https://url-user:url-password@core.invalid",
        "https://core.invalid:65536",
        "https://core.invalid:999999",
    ],
)
async def test_disabled_core_retains_legacy_target_transport(
    monkeypatch, caplog, operation, base_url
):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    requests = []

    def receive(request):
        requests.append(request)
        assert ("authorization" in request.headers) == ("url-user" in base_url)
        if "authorization" in request.headers:
            assert request.headers["authorization"].startswith("Basic ")
        assert "x-enterprise-auth-signature" not in request.headers
        return httpx.Response(200, json={"source": "ready"})

    install_transport(monkeypatch, receive)
    before = metric_counts(URL_OPERATIONS[operation])
    result = await call_core(operation, False, base_url=base_url)
    assert result[0] == 200 and len(requests) == 1
    assert_final_observation(caplog, operation, before, 200)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", list(OPERATIONS))
@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize(
    "outcome",
    ["deadline", "retry-deadline", "redirect", "success", "native-refusal", "connection-error"],
)
async def test_core_observer_records_final_returned_outcome_once(
    monkeypatch, caplog, operation, enabled, outcome
):
    if outcome in {"deadline", "retry-deadline"}:
        monkeypatch.setattr("app.clients.core_auth_context.CORE_EXECUTION_DEADLINE_SECONDS", 0.01)
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    requests = []
    cancelled = []

    async def receive(request):
        requests.append(request)
        assert ("x-enterprise-auth-signature" in request.headers) == enabled
        if outcome == "deadline":
            try:
                await asyncio.sleep(0.03)
            except asyncio.CancelledError:
                cancelled.append(True)
                raise
        if outcome == "redirect" and request.url.host == "core.invalid":
            return httpx.Response(
                302, headers={"location": "https://other.invalid/collect"}, json={"state": "ready"}
            )
        if outcome == "native-refusal":
            return httpx.Response(403, json={"detail": "native-source-grant-refused"})
        if outcome in {"connection-error", "retry-deadline"}:
            raise httpx.ConnectError("synthetic failed connection", request=request)
        return httpx.Response(200, json={"source": "ready"})

    install_transport(monkeypatch, receive)
    before = metric_counts(OPERATIONS[operation])
    result = await call_core(operation, enabled, 0.02 if outcome == "retry-deadline" else 0.001)
    if outcome in {"connection-error", "retry-deadline"} or (
        enabled and outcome in {"deadline", "redirect"}
    ):
        status = 503
    else:
        status = 403 if outcome == "native-refusal" else 200
    assert result[0] == status
    assert_final_observation(caplog, operation, before, status)
    assert cancelled == ([True] if enabled and outcome == "deadline" else [])
    expected_requests = 1
    if outcome == "connection-error" or (not enabled and outcome in {"redirect", "retry-deadline"}):
        expected_requests = 2
    assert len(requests) == expected_requests
    if enabled and outcome in {"deadline", "redirect"}:
        assert "other.invalid" not in str(result)
        assert "state" not in result[1]
    for sensitive in (bytes(range(32)).hex(), "synthetic-key", "synthetic-actor"):
        assert sensitive not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", list(OPERATIONS))
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
async def test_every_core_redirect_is_observed_as_final_safe_failure(
    monkeypatch, caplog, operation, status
):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    requests = []

    async def receive(request):
        requests.append(request)
        return httpx.Response(status, headers={"location": "http://other.invalid/collect"})

    install_transport(monkeypatch, receive)
    before = metric_counts(OPERATIONS[operation])
    assert (await call_core(operation, True))[0] == 503
    assert len(requests) == 1
    assert_final_observation(caplog, operation, before, 503)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", list(OPERATIONS))
@pytest.mark.parametrize("enabled", [True, False])
async def test_external_core_cancellation_emits_no_returned_outcome(
    monkeypatch, caplog, operation, enabled
):
    entered = asyncio.Event()
    cleaned = []
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")

    async def receive(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.append(True)

    install_transport(monkeypatch, receive)
    before = metric_counts(OPERATIONS[operation])
    task = asyncio.create_task(call_core(operation, enabled))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cleaned == [True]
    assert metric_counts(OPERATIONS[operation]) == before
    assert not [record for record in caplog.records if hasattr(record, "extra_fields")]
