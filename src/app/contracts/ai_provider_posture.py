"""Closed lotus-ai provider-mode and stub-posture policy."""

from typing import Literal

AiProviderMode = Literal[
    "disabled",
    "stub",
    "openai",
    "local_openai_compatible",
]

_DETERMINISTIC_MODES = frozenset(("disabled", "stub"))
_LIVE_MODES = frozenset(("openai", "local_openai_compatible"))


def is_valid_ai_provider_posture(*, provider_mode: object, stubbed: object) -> bool:
    """Return whether a producer mode and stub flag form a supported posture."""

    if not isinstance(provider_mode, str) or not isinstance(stubbed, bool):
        return False
    if provider_mode in _DETERMINISTIC_MODES:
        return stubbed
    if provider_mode in _LIVE_MODES:
        return not stubbed
    return False


def require_valid_ai_provider_posture(*, provider_mode: object, stubbed: object) -> None:
    """Raise a contract error when provider provenance is missing or contradictory."""

    if not is_valid_ai_provider_posture(provider_mode=provider_mode, stubbed=stubbed):
        raise ValueError("AI provider mode and stub posture are inconsistent.")
