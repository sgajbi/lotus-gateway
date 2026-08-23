"""Bounded parsing and observability evidence for Manage PM-quality failures."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_MAX_EVIDENCE_ITEMS = 8
_SAFE_REASON = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,95}$")
_SAFE_FIELD_SEGMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class PmOperatingQualityValidationEvidence:
    """Product-safe, bounded validation metadata extracted from a 4xx payload."""

    reason_codes: tuple[str, ...] = ()
    field_paths: tuple[str, ...] = ()


def extract_pm_operating_quality_validation_evidence(
    upstream_status: int,
    upstream_payload: Mapping[str, Any],
) -> PmOperatingQualityValidationEvidence:
    """Extract reason codes and field paths without retaining messages or request values."""

    if not 400 <= upstream_status < 500:
        return PmOperatingQualityValidationEvidence()

    reason_codes: list[str] = []
    field_paths: list[str] = []
    for node in _detail_nodes(upstream_payload.get("detail")):
        _append_reason_codes(node, reason_codes)
        _append_field_paths(node, field_paths)

    detail = upstream_payload.get("detail")
    if isinstance(detail, str):
        _append_reason(detail, reason_codes)

    return PmOperatingQualityValidationEvidence(
        reason_codes=tuple(reason_codes),
        field_paths=tuple(field_paths),
    )


def _detail_nodes(detail: object) -> tuple[Mapping[str, Any], ...]:
    if isinstance(detail, Mapping):
        nested = [detail]
        for key in ("errors", "issues", "violations", "validation_errors"):
            value = detail.get(key)
            if isinstance(value, Mapping):
                nested.append(value)
            elif isinstance(value, list):
                nested.extend(item for item in value if isinstance(item, Mapping))
        return tuple(nested)
    if isinstance(detail, list):
        return tuple(item for item in detail if isinstance(item, Mapping))
    return ()


def _append_reason_codes(node: Mapping[str, Any], reason_codes: list[str]) -> None:
    for key in ("code", "reason_code", "error_code", "type", "reason"):
        _append_reason(node.get(key), reason_codes)


def _append_reason(value: object, reason_codes: list[str]) -> None:
    if len(reason_codes) >= _MAX_EVIDENCE_ITEMS or not isinstance(value, str):
        return
    normalized = value.strip()
    if _SAFE_REASON.fullmatch(normalized) and normalized not in reason_codes:
        reason_codes.append(normalized)


def _append_field_paths(node: Mapping[str, Any], field_paths: list[str]) -> None:
    for key in ("field", "field_path", "path", "loc"):
        field_path = _safe_field_path(node.get(key))
        if field_path and field_path not in field_paths:
            field_paths.append(field_path)
        if len(field_paths) >= _MAX_EVIDENCE_ITEMS:
            return


def _safe_field_path(value: object) -> str | None:
    if isinstance(value, str):
        parts = value.split(".")
    elif isinstance(value, (list, tuple)):
        if any(not isinstance(item, (int, str)) for item in value):
            return None
        parts = [str(item) for item in value]
    else:
        return None

    if parts and parts[0] in {"body", "query", "path"}:
        parts = parts[1:]
    if not parts or any(not _is_safe_field_segment(part) for part in parts):
        return None
    return ".".join(parts)


def _is_safe_field_segment(value: str) -> bool:
    """Accept named fields and non-negative list indexes, never submitted values."""

    return value.isdigit() or bool(_SAFE_FIELD_SEGMENT.fullmatch(value))
