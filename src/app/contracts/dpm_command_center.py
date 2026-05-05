from pydantic import BaseModel, Field


class DpmOutcomeReviewForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0042 outcome-review "
            "authority. Gateway does not calculate expected values, realized values, variance, "
            "tolerance, hashes, lineage, or review state."
        ),
        examples=[
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "rebalance_run_id": "rr_20260415_001",
                "proof_pack_id": "ppack_20260415_001",
                "requested_by": "dpm_sg_1",
            }
        ],
    )


class DpmOutcomeReviewRefreshRequest(BaseModel):
    body: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "Optional refresh controls forwarded unchanged to lotus-manage for RFC-0042 "
            "source refresh. Empty payload asks manage to use its default source-refresh policy."
        ),
        examples=[{"refresh_reason": "late execution fill received", "requested_by": "ops_sg_1"}],
    )


class DpmOutcomeReviewSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns the outcome-review supportability state.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0042",
        description="Business authority and RFC provenance for the returned outcome-review data.",
        examples=["lotus-manage:RFC-0042"],
    )
    state: str = Field(
        description=(
            "Manage-published supportability state. Gateway preserves this value and only "
            "defaults to UNKNOWN when the upstream payload omits explicit supportability."
        ),
        examples=["SUPPORTED", "DEGRADED", "BLOCKED", "UNKNOWN"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published reason codes explaining degraded, blocked, or notable state.",
        examples=[["POST_TRADE_SOURCE_STALE", "EXECUTION_EVIDENCE_PENDING"]],
    )
    blocked_actions: list[str] = Field(
        default_factory=list,
        description="Manage-published action identifiers that callers should disable.",
        examples=[["CREATE_REPORT_INPUT", "REQUEST_AI_NARRATIVE"]],
    )
    remediation_owner: str | None = Field(
        default=None,
        description=(
            "Manage-published remediation owner when source or supportability action is needed."
        ),
        examples=["Portfolio Operations"],
    )


class DpmOutcomeReviewGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc42-outcome-review-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM command-center outcome-review responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmOutcomeReviewSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived from manage-published fields."
        ),
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage outcome-review payload preserved for Workbench composition. "
            "Gateway does not alter manage-owned calculations, hashes, lineage, state, or evidence."
        ),
        examples=[
            {
                "outcome_review_id": "or_20260415_001",
                "state": "READY",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "dimension_results": [
                    {
                        "dimension": "cash_weight",
                        "expected": {"value": "0.0340", "unit": "ratio"},
                        "realized": {"value": "0.0342", "unit": "ratio"},
                        "variance": {"value": "0.0002", "unit": "ratio"},
                        "state": "WITHIN_TOLERANCE",
                    }
                ],
            }
        ],
    )


class DpmOutcomeReviewErrorDetail(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the outcome-review request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.",
        examples=[409],
    )
    error_code: str = Field(
        description="Gateway error classification for the failed manage outcome-review request.",
        examples=["MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the manage error payload.",
        examples=["Outcome review cannot be created until execution evidence is complete."],
    )
