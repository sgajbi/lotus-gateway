import ast
import asyncio
import json
import logging
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.observed_fanout import request_observed_fanout
from app.clients.upstream_headers import build_upstream_headers
from app.core_execution_authority import (
    CoreAuthorityError,
    CoreExecutionAuthority,
    load_core_execution_authority,
)
from app.middleware.caller_identity import admit_caller_tenant, release_caller_identity
from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)


def _runtime_layer_imports(source):
    modules = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return {
        module
        for module in modules
        if any(
            module == f"app.{layer}" or module.startswith(f"app.{layer}.")
            for layer in ("clients", "services", "routers", "middleware")
        )
    }


def test_core_factory_imports_only_admitted_concrete_clients():
    source = Path("src/app/services/lotus_core_client_factory.py").read_text(encoding="utf-8")
    assert _runtime_layer_imports(source) == {
        "app.clients.lotus_core_ingestion_client",
        "app.clients.lotus_core_query_client",
    }


@pytest.mark.parametrize("layer", ["clients", "services", "routers", "middleware"])
@pytest.mark.parametrize("statement", ["import app.{layer}.probe", "from app.{layer} import probe"])
def test_core_authority_boundary_detects_runtime_dependencies(layer, statement):
    expected = f"app.{layer}.probe" if statement.startswith("import ") else f"app.{layer}"
    assert _runtime_layer_imports(statement.format(layer=layer)) == {expected}


def test_core_authority_has_no_runtime_layer_dependency():
    source = Path("src/app/core_execution_authority.py").read_text(encoding="utf-8")
    assert _runtime_layer_imports(source) == set()
    assert _runtime_layer_imports("from pydantic import SecretStr\nimport hmac") == set()


@pytest.fixture
def authority():
    return CoreExecutionAuthority(
        key_id="synthetic-key",
        secret=SecretStr(bytes(range(32)).hex()),
        service_identity="synthetic-service",
        actor_id="synthetic-actor",
        role="synthetic-role",
        allowed_tenants=frozenset({"tenant-a", "tenant-b"}),
        capabilities=frozenset({"core.source.read", "ingestion.portfolio_bundle.write"}),
    )


def test_independent_protocol_vector_and_private_final_context(authority, monkeypatch):
    monkeypatch.setattr("app.core_execution_authority.time.time", lambda: 1700000000)
    source = {
        "X-Tenant-Id": " tenant-a ",
        "X-Correlation-Id": "correlation-a",
        "X-Actor-Id": "forged-browser",
        "X-Role": "admin",
        "X-Capabilities": "everything",
        "X-Caller-Capabilities": "core.intake.write",
        "X-Service-Identity": "forged-service",
        "Authorization": "Bearer browser-value",
        "X-Enterprise-Auth-Signature": "forged",
    }
    signed = authority.sign(source)
    assert signed["x-enterprise-auth-signature"] == (
        "6b75ad081d8f9e3e6bffeb00b3c9d9493e19cc92791d20f82a0c2cc53f0eec49"
    )
    assert signed["x-actor-id"] == "synthetic-actor"
    assert signed["x-role"] == "synthetic-role"
    assert "authorization" not in signed
    assert "x-caller-capabilities" not in signed
    assert source["X-Actor-Id"] == "forged-browser"
    assert authority.secret.get_secret_value() not in repr(authority)


@pytest.mark.parametrize("field", ["key_id", "service_identity", "actor_id", "role"])
@pytest.mark.parametrize("value", ["", " ", "x\ny", "x" * 129])
def test_invalid_operator_identity_fails_closed(authority, field, value):
    with pytest.raises(CoreAuthorityError):
        replace(authority, **{field: value})


@pytest.mark.parametrize(
    "changes",
    [
        {"secret": SecretStr(" ")},
        {"allowed_tenants": frozenset()},
        {"allowed_tenants": frozenset({"*"})},
        {"capabilities": frozenset()},
        {"capabilities": frozenset({"read,write"})},
    ],
)
def test_invalid_operator_scope_fails_closed(authority, changes):
    with pytest.raises(CoreAuthorityError):
        replace(authority, **changes)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Tenant-Id": "tenant-a"},
        {"X-Tenant-Id": "tenant-c", "X-Correlation-Id": "c"},
        {"X-Tenant-Id": "tenant-a", "x-tenant-id": "tenant-b", "X-Correlation-Id": "c"},
    ],
)
def test_missing_outside_or_ambiguous_request_context_refused(authority, headers):
    with pytest.raises(CoreAuthorityError):
        authority.sign(headers)


def test_config_enablement_is_explicit_and_incomplete_fails_closed(monkeypatch):
    monkeypatch.setenv("CORE_EXECUTION_ENABLED", "false")
    monkeypatch.setenv("CORE_EXECUTION_ALLOWED_TENANTS", "malformed")
    assert load_core_execution_authority() is None
    monkeypatch.setenv("CORE_EXECUTION_ENABLED", "true")
    with pytest.raises(CoreAuthorityError, match="^invalid_core_execution_configuration$"):
        load_core_execution_authority()
    monkeypatch.setenv("CORE_EXECUTION_ENABLED", "maybe")
    with pytest.raises(CoreAuthorityError, match="enablement"):
        load_core_execution_authority()


def test_factory_configuration_rotates_cached_authority(authority, monkeypatch):
    monkeypatch.setenv("CORE_EXECUTION_ENABLED", "true")
    for field in ("key_id", "service_identity", "actor_id", "role"):
        monkeypatch.setenv(f"CORE_EXECUTION_{field.upper()}", getattr(authority, field))
    monkeypatch.setenv("CORE_EXECUTION_SECRET", authority.secret.get_secret_value())
    monkeypatch.setenv(
        "CORE_EXECUTION_ALLOWED_TENANTS", json.dumps(sorted(authority.allowed_tenants))
    )
    monkeypatch.setenv("CORE_EXECUTION_CAPABILITIES", json.dumps(sorted(authority.capabilities)))
    assert build_lotus_core_query_client()._execution_authority == authority
    signature = lotus_core_query_client_signature()
    monkeypatch.setenv(
        "CORE_EXECUTION_SECRET", SecretStr(bytes(range(1, 33)).hex()).get_secret_value()
    )
    assert signature != lotus_core_query_client_signature()
    assert authority.secret.get_secret_value() not in repr(signature)


def install_transport(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.clients.http_json_resilience.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )


@pytest.mark.asyncio
async def test_query_concurrent_tenants_and_error_cancellation_reset(authority, monkeypatch):
    seen = []
    entered = asyncio.Event()

    async def receive(request):
        seen.append(dict(request.headers))
        if request.headers["x-correlation-id"] == "non-core":
            assert not any("enterprise-auth" in name for name in request.headers)
            assert "x-capabilities" not in request.headers
            assert "x-service-identity" not in request.headers
            return httpx.Response(200, json={"non_core": True})
        if request.headers["x-correlation-id"] == "cancel":
            entered.set()
            await asyncio.Event().wait()
        if request.headers["x-correlation-id"] == "error":
            raise httpx.ConnectError("synthetic transport failure", request=request)
        await asyncio.sleep(0)
        return httpx.Response(200, json={"tenant": request.headers["x-tenant-id"]})

    install_transport(monkeypatch, receive)
    client = LotusCoreQueryClient(
        "https://core.invalid", 1, max_retries=0, execution_authority=authority
    )

    async def call(tenant, correlation):
        token = admit_caller_tenant(tenant)
        try:
            return await client.list_instruments(2, correlation)
        finally:
            release_caller_identity(token)

    results = await asyncio.gather(call("tenant-a", "a"), call("tenant-b", "b"))
    assert results == [(200, {"tenant": "tenant-a"}), (200, {"tenant": "tenant-b"})]
    assert seen[0]["x-enterprise-auth-signature"] != seen[1]["x-enterprise-auth-signature"]
    assert (await call("tenant-a", "error"))[0] == 503
    task = asyncio.create_task(call("tenant-b", "cancel"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with pytest.raises(CoreAuthorityError):
        await client.list_instruments(2, "no-context-after-reset")
    assert (await call("tenant-a", "after"))[1] == {"tenant": "tenant-a"}
    generic = build_upstream_headers("non-core")
    assert not any("enterprise-auth" in name.lower() for name in generic)
    assert "x-capabilities" not in {name.lower() for name in generic}
    assert await request_observed_fanout(
        logger=logging.getLogger(__name__),
        service="non-core",
        operation="test.read",
        method="GET",
        url="https://non-core.invalid",
        timeout_seconds=1,
        headers=generic,
    ) == (200, {"non_core": True})


@pytest.mark.asyncio
async def test_intake_uses_only_explicit_tenant_and_preserves_idempotency(authority, monkeypatch):
    seen = []

    async def receive(request):
        seen.append(request)
        return httpx.Response(403, json={"detail": "native-source-grant-refused"})

    install_transport(monkeypatch, receive)
    client = LotusCoreIngestionClient("https://core.invalid", 1, execution_authority=authority)
    token = admit_caller_tenant("tenant-b")
    try:
        with pytest.raises(CoreAuthorityError):
            await client.ingest_portfolio_bundle({}, "intake")
        result = await client.ingest_portfolio_bundle(
            {}, "intake", "replay-key", {"X-Tenant-Id": "tenant-a", "X-Actor-Id": "human"}
        )
    finally:
        release_caller_identity(token)
    assert result == (403, {"detail": "native-source-grant-refused"})
    assert len(seen) == 1
    assert seen[0].headers["x-tenant-id"] == "tenant-a"
    assert seen[0].headers["x-idempotency-key"] == "replay-key"
    assert seen[0].headers["x-actor-id"] == authority.actor_id


@pytest.mark.asyncio
async def test_retry_remains_signed_and_next_request_gets_fresh_timestamp(authority, monkeypatch):
    seen = []
    clock = [1700000000]
    monkeypatch.setattr("app.core_execution_authority.time.time", lambda: clock[0])

    async def receive(request):
        seen.append(dict(request.headers))
        clock[0] += 1
        if len(seen) == 1:
            raise httpx.ConnectError("synthetic pre-send failure", request=request)
        return httpx.Response(200, json={})

    install_transport(monkeypatch, receive)
    client = LotusCoreQueryClient(
        "https://core.invalid", 1, retry_backoff_seconds=0.001, execution_authority=authority
    )
    token = admit_caller_tenant("tenant-a")
    try:
        assert (await client.list_instruments(2, "retry"))[0] == 200
        assert (await client.list_instruments(2, "next"))[0] == 200
    finally:
        release_caller_identity(token)
    assert seen[0]["x-enterprise-auth-signature"] == seen[1]["x-enterprise-auth-signature"]
    assert all(abs(clock[0] - int(h["x-enterprise-auth-timestamp"])) < 300 for h in seen)
    assert seen[2]["x-enterprise-auth-timestamp"] != seen[0]["x-enterprise-auth-timestamp"]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["query", "bundle", "preview", "commit"])
async def test_core_total_deadline_bounds_retry_backoff_and_context_resets(
    authority, monkeypatch, operation
):
    monkeypatch.setattr("app.clients.core_auth_context.CORE_EXECUTION_DEADLINE_SECONDS", 0.03)
    requests = []

    async def receive(request):
        requests.append(dict(request.headers))
        raise httpx.ConnectError("synthetic failed connection", request=request)

    install_transport(monkeypatch, receive)
    query = LotusCoreQueryClient(
        "https://core.invalid",
        1,
        max_retries=5,
        retry_backoff_seconds=0.02,
        execution_authority=authority,
    )
    intake = LotusCoreIngestionClient(
        "https://core.invalid",
        1,
        max_retries=5,
        retry_backoff_seconds=0.02,
        execution_authority=authority,
    )
    token = admit_caller_tenant("tenant-a")
    try:
        if operation == "query":
            result = await query.list_instruments(2, "deadline")
        elif operation == "bundle":
            result = await intake.ingest_portfolio_bundle(
                {}, "deadline", caller_headers={"X-Tenant-Id": "tenant-a"}
            )
        elif operation == "preview":
            result = await intake.preview_upload(
                "portfolio", "synthetic.csv", b"", 1, "deadline", {"X-Tenant-Id": "tenant-a"}
            )
        else:
            result = await intake.commit_upload(
                "portfolio", "synthetic.csv", b"", False, "deadline", {"X-Tenant-Id": "tenant-a"}
            )
    finally:
        release_caller_identity(token)
    assert result[0] == 503
    assert "core execution deadline exceeded" in str(result[1])
    assert 1 <= len(requests) < 6
    assert len({request["x-enterprise-auth-signature"] for request in requests}) == 1
    await asyncio.sleep(0.04)
    assert len(requests) < 6  # cancellation must not leave retries running in the background
    with pytest.raises(CoreAuthorityError):
        await query.list_instruments(2, "reset")


@pytest.mark.asyncio
async def test_disabled_legacy_core_call_retains_timeout_behavior(monkeypatch):
    monkeypatch.setattr("app.clients.core_auth_context.CORE_EXECUTION_DEADLINE_SECONDS", 0.001)

    async def receive(request):
        await asyncio.sleep(0.01)
        assert "x-enterprise-auth-signature" not in request.headers
        return httpx.Response(200, json={})

    install_transport(monkeypatch, receive)
    query = LotusCoreQueryClient("https://core.invalid", 1)
    assert await query.list_instruments(2, "legacy") == (200, {})


async def call_redirect_probe(operation, authority):
    query = LotusCoreQueryClient("https://core.invalid", 1, execution_authority=authority)
    intake = LotusCoreIngestionClient("https://core.invalid", 1, execution_authority=authority)
    admitted = {"X-Tenant-Id": "tenant-a"}
    if operation == "query-get":
        return await query.list_instruments(2, "redirect-probe")
    if operation == "query-post":
        return await query.get_core_snapshot(
            "portfolio", "2026-04-10", [], "consumer", "redirect-probe"
        )
    if operation == "bundle":
        return await intake.ingest_portfolio_bundle({}, "redirect-probe", "replay", admitted)
    if operation == "preview":
        return await intake.preview_upload(
            "portfolio", "synthetic.csv", b"", 1, "redirect-probe", admitted
        )
    return await intake.commit_upload(
        "portfolio", "synthetic.csv", b"", False, "redirect-probe", admitted
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "target",
    [
        "https://other.invalid/collect",
        "http://other.invalid/collect",
        "https://core.invalid/collect",
    ],
)
@pytest.mark.parametrize("operation", ["query-get", "query-post", "bundle", "preview", "commit"])
async def test_enabled_core_refuses_redirect_before_disclosing_context(
    authority, monkeypatch, status, target, operation
):
    seen = []

    async def receive(request):
        seen.append(request)
        if len(seen) > 1:
            pytest.fail("redirect disclosed signed authority through a second request")
        assert request.url.host == "core.invalid"
        assert "x-enterprise-auth-signature" in request.headers
        return httpx.Response(
            status,
            headers={"location": target},
            json={"sensitive_producer_body": "must-not-be-returned"},
        )

    install_transport(monkeypatch, receive)
    token = admit_caller_tenant("tenant-a")
    try:
        result = await call_redirect_probe(operation, authority)
    finally:
        release_caller_identity(token)
    assert result == (
        503,
        {"detail": "upstream communication failure: core upstream redirect refused"},
    )
    assert len(seen) == 1
    assert target not in str(result)
    assert "sensitive_producer_body" not in str(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["generic", "disabled-core"])
async def test_default_generic_and_disabled_core_redirect_compatibility(monkeypatch, mode):
    seen = []

    async def receive(request):
        seen.append(request)
        assert "x-enterprise-auth-signature" not in request.headers
        if request.url.host == "core.invalid":
            return httpx.Response(302, headers={"location": "https://other.invalid/collect"})
        return httpx.Response(200, json={"legacy_redirect": True})

    install_transport(monkeypatch, receive)
    if mode == "disabled-core":
        result = await call_redirect_probe("query-get", None)
    else:
        result = await request_observed_fanout(
            logger=logging.getLogger(__name__),
            service="non-core",
            operation="test.read",
            method="GET",
            url="https://core.invalid",
            timeout_seconds=1,
            headers=build_upstream_headers("generic-redirect"),
        )
    assert result == (200, {"legacy_redirect": True})
    assert [request.url.host for request in seen] == ["core.invalid", "other.invalid"]


@pytest.mark.asyncio
@pytest.mark.parametrize("source_status", [200, 403, "connection-error", "deadline"])
async def test_observed_fanout_extraction_preserves_status_and_single_event(
    monkeypatch, source_status
):
    from app.clients import observed_fanout

    emitted = []
    monkeypatch.setattr(
        observed_fanout,
        "emit_gateway_analytics_fanout_log",
        lambda **kwargs: emitted.append(kwargs),
    )
    original_send = observed_fanout.request_with_retry_outcome

    async def inspect_options(**kwargs):
        assert "follow_redirects" not in kwargs
        assert "core_execution" not in kwargs
        return await original_send(**kwargs)

    monkeypatch.setattr(observed_fanout, "request_with_retry_outcome", inspect_options)

    async def receive(request):
        if source_status == "connection-error":
            raise httpx.ConnectError("synthetic connection failure", request=request)
        if source_status == "deadline":
            await asyncio.Event().wait()
        return httpx.Response(source_status, json={"source_payload": "unchanged"})

    install_transport(monkeypatch, receive)
    result = await request_observed_fanout(
        logger=logging.getLogger(__name__),
        service="generic",
        operation="test.observe",
        method="GET",
        url="https://generic.invalid",
        timeout_seconds=1,
        max_retries=0,
        total_deadline_seconds=0.001 if source_status == "deadline" else None,
    )
    expected = source_status if isinstance(source_status, int) else 503
    assert result[0] == expected
    if isinstance(source_status, int):
        assert result[1] == {"source_payload": "unchanged"}
    assert len(emitted) == 1
    assert emitted[0]["status_code"] == result[0]
    assert emitted[0]["payload"] == result[1]
    assert emitted[0]["service"] == "generic"
    assert emitted[0]["operation"] == "test.observe"


@pytest.mark.asyncio
async def test_observed_fanout_extraction_preserves_external_cancellation(monkeypatch):
    entered = asyncio.Event()
    emitted = []
    monkeypatch.setattr(
        "app.clients.observed_fanout.emit_gateway_analytics_fanout_log",
        lambda **kwargs: emitted.append(kwargs),
    )

    async def receive(request):
        entered.set()
        await asyncio.Event().wait()

    install_transport(monkeypatch, receive)
    task = asyncio.create_task(
        request_observed_fanout(
            logger=logging.getLogger(__name__),
            service="generic",
            operation="test.cancel",
            method="GET",
            url="https://generic.invalid",
            timeout_seconds=1,
        )
    )
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert emitted == []
