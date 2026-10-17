"""Explicit source contract proof, without installing a sibling as a runtime dependency.

Set CORE_PROTOCOL_SOURCE_ROOT to the reviewed Core checkout to run this pack.
Only native pure verifier/authorization definitions are compiled unchanged.
This proves HTTP transport/protocol agreement, not Core application/runtime admission.
"""

import ast
import asyncio
import hashlib
import hmac
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr

from app.clients.lotus_core_ingestion_client import LotusCoreIngestionClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.core_execution_authority import CoreExecutionAuthority
from app.middleware.caller_identity import admit_caller_tenant, release_caller_identity

CORE_PROTOCOL_PIN = "ceba793a4e538688723938e4f85bd9a0d117dc8f"


def _native_definitions(path, names, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    selected = [node for node in tree.body if getattr(node, "name", None) in names]
    assert {node.name for node in selected} == set(names)
    module = ast.Module(
        body=[
            ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
            *selected,
        ],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)


@pytest.fixture
def native():
    configured = os.getenv("CORE_PROTOCOL_SOURCE_ROOT")
    if not configured:
        pytest.skip("explicit reviewed Core source checkout required for native protocol proof")
    root = Path(configured).resolve()
    pin = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert pin == CORE_PROTOCOL_PIN
    relative = Path("src/libs/portfolio-common/portfolio_common")
    sources = [relative / "enterprise_readiness.py", relative / "enterprise_request_context.py"]
    for source in sources:
        committed = subprocess.run(
            ["git", "show", f"{pin}:{source.as_posix()}"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        assert committed.replace(b"\r\n", b"\n") == (root / source).read_bytes().replace(
            b"\r\n", b"\n"
        )
    namespace = {
        "__name__": __name__,
        "dataclass": dataclass,
        "hashlib": hashlib,
        "hmac": hmac,
        "time": time,
        "MAX_SECURITY_AUDIT_AUTHORITY_LENGTH": 128,
    }
    _native_definitions(root / sources[1], {"audit_authority_headers_are_bounded"}, namespace)
    _native_definitions(
        root / sources[0],
        {
            "VerifiedServicePrincipal",
            "_normalize_headers",
            "_capabilities_from_headers",
            "_verified_service_principal",
            "verify_service_principal",
            "_unsupported_authorization_reason",
            "_auth_context_timestamp",
            "_enterprise_auth_context_signature",
        },
        namespace,
    )
    # Compile Core's actual capability refusal method as a standalone definition.
    tree = ast.parse((root / sources[0]).read_text(encoding="utf-8"))
    runtime = next(
        node for node in tree.body if getattr(node, "name", "") == "EnterpriseReadinessRuntime"
    )
    method = next(
        node
        for node in runtime.body
        if getattr(node, "name", "") == "_authorize_required_capability"
    )
    # Future annotations avoids importing Core's unrelated infrastructure graph.
    module = ast.Module(
        body=[
            ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
            method,
        ],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(root / sources[0]), "exec"), namespace)
    return namespace


@pytest.fixture
def execution_authority():
    return CoreExecutionAuthority(
        "synthetic-key",
        SecretStr(bytes(range(32)).hex()),
        "synthetic-service",
        "synthetic-actor",
        "synthetic-role",
        frozenset({"tenant-a", "tenant-b"}),
        frozenset(
            {"source_data.portfolio_state_snapshot.read", "ingestion.portfolio_bundle.write"}
        ),
    )


def settings_for(authority):
    return SimpleNamespace(
        enterprise_auth_context_hmac_secret=authority.secret.get_secret_value(),
        enterprise_primary_key_id=authority.key_id,
        enterprise_auth_context_max_age_seconds=300,
    )


def admit_native(native, headers, authority, capability):
    principal = native["verify_service_principal"](headers, settings_for(authority))
    if isinstance(principal, str):
        return False, principal
    policy = SimpleNamespace(env_enabled=lambda *_: True)
    return native["_authorize_required_capability"](policy, capability, principal)


@pytest.mark.asyncio
async def test_real_query_and_ingestion_transport_agree_with_native(
    native, execution_authority, monkeypatch
):
    observed = []

    async def receive(request):
        headers = dict(request.headers)
        capability = (
            "ingestion.portfolio_bundle.write"
            if request.url.path.startswith("/ingest")
            else "source_data.portfolio_state_snapshot.read"
        )
        assert admit_native(native, headers, execution_authority, capability) == (True, None)
        observed.append(request)
        await asyncio.sleep(0)
        return httpx.Response(200, json={"native_verified": True})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.clients.http_json_resilience.httpx.AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(receive), **kw),
    )
    query = LotusCoreQueryClient("https://core.invalid", 1, execution_authority=execution_authority)
    intake = LotusCoreIngestionClient(
        "https://core.invalid", 1, execution_authority=execution_authority
    )
    token = admit_caller_tenant("tenant-a")
    try:
        assert (await query.get_core_snapshot("portfolio", "2026-04-10", [], "consumer", "q"))[
            0
        ] == 200
        assert (
            await query._get_control_plane_resource(
                operation="core.snapshot.read",
                path="/integration/portfolios/portfolio/core-snapshot",
                correlation_id="q-read",
            )
        )[0] == 200
        assert (await intake.ingest_portfolio_bundle({}, "i", "idem", {"X-Tenant-Id": "tenant-b"}))[
            0
        ] == 200
    finally:
        release_caller_identity(token)
    assert [request.headers["x-tenant-id"] for request in observed] == [
        "tenant-a",
        "tenant-a",
        "tenant-b",
    ]
    assert observed[2].headers["x-idempotency-key"] == "idem"


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ({"x-enterprise-auth-key-id": "wrong"}, "invalid_auth_context_key_id"),
        ({"x-enterprise-auth-timestamp": "1"}, "stale_auth_context"),
        ({"x-enterprise-auth-signature": "forged"}, "invalid_auth_context_signature"),
        ({"x-enterprise-auth-signature": ""}, "missing_auth_context_signature"),
        ({"x-enterprise-auth-timestamp": "bad"}, "invalid_auth_context_timestamp"),
        ({"x-correlation-id": "changed-after-signing"}, "invalid_auth_context_signature"),
        ({"x-capabilities": "privilege-injected-after-signing"}, "invalid_auth_context_signature"),
        ({"x-service-identity": ""}, "missing_service_identity"),
    ],
)
def test_native_adverse_protocol_context(native, execution_authority, mutation, reason):
    headers = execution_authority.sign({"X-Tenant-Id": "tenant-a", "X-Correlation-Id": "q"})
    headers.update(mutation)
    assert admit_native(
        native, headers, execution_authority, "source_data.portfolio_state_snapshot.read"
    ) == (False, reason)


def test_native_wrong_secret_and_missing_capability_and_rule(native, execution_authority):
    from dataclasses import replace

    headers = execution_authority.sign({"X-Tenant-Id": "tenant-a", "X-Correlation-Id": "q"})
    wrong = replace(execution_authority, secret=SecretStr(bytes(range(1, 33)).hex()))
    assert admit_native(native, headers, wrong, "source_data.portfolio_state_snapshot.read") == (
        False,
        "invalid_auth_context_signature",
    )
    assert admit_native(native, headers, execution_authority, "not.admitted") == (
        False,
        "missing_capability:not.admitted",
    )
    assert admit_native(native, headers, execution_authority, None) == (
        False,
        "missing_capability_rule",
    )


@pytest.mark.asyncio
async def test_retry_that_expires_preserves_native_stale_refusal(
    native, execution_authority, monkeypatch
):
    clock = [1700000000]
    monkeypatch.setattr("app.core_execution_authority.time.time", lambda: clock[0])
    attempts = []

    async def receive(request):
        attempts.append(dict(request.headers))
        if len(attempts) == 1:
            clock[0] += 301
            raise httpx.ConnectError("synthetic delayed connection failure", request=request)
        assert admit_native(
            native,
            dict(request.headers),
            execution_authority,
            "source_data.portfolio_state_snapshot.read",
        ) == (False, "stale_auth_context")
        return httpx.Response(403, json={"detail": "stale_auth_context"})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.clients.http_json_resilience.httpx.AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(receive), **kw),
    )
    query = LotusCoreQueryClient(
        "https://core.invalid",
        1,
        retry_backoff_seconds=0.001,
        execution_authority=execution_authority,
    )
    token = admit_caller_tenant("tenant-a")
    try:
        assert await query.list_instruments(2, "delayed") == (403, {"detail": "stale_auth_context"})
    finally:
        release_caller_identity(token)
    assert len(attempts) == 2
    assert attempts[0]["x-enterprise-auth-signature"] == attempts[1]["x-enterprise-auth-signature"]
