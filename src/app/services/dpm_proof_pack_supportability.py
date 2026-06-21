from typing import Any

from app.contracts.dpm_proof_packs import DpmProofPackSupportability


def build_dpm_proof_pack_supportability(
    payload: dict[str, Any],
) -> DpmProofPackSupportability:
    proof_pack = _proof_pack_payload(payload)
    reason_codes = _reason_codes_from_payload(payload, proof_pack)
    return DpmProofPackSupportability(
        state=_proof_pack_state(payload, proof_pack),
        proof_pack_id=_safe_str(proof_pack.get("proof_pack_id") or payload.get("proof_pack_id")),
        reason_codes=sorted(set(reason_codes)),
        section_state_counts=_section_state_counts(proof_pack),
        content_hash=_safe_str(proof_pack.get("content_hash") or payload.get("content_hash")),
        markdown_available=bool(payload.get("markdown_url") or payload.get("markdown")),
        report_input_available=bool(
            payload.get("report_input_url")
            or payload.get("report_input")
            or proof_pack.get("report_input_ref")
        ),
        ai_evidence_input_available=bool(
            payload.get("ai_evidence_input_url")
            or payload.get("ai_evidence_input")
            or proof_pack.get("ai_evidence_input_ref")
        ),
    )


def _proof_pack_payload(payload: dict[str, Any]) -> dict[str, Any]:
    proof_pack = payload.get("proof_pack")
    return proof_pack if isinstance(proof_pack, dict) else payload


def _proof_pack_state(payload: dict[str, Any], proof_pack: dict[str, Any]) -> str:
    state = (
        proof_pack.get("status")
        or proof_pack.get("state")
        or payload.get("supportability_status")
        or payload.get("supportabilityStatus")
        or payload.get("status")
        or "UNKNOWN"
    )
    return str(state)


def _reason_codes_from_payload(
    payload: dict[str, Any],
    proof_pack: dict[str, Any],
) -> list[str]:
    reason_codes = _list_of_strings(payload.get("reason_codes") or payload.get("reasonCodes") or [])
    reason_codes.extend(
        _list_of_strings(proof_pack.get("reason_codes") or proof_pack.get("reasonCodes") or [])
    )
    for section in _sections(proof_pack):
        reason_codes.extend(
            _list_of_strings(section.get("reason_codes") or section.get("reasonCodes") or [])
        )
    return reason_codes


def _section_state_counts(proof_pack: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for section in _sections(proof_pack):
        state = section.get("state") or section.get("status")
        if state is None:
            continue
        state_label = str(state)
        counts[state_label] = counts.get(state_label, 0) + 1
    return counts


def _sections(proof_pack: dict[str, Any]) -> list[dict[str, Any]]:
    sections = proof_pack.get("sections")
    if not isinstance(sections, list):
        return []
    return [section for section in sections if isinstance(section, dict)]


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _safe_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
