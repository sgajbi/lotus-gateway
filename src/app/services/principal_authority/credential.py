"""App-owned Ed25519 compact-JWS verification, matching Platform refusal order."""

import base64
import binascii
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.services.principal_authority.contracts import PrincipalDenied, PrincipalKind


@dataclass(frozen=True)
class VerifiedCredential:
    subject: str
    tenant_id: str
    principal_kind: PrincipalKind
    delegated_actor: str | None
    credential_id: str


def _decode(segment: str) -> bytes:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", segment):
        raise ValueError("invalid base64url")
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _object(segment: str) -> dict[str, object]:
    value = json.loads(_decode(segment), object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        raise ValueError("object required")
    return value


def _required_string(claims: dict[str, object], name: str) -> str:
    value = claims.get(name)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise PrincipalDenied("malformed_credential", 401)
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise PrincipalDenied("malformed_credential", 401)
    return value


def _signed_claims(
    credential: str, trusted_keys: Mapping[str, Ed25519PublicKey]
) -> dict[str, object]:
    try:
        if len(credential) > 16384:
            raise ValueError("oversized credential")
        header_segment, payload_segment, signature_segment = credential.split(".")
        header, claims = _object(header_segment), _object(payload_segment)
        signature = _decode(signature_segment)
        if header.get("alg") != "EdDSA" or "crit" in header or "b64" in header:
            raise ValueError("unsupported JWS header")
        key_id = _required_string(header, "kid")
    except (ValueError, binascii.Error, UnicodeError, RecursionError):
        raise PrincipalDenied("malformed_credential", 401) from None
    key = trusted_keys.get(key_id)
    if key is None:
        raise PrincipalDenied("unknown_key_id", 401)
    try:
        key.verify(signature, f"{header_segment}.{payload_segment}".encode("ascii"))
    except InvalidSignature:
        raise PrincipalDenied("present_but_unverified", 401) from None
    return claims


def verify_credential(
    credential: str,
    *,
    trusted_keys: Mapping[str, Ed25519PublicKey],
    issuer: str,
    audience: str,
    now: float,
) -> VerifiedCredential:
    if not credential.strip():
        raise PrincipalDenied("missing_credential", 401)
    claims = _signed_claims(credential, trusted_keys)
    if claims.get("iss") != issuer:
        raise PrincipalDenied("wrong_issuer", 401)
    claimed_audience = claims.get("aud")
    audiences = claimed_audience if isinstance(claimed_audience, list) else [claimed_audience]
    if audience not in audiences:
        raise PrincipalDenied("wrong_audience", 401)
    expiry, not_before = claims.get("exp"), claims.get("nbf")
    if (
        not math.isfinite(now)
        or type(expiry) is not int
        or now >= expiry
        or (not_before is not None and (type(not_before) is not int or now < not_before))
    ):
        raise PrincipalDenied("expired_credential", 401)
    subject = _required_string(claims, "sub")
    tenant = _required_string(claims, "tenant")
    credential_id = _required_string(claims, "jti")
    kind = claims.get("principal_kind")
    if kind not in ("user", "service", "delegated"):
        raise PrincipalDenied("malformed_credential", 401)
    actor = _required_string(claims, "act") if kind == "delegated" else None
    return VerifiedCredential(subject, tenant, kind, actor, credential_id)
