"""Real signed bytes -> registered route -> concrete Core transport, controlled authority."""

import asyncio
import base64
import copy
import json

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.contracts.portfolio_tax_lots import PORTFOLIO_TAX_LOT_RESPONSE_EXAMPLE
from app.main import app
from app.middleware.caller_identity import admitted_tenant_cache_scope
from app.services.portfolio_service import PortfolioService
from app.services.principal_authority.contracts import AuthorityUnavailable, GrantSet
from app.services.principal_authority.resolver import SignedPrincipalGrantResolver

PATH = "/api/v1/portfolio/portfolios/PF_1001/positions/US0378331005/lots"
ISSUER = "https://controlled-identity.test"
NOW = 1800000000


def _segment(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


class ControlledAuthority:
    """In-memory test authority; never deployment identity or a hosted grant store."""

    def __init__(self):
        self.member = True
        self.user = GrantSet(frozenset({"portfolio.read"}), frozenset({"PF_1001"}))
        self.application = self.user
        self.revoked = False
        self.unavailable = None
        self.lookups = []

    def _record(self, operation, *args):
        self.lookups.append((operation, *args))
        if self.unavailable == operation:
            raise AuthorityUnavailable

    async def tenant_members(self, subject, tenant_id):
        self._record("membership", subject, tenant_id)
        await asyncio.sleep(0)
        return self.member

    async def grants_for(self, subject, tenant_id):
        self._record("grants", subject, tenant_id)
        return self.user

    async def application_grants_for(self, actor, tenant_id):
        self._record("application", actor, tenant_id)
        return self.application

    async def is_revoked(self, credential_id, subject):
        self._record("revocation", credential_id, subject)
        return self.revoked


@pytest.fixture
def principal_route(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_TAX_LOT_PRINCIPAL_POSTURE", "verified")
    monkeypatch.setattr(app.state, "is_draining", False, raising=False)
    key = Ed25519PrivateKey.generate()
    foreign = Ed25519PrivateKey.generate()
    authority = ControlledAuthority()
    resolver = SignedPrincipalGrantResolver(
        issuer=ISSUER,
        trusted_keys={"trusted": key.public_key()},
        grants=authority,
        revocations=authority,
        clock=lambda: NOW,
    )
    monkeypatch.setattr(app.state, "principal_grant_resolver", resolver, raising=False)
    calls = []
    source = copy.deepcopy(PORTFOLIO_TAX_LOT_RESPONSE_EXAMPLE)
    source.pop("contract_version")
    source.pop("correlation_id")
    source_status = [200]

    async def respond(request):
        await asyncio.sleep(0)
        calls.append(request)
        return httpx.Response(source_status[0], json=source)

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(**{"transport": httpx.MockTransport(respond), **kwargs}),
    )
    service = PortfolioService(
        LotusCoreQueryClient("https://controlled-core.test", 2, max_retries=0),
        upstream_cache_ttl_seconds=0,
    )
    monkeypatch.setattr("app.routers.portfolio_positions.portfolio_service", lambda: service)

    def mint(overrides=None, *, signer=None, header=None):
        claims = {
            "iss": ISSUER,
            "aud": "lotus-gateway",
            "sub": "advisor-a",
            "tenant": "tenant-a",
            "jti": "controlled-credential",
            "exp": NOW + 120,
            "nbf": NOW - 1,
            "principal_kind": "delegated",
            "act": "workbench",
            **(overrides or {}),
        }
        wire = f"{_segment(header or {'alg': 'EdDSA', 'kid': 'trusted'})}.{_segment(claims)}"
        signature = (signer or key).sign(wire.encode())
        return f"{wire}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"

    return authority, calls, mint, foreign, original, source, source_status


async def _get(harness, credential, *, headers=None, path=PATH):
    original = harness[4]
    request_headers = {} if credential is None else {"Authorization": f"Bearer {credential}"}
    request_headers.update(headers or {})
    async with original(
        transport=httpx.ASGITransport(app), base_url="https://gateway.test"
    ) as client:
        return await client.get(path, headers=request_headers)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "denial,status",
    [
        ("missing_credential", 401),
        ("malformed_credential", 401),
        ("expired_credential", 401),
        ("wrong_audience", 401),
        ("wrong_issuer", 401),
        ("unknown_key_id", 401),
        ("revoked_principal", 401),
        ("present_but_unverified", 401),
        ("tenant_not_a_member", 403),
        ("capability_not_granted", 403),
        ("portfolio_outside_scope", 403),
        ("delegated_capability_not_held_by_user", 403),
        ("grant_store_unavailable", 503),
    ],
)
async def test_all_published_denials_before_protected_core_call(principal_route, denial, status):
    authority, calls, mint, foreign, *_ = principal_route
    credential = mint()
    if denial == "missing_credential":
        credential = None
    elif denial == "malformed_credential":
        credential = "invalid-jws"
    elif denial == "expired_credential":
        credential = mint({"exp": NOW})
    elif denial == "wrong_audience":
        credential = mint({"aud": "lotus-workbench-bff"})
    elif denial == "wrong_issuer":
        credential = mint({"iss": "https://untrusted.test"})
    elif denial == "unknown_key_id":
        credential = mint(header={"alg": "EdDSA", "kid": "unknown"})
    elif denial == "present_but_unverified":
        credential = mint(signer=foreign)
    elif denial == "revoked_principal":
        authority.revoked = True
    elif denial == "tenant_not_a_member":
        authority.member = False
    elif denial == "capability_not_granted":
        authority.application = GrantSet(frozenset(), authority.user.portfolio_scope)
    elif denial == "portfolio_outside_scope":
        authority.application = GrantSet(authority.user.capabilities, frozenset({"OTHER"}))
    elif denial == "delegated_capability_not_held_by_user":
        authority.user = GrantSet(frozenset(), authority.user.portfolio_scope)
    elif denial == "grant_store_unavailable":
        authority.unavailable = "grants"
    response = await _get(
        principal_route,
        credential,
        headers={"X-Tenant-Id": "hostile", "X-Caller-Capabilities": "portfolio.read,admin"},
    )
    assert response.status_code == status
    assert response.json() == {"detail": {"code": denial}}
    assert calls == []
    assert admitted_tenant_cache_scope() == ""


@pytest.mark.asyncio
async def test_foreign_signature_verifies_only_when_foreign_key_is_trusted(
    principal_route, monkeypatch
):
    authority, calls, mint, foreign, *_ = principal_route
    credential = mint(signer=foreign)
    response = await _get(principal_route, credential)
    assert response.status_code == 401
    assert calls == []
    monkeypatch.setattr(
        app.state,
        "principal_grant_resolver",
        SignedPrincipalGrantResolver(
            issuer=ISSUER,
            trusted_keys={"trusted": foreign.public_key()},
            grants=authority,
            revocations=authority,
            clock=lambda: NOW,
        ),
    )
    response = await _get(principal_route, credential)
    assert response.status_code == 200
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_valid_delegation_concurrent_isolation_and_source_fidelity(principal_route):
    authority, calls, mint, _, _, source, _ = principal_route
    results = await asyncio.gather(
        *[
            _get(
                principal_route,
                mint({"sub": f"advisor-{tenant}", "tenant": tenant}),
                headers={
                    "X-Tenant-Id": "hostile-tenant",
                    "X-Actor-Id": "hostile-actor",
                    "X-Region": "HOSTILE",
                    "X-Role": "ADMIN",
                    "X-Caller-Capabilities": "admin",
                    "X-Correlation-Id": f"corr-{tenant}",
                },
            )
            for tenant in ("tenant-a", "tenant-b")
        ]
    )
    assert all(response.status_code == 200 for response in results)
    assert len(calls) == 2
    for response in results:
        assert response.json()["lots"] == source["lots"]
    for request in calls:
        tenant = request.headers["X-Tenant-Id"]
        assert request.headers["X-Correlation-Id"] == f"corr-{tenant}"
        assert "Authorization" not in request.headers
        assert "X-Role" not in request.headers
        assert "X-Actor-Id" not in request.headers
        assert "X-Region" not in request.headers
        assert ("membership", f"advisor-{tenant}", tenant) in authority.lookups
        assert ("application", "workbench", tenant) in authority.lookups
    assert {request.headers["X-Tenant-Id"] for request in calls} == {"tenant-a", "tenant-b"}
    assert admitted_tenant_cache_scope() == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["membership", "grants", "application", "revocation"])
async def test_unavailable_authority_never_falls_back(principal_route, operation):
    principal_route[0].unavailable = operation
    response = await _get(principal_route, principal_route[2]())
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "grant_store_unavailable"}}
    assert principal_route[1] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["user", "service"])
async def test_non_delegated_principal_does_not_require_application_lookup(principal_route, kind):
    authority, calls, mint, *_ = principal_route
    authority.unavailable = "application"
    response = await _get(principal_route, mint({"principal_kind": kind}))
    assert response.status_code == 200
    assert len(calls) == 1
    assert all(lookup[0] != "application" for lookup in authority.lookups)


@pytest.mark.asyncio
@pytest.mark.parametrize("part", ["resolver", "grants", "revocations", "issuer", "keys"])
async def test_absent_deployment_authority_is_unavailable(principal_route, monkeypatch, part):
    resolver = app.state.principal_grant_resolver
    if part == "resolver":
        monkeypatch.delattr(app.state, "principal_grant_resolver")
    else:
        monkeypatch.setattr(resolver, f"_{part}", {} if part == "keys" else None)
    response = await _get(principal_route, principal_route[2]())
    assert response.status_code == 503
    assert principal_route[1] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "posture,environment", [("header-trust", "production"), ("other", "local")]
)
async def test_posture_is_deployment_selected_and_header_trust_local_only(
    principal_route, monkeypatch, posture, environment
):
    monkeypatch.setenv("PORTFOLIO_TAX_LOT_PRINCIPAL_POSTURE", posture)
    monkeypatch.setenv("ENVIRONMENT", environment)
    response = await _get(
        principal_route, principal_route[2](), headers={"X-Principal-Posture": "verified"}
    )
    assert response.status_code == 503
    assert principal_route[1] == []


@pytest.mark.asyncio
async def test_verified_read_preserves_core_error_and_releases_tenant(principal_route):
    principal_route[6][0] = 404
    principal_route[5].clear()
    principal_route[5].update(detail="source lot not found")
    response = await _get(principal_route, principal_route[2]())
    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "lotus-core portfolio tax-lot lookup rejected the request: upstream request failed"
        )
    }
    assert len(principal_route[1]) == 1
    assert admitted_tenant_cache_scope() == ""


def test_pilot_openapi_exposes_credential_and_bounded_denials():
    operation = app.openapi()["paths"][
        PATH.replace("PF_1001", "{portfolio_id}").replace("US0378331005", "{security_id}")
    ]["get"]
    assert operation["security"] == [{"PortfolioPrincipalCredential": []}]
    assert {"401", "403", "503"} <= operation["responses"].keys()
    assert "does not protect other routes" in operation["description"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims,header,code",
    [
        ({"exp": True}, None, "expired_credential"),
        ({"nbf": NOW + 1}, None, "expired_credential"),
        ({"sub": ""}, None, "malformed_credential"),
        ({"tenant": " padded "}, None, "malformed_credential"),
        ({"tenant": "bad\r\ntenant"}, None, "malformed_credential"),
        ({"jti": None}, None, "malformed_credential"),
        ({"act": None}, None, "malformed_credential"),
        ({"principal_kind": "other"}, None, "malformed_credential"),
        ({}, {"alg": "none", "kid": "trusted"}, "malformed_credential"),
        ({}, {"alg": "HS256", "kid": "trusted"}, "malformed_credential"),
        ({}, {"alg": "EdDSA", "kid": ""}, "malformed_credential"),
        ({}, {"alg": "EdDSA", "kid": "trusted", "crit": []}, "malformed_credential"),
    ],
)
async def test_signed_invalid_claims_and_unsupported_headers_fail_closed(
    principal_route, claims, header, code
):
    response = await _get(principal_route, principal_route[2](claims, header=header))
    assert response.status_code == 401
    assert response.json() == {"detail": {"code": code}}
    assert principal_route[1] == []


@pytest.mark.asyncio
async def test_delegated_user_scope_cannot_be_widened_by_application(principal_route):
    authority = principal_route[0]
    authority.user = GrantSet(authority.user.capabilities, frozenset({"OTHER"}))
    response = await _get(principal_route, principal_route[2]())
    assert response.status_code == 403
    assert response.json() == {"detail": {"code": "portfolio_outside_scope"}}
    assert principal_route[1] == []


@pytest.mark.asyncio
async def test_duplicate_authorization_is_refused(principal_route):
    original = principal_route[4]
    async with original(
        transport=httpx.ASGITransport(app), base_url="https://gateway.test"
    ) as client:
        response = await client.get(
            PATH,
            headers=[
                ("Authorization", f"Bearer {principal_route[2]()}"),
                ("Authorization", "Bearer foreign"),
            ],
        )
    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "malformed_credential"}}
    assert principal_route[1] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        "[" * 6000 + "0" + "]" * 6000,
        '{"sub":"first","sub":"second"}',
        "[]",
        "{invalid}",
    ],
)
async def test_untrusted_json_parser_refuses_bounded_malformed_token(principal_route, payload):
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    credential = f"{_segment({'alg': 'EdDSA', 'kid': 'trusted'})}.{encoded}.AA"
    assert len(credential) < 16384
    response = await _get(principal_route, credential)
    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "malformed_credential"}}
    assert principal_route[1] == []
    assert principal_route[0].lookups == []
