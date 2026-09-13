from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AdvisoryPolicyBodyRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque advisory policy payload forwarded unchanged to lotus-advise. Gateway "
            "does not evaluate policy rules, infer supportability, approve sign-off, or create "
            "client-ready publication posture locally."
        ),
        examples=[
            {
                "requested_by": "advisor_1",
                "source_evaluation_hash": "sha256:policy-evaluation-001",
                "reason": {"purpose": "advisor and compliance review"},
            }
        ],
    )


class AdvisoryPolicyEvaluationPortfolioSnapshot(BaseModel):
    """The portfolio identifier whose authority must be admitted for finalization."""

    model_config = ConfigDict(extra="allow")

    portfolio_id: str = Field(
        min_length=1,
        pattern=r"\S",
        description="Portfolio identifier selected as evidence for this policy evaluation.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )


class AdvisoryPolicyEvaluationInputs(BaseModel):
    """The minimum typed evidence inputs needed at Gateway's authorization boundary."""

    model_config = ConfigDict(extra="allow")

    portfolio_snapshot: AdvisoryPolicyEvaluationPortfolioSnapshot = Field(
        description="Portfolio snapshot whose identifier is matched to admitted portfolio scope."
    )


class AdvisoryPolicyEvaluationEvidenceBundle(BaseModel):
    """Evaluation evidence while preserving Advise-owned extensions unchanged."""

    model_config = ConfigDict(extra="allow")

    inputs: AdvisoryPolicyEvaluationInputs = Field(
        description="Evidence inputs containing the portfolio snapshot used for finalization."
    )


class AdvisoryPolicyEvaluationFinalizeBody(BaseModel):
    """Opaque Advise payload with the resource identifier Gateway must authorize."""

    model_config = ConfigDict(extra="allow")

    evidence_bundle: AdvisoryPolicyEvaluationEvidenceBundle = Field(
        description="Evidence bundle whose portfolio identifier is checked before outbound I/O."
    )


class AdvisoryPolicyEvaluationFinalizeRequest(BaseModel):
    """Create-evaluation payload with its authorization-relevant evidence made explicit."""

    body: AdvisoryPolicyEvaluationFinalizeBody = Field(
        description=(
            "Advisory-policy finalization payload forwarded to lotus-advise after Gateway verifies "
            "the path proposal and evidence portfolio against caller-admitted resource scope."
        ),
        examples=[
            {
                "evidence_bundle": {
                    "inputs": {"portfolio_snapshot": {"portfolio_id": "PB_SG_GLOBAL_BAL_001"}}
                }
            }
        ],
    )


class AdvisoryPolicyErrorResponse(BaseModel):
    """A refusal raised by Gateway itself, before any lotus-advise request is made.

    Distinct from the upstream error envelope: this one reports that the caller's
    admitted scope does not cover the operation, so no upstream call happened and
    there is no upstream content to convey.
    """

    code: str = Field(
        description="Stable product-safe advisory-policy caller-context error code.",
        examples=["advisory_policy_access_denied"],
    )
    message: str = Field(
        description=(
            "Product-safe explanation. Deliberately uniform across missing roles and missing "
            "capabilities so the response cannot be used to enumerate either."
        ),
        examples=["Advisory-policy access is not available for this caller."],
    )
    correlation_id: str = Field(
        description="Opaque request correlation identifier for support follow-up.",
        examples=["corr-advisory-policy-1"],
    )


class AdvisoryPolicyEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-advisory-policy-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for advisory policy envelopes.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Advisory policy payload returned by lotus-advise. Gateway preserves policy-pack, "
            "policy-evaluation, workflow, sign-off, report-package, AI-evidence, lineage, "
            "replay, degraded, and blocked posture without recomputing or promoting policy facts."
        ),
    )
