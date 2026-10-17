"""Opt-in operator-owned execution authority for Core's existing HMAC protocol."""

import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreAuthorityError(ValueError):
    """Bounded local refusal; never include configuration values in diagnostics."""


def _context_value(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 128 or not normalized.isascii():
        raise CoreAuthorityError("invalid_core_execution_context")
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise CoreAuthorityError("invalid_core_execution_context")
    return normalized


@dataclass(frozen=True)
class CoreExecutionAuthority:
    key_id: str
    secret: SecretStr = field(repr=False)
    service_identity: str
    actor_id: str
    role: str
    allowed_tenants: frozenset[str]
    capabilities: frozenset[str]

    def __post_init__(self) -> None:
        for name in ("key_id", "service_identity", "actor_id", "role"):
            object.__setattr__(self, name, _context_value(getattr(self, name)))
        for name in ("allowed_tenants", "capabilities"):
            values = frozenset(_context_value(value) for value in getattr(self, name))
            if not values or any("," in value or "*" in value for value in values):
                raise CoreAuthorityError("invalid_core_execution_scope")
            object.__setattr__(self, name, values)
        secret = self.secret.get_secret_value().strip()
        if not secret:
            raise CoreAuthorityError("missing_core_execution_secret")
        object.__setattr__(self, "secret", SecretStr(secret))

    def sign(self, headers: dict[str, str]) -> dict[str, str]:
        # Collapse casing once, refusing ambiguous input before normalization/signing.
        result = {name.lower(): value.strip() for name, value in headers.items()}
        if len(result) != len(headers):
            raise CoreAuthorityError("ambiguous_core_execution_context")
        tenant = _context_value(result.get("x-tenant-id", ""))
        if tenant not in self.allowed_tenants:
            raise CoreAuthorityError("core_execution_tenant_not_allowed")
        correlation = _context_value(result.get("x-correlation-id", ""))
        # Never sign browser privileges or impersonate its actor. The tenant remains
        # the admitted request fence; service execution identity is operator-owned.
        for name in tuple(result):
            if name.startswith("x-enterprise-auth-") or name in {
                "authorization",
                "x-capabilities",
                "x-caller-capabilities",
                "x-service-identity",
                "x-actor-id",
                "x-role",
            }:
                del result[name]
        result.update(
            {
                "x-enterprise-auth-key-id": self.key_id,
                "x-service-identity": self.service_identity,
                "x-actor-id": self.actor_id,
                "x-role": self.role,
                "x-tenant-id": tenant,
                "x-correlation-id": correlation,
                "x-enterprise-auth-timestamp": str(int(time.time())),
                "x-capabilities": ",".join(sorted(self.capabilities)),
            }
        )
        result["x-enterprise-auth-signature"] = _context_signature(result, self.secret)
        return result


def _context_signature(headers: dict[str, str], secret: SecretStr) -> str:
    canonical = "\n".join(
        (
            "lotus-enterprise-auth-context-v1",
            *(
                headers[name]
                for name in (
                    "x-enterprise-auth-key-id",
                    "x-service-identity",
                    "x-actor-id",
                    "x-tenant-id",
                    "x-role",
                    "x-correlation-id",
                    "x-enterprise-auth-timestamp",
                    "x-capabilities",
                )
            ),
        )
    )
    return hmac.new(
        secret.get_secret_value().encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class _CoreExecutionSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CORE_EXECUTION_",
        env_file=None,
        hide_input_in_errors=True,
    )
    key_id: str = ""
    secret: SecretStr = SecretStr("")
    service_identity: str = ""
    actor_id: str = ""
    role: str = ""
    allowed_tenants: frozenset[str] = frozenset()
    capabilities: frozenset[str] = frozenset()


def load_core_execution_authority() -> CoreExecutionAuthority | None:
    """Load explicitly enabled server configuration; absence keeps legacy transport."""
    enabled = os.getenv("CORE_EXECUTION_ENABLED", "false").strip().lower()
    if enabled in {"false", "0"}:
        return None
    if enabled not in {"true", "1"}:
        raise CoreAuthorityError("invalid_core_execution_enablement")
    try:
        configured = _CoreExecutionSettings()
        return CoreExecutionAuthority(
            **{name: getattr(configured, name) for name in _CoreExecutionSettings.model_fields}
        )
    except (ValueError, TypeError):
        raise CoreAuthorityError("invalid_core_execution_configuration") from None
