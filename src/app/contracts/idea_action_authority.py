"""Shared transport primitives for governed Idea review and conversion authority."""

from datetime import datetime
from typing import Literal

SHA256_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"

IdeaSourceCutPosture = Literal[
    "coherent",
    "coherent_with_declared_tolerance",
    "mixed",
    "partial",
    "unknown",
]
IdeaReviewChannel = Literal["workbench", "operator"]
IdeaPersistedReviewChannel = Literal["workbench", "operator", "legacy_unverified"]
IdeaReviewActionName = Literal[
    "approve_for_conversion",
    "reject",
    "no_action",
    "suppress",
    "snooze",
    "escalate_to_pm",
    "escalate_to_compliance",
]


def require_timezone_aware(alias: str, value: datetime) -> datetime:
    """Reject chronology that cannot be interpreted as one transport instant."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{alias} must include a timezone offset")
    return value


def require_non_blank(alias: str, value: str) -> str:
    """Reject source authority identifiers that contain no usable text."""
    if not value.strip():
        raise ValueError(f"{alias} must not be blank")
    return value
