from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

POLICY_CONTROL_SERVICE_IDENTITY = "lotus-gateway"
POLICY_CONTROL_TENANT_ID = "tenant_sg_001"
POLICY_CONTROL_LEGAL_ENTITY_CODE = "REFERENCE"
POLICY_STEWARD_ROLE = "POLICY_STEWARD"
POLICY_CHECKER_ROLE = "POLICY_CHECKER"
ADVISOR_ROLE = "ADVISOR"
COMPLIANCE_REVIEWER_ROLE = "COMPLIANCE_REVIEWER"
POLICY_PACK_VALIDATE_CAPABILITY = "advisory.policy_pack.validate"
POLICY_PACK_ACTIVATE_CAPABILITY = "advisory.policy_pack.activate"
POLICY_EVALUATION_FINALIZE_CAPABILITY = "advisory.policy_evaluation.finalize"
POLICY_EVALUATION_REVIEW_EVENT_CAPABILITY = "advisory.policy_evaluation.review_event"
POLICY_EVALUATION_SIGN_OFF_CAPABILITY = "advisory.policy_evaluation.sign_off"
POLICY_EVALUATION_REPORT_PACKAGE_CAPABILITY = "advisory.policy_evaluation.report_package"
POLICY_EVALUATION_AI_EVIDENCE_CAPABILITY = "advisory.policy_evaluation.ai_evidence"

HeaderFactory = Callable[[str, dict[str, str] | None], dict[str, str]]
PolicyEvaluationReader = Callable[[str, str], Awaitable[tuple[int, dict[str, Any]]]]


def build_policy_control_headers(
    headers_factory: HeaderFactory,
    correlation_id: str,
    *,
    actor_id: str,
    role: str,
    capability: str,
    idempotency_key: str | None = None,
    authorized_proposal_id: str | None = None,
    authorized_portfolio_id: str | None = None,
) -> dict[str, str]:
    extras = {
        "X-Actor-Id": actor_id,
        "X-Role": role,
        "X-Tenant-Id": POLICY_CONTROL_TENANT_ID,
        "X-Legal-Entity-Code": POLICY_CONTROL_LEGAL_ENTITY_CODE,
        "X-Service-Identity": POLICY_CONTROL_SERVICE_IDENTITY,
        "X-Capabilities": capability,
    }
    if idempotency_key is not None:
        extras["Idempotency-Key"] = idempotency_key
    if authorized_proposal_id is not None:
        extras["X-Authorized-Proposal-Id"] = authorized_proposal_id
    if authorized_portfolio_id is not None:
        extras["X-Authorized-Portfolio-Id"] = authorized_portfolio_id
    return headers_factory(correlation_id, extras)


async def build_policy_evaluation_control_headers(
    *,
    read_policy_evaluation: PolicyEvaluationReader,
    headers_factory: HeaderFactory,
    evaluation_id: str,
    correlation_id: str,
    actor_id: str,
    role: str,
    capability: str,
    idempotency_key: str | None,
) -> dict[str, str] | tuple[int, dict[str, Any]]:
    status_code, record = await read_policy_evaluation(evaluation_id, correlation_id)
    if status_code >= 400:
        return status_code, record
    return build_policy_control_headers(
        headers_factory,
        correlation_id,
        actor_id=actor_id,
        role=role,
        capability=capability,
        idempotency_key=idempotency_key,
        authorized_proposal_id=record_value(record, "proposal_id"),
        authorized_portfolio_id=record_value(record, "portfolio_id"),
    )


def body_actor(body: dict[str, Any], key: str, *, fallback: str) -> str:
    actor = str(body.get(key) or "").strip()
    return actor or fallback


def evidence_portfolio_id(body: dict[str, Any]) -> str | None:
    evidence_bundle = body.get("evidence_bundle")
    if not isinstance(evidence_bundle, dict):
        return None
    inputs = evidence_bundle.get("inputs")
    if not isinstance(inputs, dict):
        return None
    portfolio_snapshot = inputs.get("portfolio_snapshot")
    if not isinstance(portfolio_snapshot, dict):
        return None
    portfolio_id = str(portfolio_snapshot.get("portfolio_id") or "").strip()
    return portfolio_id or None


def record_value(record: dict[str, Any], key: str) -> str | None:
    value = str(record.get(key) or "").strip()
    return value or None
